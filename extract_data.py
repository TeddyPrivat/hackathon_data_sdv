"""
extract_data.py
---------------
Downloads and loads climate data sources into pandas DataFrames.
Files are cached in a local `data/` directory to avoid re-downloading.

Usage:
    python extract_data.py
"""

import os
import io
import json
import zipfile
import gzip
import shutil
from pathlib import Path

import pandas as pd
import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Shared request headers to avoid 403 on some servers
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; ClimateDataLoader/1.0; "
        "+https://github.com/climate-data)"
    )
}

REQUEST_TIMEOUT = 120  # seconds


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _download(url: str, dest: Path, chunk_size: int = 1 << 20) -> Path:
    """Download *url* to *dest*, streaming in chunks. Skips if already cached."""
    if dest.exists() and dest.stat().st_size > 0:
        print(f"  [cache] {dest.name}")
        return dest
    print(f"  [download] {url}")
    with requests.get(url, headers=HEADERS, stream=True, timeout=REQUEST_TIMEOUT) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=chunk_size):
                f.write(chunk)
    print(f"  [saved] {dest.name} ({dest.stat().st_size / 1024:.1f} KB)")
    return dest


def _read_csv_with_fallback(
    path_or_buffer,
    sep: str = ",",
    comment: str = None,
    **kwargs,
) -> pd.DataFrame:
    """Try reading CSV with utf-8, then latin-1 on UnicodeDecodeError."""
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            return pd.read_csv(
                path_or_buffer,
                sep=sep,
                comment=comment,
                encoding=enc,
                low_memory=False,
                **kwargs,
            )
        except UnicodeDecodeError:
            if hasattr(path_or_buffer, "seek"):
                path_or_buffer.seek(0)
            continue
    raise ValueError(f"Could not decode {path_or_buffer} with utf-8 / latin-1 / cp1252")


def _status(name: str, df: pd.DataFrame) -> None:
    print(f"[OK] Loaded {name}: {df.shape[0]} rows x {df.shape[1]} cols")


# ---------------------------------------------------------------------------
# 1. Météo-France — Stations metadata
# ---------------------------------------------------------------------------

def load_meteofrance_stations() -> pd.DataFrame:
    """Météo-France station metadata (CSV)."""
    url = (
        "https://static.data.gouv.fr/resources/stations-meteo-france/"
        "20250104-124154/stations-meteo-france.csv"
    )
    dest = DATA_DIR / "stations-meteo-france.csv"
    try:
        _download(url, dest)
        df = _read_csv_with_fallback(dest, sep=",")
        _status("Météo-France Stations", df)
        return df
    except Exception as e:
        print(f"[ERROR] load_meteofrance_stations: {e}")
        return pd.DataFrame()


# ---------------------------------------------------------------------------
# 2–4. Météo-France — LSH homogenised long series (Tmax, Tmin, Précipitations)
# ---------------------------------------------------------------------------

def _load_lsh_zip(url: str, label: str) -> pd.DataFrame:
    """
    Generic loader for Météo-France LSH ZIP archives.

    Each ZIP contains multiple CSV files (one per station).  All CSVs are
    concatenated into a single DataFrame.  The individual CSV files use a
    semicolon separator and start with comment/metadata lines; the first
    non-comment line is the header.
    """
    filename = url.split("/")[-1]
    dest = DATA_DIR / filename
    extract_dir = DATA_DIR / filename.replace(".zip", "")

    try:
        _download(url, dest)

        if not extract_dir.exists():
            print(f"  [extract] {filename}")
            with zipfile.ZipFile(dest, "r") as zf:
                zf.extractall(extract_dir)

        csv_files = list(extract_dir.rglob("*.csv"))
        if not csv_files:
            # Some ZIPs nest an extra directory level
            csv_files = list(extract_dir.rglob("*.CSV"))
        if not csv_files:
            raise FileNotFoundError(f"No CSV files found inside {extract_dir}")

        print(f"  [info] {len(csv_files)} CSV files found in archive")

        frames = []
        for csv_path in csv_files:
            try:
                # LSH files: semicolon-separated, may have comment lines starting with #
                df_part = _read_csv_with_fallback(csv_path, sep=";", comment="#")
                # Attach source filename as a station identifier when not already present
                if "fichier" not in df_part.columns:
                    df_part["_source_file"] = csv_path.stem
                frames.append(df_part)
            except Exception as e_inner:
                print(f"  [warn] Could not read {csv_path.name}: {e_inner}")

        if not frames:
            raise ValueError("No data frames could be loaded from the ZIP")

        df = pd.concat(frames, ignore_index=True)
        _status(label, df)
        return df

    except Exception as e:
        print(f"[ERROR] {label}: {e}")
        return pd.DataFrame()


def load_lsh_tmax() -> pd.DataFrame:
    """Météo-France LSH Tmax (homogenized long series)."""
    return _load_lsh_zip(
        "https://object.files.data.gouv.fr/meteofrance/data/synchro_ftp/REF_CC/LSH/SH_TX_metropole.zip",
        "Météo-France LSH Tmax",
    )


def load_lsh_tmin() -> pd.DataFrame:
    """Météo-France LSH Tmin (homogenized long series)."""
    return _load_lsh_zip(
        "https://object.files.data.gouv.fr/meteofrance/data/synchro_ftp/REF_CC/LSH/SH_TN_metropole.zip",
        "Météo-France LSH Tmin",
    )


def load_lsh_precip() -> pd.DataFrame:
    """Météo-France LSH Précipitations (homogenized long series)."""
    return _load_lsh_zip(
        "https://object.files.data.gouv.fr/meteofrance/data/synchro_ftp/REF_CC/LSH/SH_RR_metropole.zip",
        "Météo-France LSH Précipitations",
    )


# ---------------------------------------------------------------------------
# 5. Météo-France — Observations quotidiennes Paris (dept 75)
# ---------------------------------------------------------------------------

def load_obs_quot_paris() -> pd.DataFrame:
    """
    Météo-France daily observations for Paris (dept 75).
    Tries the historical file first (1950-2024), then the recent one (2025-2026).
    """
    urls = [
        (
            "https://object.files.data.gouv.fr/meteofrance/data/synchro_ftp/"
            "BASE/QUOT/Q_75_previous-1950-2024_RR-T-Vent.csv.gz",
            "Q_75_previous-1950-2024_RR-T-Vent.csv.gz",
        ),
        (
            "https://object.files.data.gouv.fr/meteofrance/data/synchro_ftp/"
            "BASE/QUOT/Q_75_latest-2025-2026_RR-T-Vent.csv.gz",
            "Q_75_latest-2025-2026_RR-T-Vent.csv.gz",
        ),
    ]

    frames = []
    for url, fname in urls:
        dest = DATA_DIR / fname
        try:
            _download(url, dest)
            with gzip.open(dest, "rb") as gz:
                raw = gz.read()
            for enc in ("utf-8", "latin-1"):
                try:
                    df_part = pd.read_csv(
                        io.BytesIO(raw),
                        sep=";",
                        encoding=enc,
                        low_memory=False,
                    )
                    frames.append(df_part)
                    print(f"  [info] {fname}: {len(df_part)} rows")
                    break
                except UnicodeDecodeError:
                    continue
        except Exception as e:
            print(f"  [warn] Could not load {fname}: {e}")

    if not frames:
        print("[ERROR] load_obs_quot_paris: no data loaded")
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True)
    _status("Météo-France Obs. Quot. Paris", df)
    return df


# ---------------------------------------------------------------------------
# 6–9. NOAA greenhouse gas monthly means
# ---------------------------------------------------------------------------

def _load_noaa_csv(url: str, label: str) -> pd.DataFrame:
    """
    Generic loader for NOAA GML monthly CSV files.
    All lines starting with '#' are treated as comments.
    """
    filename = url.split("/")[-1]
    dest = DATA_DIR / filename
    try:
        _download(url, dest)
        df = pd.read_csv(dest, comment="#", encoding="utf-8")
        # Strip any stray whitespace from column names
        df.columns = [c.strip() for c in df.columns]
        _status(label, df)
        return df
    except Exception as e:
        print(f"[ERROR] {label}: {e}")
        return pd.DataFrame()


def load_noaa_co2_mlo() -> pd.DataFrame:
    """NOAA CO2 monthly means — Mauna Loa."""
    return _load_noaa_csv(
        "https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_mm_mlo.csv",
        "NOAA CO2 Mauna Loa",
    )


def load_noaa_co2_global() -> pd.DataFrame:
    """NOAA CO2 global monthly means."""
    return _load_noaa_csv(
        "https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_mm_gl.csv",
        "NOAA CO2 Global",
    )


def load_noaa_ch4_global() -> pd.DataFrame:
    """NOAA CH4 global monthly means."""
    return _load_noaa_csv(
        "https://gml.noaa.gov/webdata/ccgg/trends/ch4/ch4_mm_gl.csv",
        "NOAA CH4 Global",
    )


def load_noaa_n2o_global() -> pd.DataFrame:
    """NOAA N2O global monthly means."""
    return _load_noaa_csv(
        "https://gml.noaa.gov/webdata/ccgg/trends/n2o/n2o_mm_gl.csv",
        "NOAA N2O Global",
    )


# ---------------------------------------------------------------------------
# 10–11. ADEME — Projections climatiques +2°C and +4°C
# ---------------------------------------------------------------------------

def _load_ademe_projections(url: str, label: str, cache_name: str) -> pd.DataFrame:
    """
    ADEME climate projections CSV (semicolon-separated, comma decimal separator).
    The raw endpoint streams CSV directly; we cache it locally.
    """
    dest = DATA_DIR / cache_name
    try:
        _download(url, dest)
        df = _read_csv_with_fallback(dest, sep=";", decimal=",")
        _status(label, df)
        return df
    except Exception as e:
        print(f"[ERROR] {label}: {e}")
        return pd.DataFrame()


def load_ademe_2c() -> pd.DataFrame:
    """ADEME projections climatiques +2°C."""
    return _load_ademe_projections(
        "https://data.ademe.fr/data-fair/api/v1/datasets/"
        "donnees-climatiques-prospectives-france-2c/raw",
        "ADEME Projections +2°C",
        "ademe_projections_2c.csv",
    )


def load_ademe_4c() -> pd.DataFrame:
    """ADEME projections climatiques +4°C."""
    return _load_ademe_projections(
        "https://data.ademe.fr/data-fair/api/v1/datasets/"
        "donnees-climatiques-prospectives-france-4c/raw",
        "ADEME Projections +4°C",
        "ademe_projections_4c.csv",
    )


# ---------------------------------------------------------------------------
# 12. SDES — GES format NAMEA
# ---------------------------------------------------------------------------

def load_sdes_ges_namea() -> pd.DataFrame:
    """
    SDES greenhouse gas emissions (NAMEA format), semicolon-separated CSV.
    The data.gouv.fr URL redirects to the actual file — requests follows it.
    """
    url = "https://www.data.gouv.fr/api/1/datasets/r/3e33c154-b738-488a-bdd9-18b7deaef182"
    dest = DATA_DIR / "sdes_ges_namea.csv"
    try:
        _download(url, dest)
        df = _read_csv_with_fallback(dest, sep=";")
        _status("SDES GES NAMEA", df)
        return df
    except Exception as e:
        print(f"[ERROR] load_sdes_ges_namea: {e}")
        return pd.DataFrame()


# ---------------------------------------------------------------------------
# 13. VigiEau — Arrêtés sécheresse 2024
# ---------------------------------------------------------------------------

def load_vigieau_arretes() -> pd.DataFrame:
    """VigiEau drought restriction orders 2024 (CSV)."""
    url = (
        "https://static.data.gouv.fr/resources/donnee-secheresse-vigieau/"
        "20260316-060938/arretes-2024.csv"
    )
    dest = DATA_DIR / "vigieau_arretes_2024.csv"
    try:
        _download(url, dest)
        df = _read_csv_with_fallback(dest, sep=",")
        _status("VigiEau Arrêtés 2024", df)
        return df
    except Exception as e:
        print(f"[ERROR] load_vigieau_arretes: {e}")
        return pd.DataFrame()


# ---------------------------------------------------------------------------
# 14. VigiEau — Zones en vigueur (GeoJSON)
# ---------------------------------------------------------------------------

def load_vigieau_zones() -> pd.DataFrame:
    """
    VigiEau current alert zones (GeoJSON).
    Uses geopandas if available, otherwise falls back to pandas + json.
    """
    url = (
        "https://regleau.s3.gra.perf.cloud.ovh.net/geojson/"
        "zones_arretes_en_vigueur.geojson"
    )
    dest = DATA_DIR / "vigieau_zones_en_vigueur.geojson"
    try:
        _download(url, dest)

        # Try geopandas first
        try:
            import geopandas as gpd
            df = gpd.read_file(dest)
            _status("VigiEau Zones (geopandas)", df)
            return df
        except ImportError:
            pass

        # Fallback: flatten GeoJSON features into a regular DataFrame
        with open(dest, "r", encoding="utf-8") as f:
            geojson = json.load(f)

        features = geojson.get("features", [])
        rows = []
        for feat in features:
            row = feat.get("properties", {}).copy()
            # Store geometry type for reference
            geom = feat.get("geometry") or {}
            row["_geometry_type"] = geom.get("type")
            rows.append(row)

        df = pd.DataFrame(rows)
        _status("VigiEau Zones (pandas/json)", df)
        return df

    except Exception as e:
        print(f"[ERROR] load_vigieau_zones: {e}")
        return pd.DataFrame()


# ---------------------------------------------------------------------------
# 15. Explore2/TRACC — Projections débits (VCN10 par région, ~32 MB)
# ---------------------------------------------------------------------------

def load_explore2_debits() -> pd.DataFrame:
    """
    Explore2/TRACC future streamflow projections — VCN10 low-flow indicator
    aggregated at regional level (~32 MB CSV).
    """
    url = "https://www.data.gouv.fr/api/1/datasets/r/cc468fd0-2a1e-46ba-bddc-651c220df291"
    dest = DATA_DIR / "explore2_vcn10_region.csv"
    try:
        _download(url, dest)
        df = _read_csv_with_fallback(dest, sep=";")
        _status("Explore2/TRACC VCN10 Région", df)
        return df
    except Exception as e:
        print(f"[ERROR] load_explore2_debits: {e}")
        return pd.DataFrame()


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

DATASETS = [
    ("Météo-France Stations",         load_meteofrance_stations),
    ("Météo-France LSH Tmax",         load_lsh_tmax),
    ("Météo-France LSH Tmin",         load_lsh_tmin),
    ("Météo-France LSH Précipitations", load_lsh_precip),
    ("Météo-France Obs. Quot. Paris", load_obs_quot_paris),
    ("NOAA CO2 Mauna Loa",            load_noaa_co2_mlo),
    ("NOAA CO2 Global",               load_noaa_co2_global),
    ("NOAA CH4 Global",               load_noaa_ch4_global),
    ("NOAA N2O Global",               load_noaa_n2o_global),
    ("ADEME Projections +2°C",        load_ademe_2c),
    ("ADEME Projections +4°C",        load_ademe_4c),
    ("SDES GES NAMEA",                load_sdes_ges_namea),
    ("VigiEau Arrêtés 2024",          load_vigieau_arretes),
    ("VigiEau Zones GeoJSON",         load_vigieau_zones),
    ("Explore2/TRACC Débits VCN10",   load_explore2_debits),
]

SEPARATOR = "=" * 72


def main() -> None:
    print(SEPARATOR)
    print("  Climate Data Loader")
    print(f"  Cache directory: {DATA_DIR.resolve()}")
    print(SEPARATOR)

    results: dict[str, pd.DataFrame] = {}

    for name, loader in DATASETS:
        print(f"\n{'-' * 60}")
        print(f">>> {name}")
        print(f"{'-' * 60}")
        df = loader()
        results[name] = df

        if df.empty:
            print(f"  [SKIP] DataFrame is empty — no preview available.")
            continue

        print(f"\n  Shape: {df.shape}")
        print("\n  --- head(3) ---")
        with pd.option_context(
            "display.max_columns", 10,
            "display.width", 120,
            "display.max_colwidth", 30,
        ):
            print(df.head(3).to_string(index=False))

        print("\n  --- info() ---")
        buf = io.StringIO()
        df.info(buf=buf, verbose=False, show_counts=False)
        print(buf.getvalue())

    # Summary table
    print(f"\n{SEPARATOR}")
    print("  SUMMARY")
    print(SEPARATOR)
    print(f"  {'Dataset':<42} {'Rows':>8} {'Cols':>6}")
    print(f"  {'-'*42} {'-'*8} {'-'*6}")
    for name, df in results.items():
        if df.empty:
            print(f"  {name:<42} {'FAILED':>8} {'':>6}")
        else:
            print(f"  {name:<42} {df.shape[0]:>8,} {df.shape[1]:>6}")
    print(SEPARATOR)


if __name__ == "__main__":
    main()
