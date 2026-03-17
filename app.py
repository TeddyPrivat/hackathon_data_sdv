import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from pathlib import Path
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error
import requests

st.set_page_config(
    page_title="Climat France 2100",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Design System ─────────────────────────────────────────────────────────────
BG       = "#07090f"
BG_CARD  = "#0d1117"
BG_CARD2 = "#111827"
BORDER   = "rgba(255,255,255,0.07)"
TEXT     = "#f0f4f8"
TEXT_SUB = "#6b7f99"
TEXT_DIM = "#3d4f63"
BLUE     = "#3b82f6"
AMBER    = "#f59e0b"
RED      = "#ef4444"
GREEN    = "#10b981"

PLOT_LAYOUT = dict(
    plot_bgcolor=BG_CARD,
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color=TEXT_SUB, family="Inter, system-ui, sans-serif", size=11),
    xaxis=dict(gridcolor="rgba(255,255,255,0.04)", linecolor="rgba(255,255,255,0.08)",
               tickcolor=TEXT_DIM, title_font=dict(color=TEXT_SUB)),
    yaxis=dict(gridcolor="rgba(255,255,255,0.04)", linecolor="rgba(255,255,255,0.08)",
               tickcolor=TEXT_DIM, title_font=dict(color=TEXT_SUB)),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT_SUB)),
    margin=dict(t=30, b=40, l=50, r=20),
)

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

* {{ font-family: 'Inter', system-ui, sans-serif !important; }}

/* ── App background ── */
html, body, [data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > .main {{
    background: {BG} !important;
}}
[data-testid="block-container"] {{
    padding: 2rem 2.5rem 3rem !important;
    max-width: 1400px;
}}

/* ── Sidebar ── */
[data-testid="stSidebar"] {{
    background: #060810 !important;
    border-right: 1px solid {BORDER} !important;
}}
[data-testid="stSidebar"] * {{ color: {TEXT_SUB} !important; }}
[data-testid="stSidebar"] .stRadio label span {{ color: {TEXT} !important; }}
[data-testid="stSidebar"] hr {{ border-color: {BORDER} !important; }}

/* ── All text ── */
h1, h2, h3, h4, p, span, div, label {{
    color: {TEXT} !important;
}}
h1 {{ font-size: 1.65rem !important; font-weight: 700 !important;
     letter-spacing: -0.02em !important; }}
h2 {{ font-size: 1.1rem !important; font-weight: 600 !important;
     color: {TEXT_SUB} !important; text-transform: uppercase !important;
     letter-spacing: 0.08em !important; font-size: 0.78rem !important;
     margin-top: 2rem !important; margin-bottom: 1rem !important; }}
h3 {{ font-size: 1rem !important; font-weight: 600 !important; }}

/* ── Widgets ── */
[data-testid="stSelectbox"] > div,
[data-testid="stMultiSelect"] > div {{
    background: {BG_CARD} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 8px !important;
}}
[data-testid="stSlider"] [data-baseweb="slider"] {{
    background: {BG_CARD} !important;
}}
[data-testid="stRadio"] label {{ color: {TEXT_SUB} !important; }}
[data-baseweb="select"] {{ background: {BG_CARD} !important; }}
[data-baseweb="select"] * {{ color: {TEXT} !important; background: {BG_CARD} !important; }}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {{ background: {BG_CARD} !important; border-radius: 10px; }}
.dvn-scroller {{ background: {BG_CARD} !important; }}

/* ── Custom components ── */
.page-header {{
    border-bottom: 1px solid {BORDER};
    padding-bottom: 1.2rem;
    margin-bottom: 0.5rem;
}}
.page-title {{
    font-size: 1.65rem;
    font-weight: 700;
    color: {TEXT} !important;
    letter-spacing: -0.02em;
    margin: 0;
}}
.page-sub {{
    font-size: 0.87rem;
    color: {TEXT_SUB} !important;
    margin-top: 0.4rem;
    line-height: 1.6;
}}
.kpi-card {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 1.3rem 1.4rem;
    position: relative;
    overflow: hidden;
}}
.kpi-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: var(--accent, {BLUE});
}}
.kpi-label {{
    font-size: 0.72rem;
    font-weight: 500;
    color: {TEXT_SUB} !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.5rem;
}}
.kpi-value {{
    font-size: 2rem;
    font-weight: 700;
    color: {TEXT} !important;
    letter-spacing: -0.03em;
    line-height: 1;
}}
.kpi-sub {{
    font-size: 0.78rem;
    color: {TEXT_DIM} !important;
    margin-top: 0.4rem;
}}
.section-label {{
    font-size: 0.72rem;
    font-weight: 600;
    color: {TEXT_DIM} !important;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.8rem;
    margin-top: 2rem;
}}
.reco-card {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 1.4rem 1.5rem;
    margin-bottom: 0.8rem;
    border-left: 3px solid var(--accent-reco);
}}
.reco-title {{
    font-size: 0.9rem;
    font-weight: 600;
    color: {TEXT} !important;
    margin-bottom: 0.8rem;
}}
.reco-item {{
    font-size: 0.83rem;
    color: {TEXT_SUB} !important;
    padding: 0.25rem 0;
    padding-left: 0.8rem;
    border-left: 1px solid {BORDER};
    margin-left: 0.2rem;
    margin-bottom: 0.2rem;
}}
.source-tag {{
    display: inline-block;
    margin-top: 0.8rem;
    font-size: 0.7rem;
    color: {TEXT_DIM} !important;
    background: rgba(255,255,255,0.04);
    padding: 0.2rem 0.6rem;
    border-radius: 4px;
}}
.scenario-pill {{
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-right: 0.4rem;
}}
.divider {{
    border: none;
    border-top: 1px solid {BORDER};
    margin: 1.5rem 0;
}}
</style>
""", unsafe_allow_html=True)

DATA = Path("data")

SCENARIO_COLORS = {
    "Optimiste (+1.4°C)":      BLUE,
    "Intermédiaire (+2.7°C)":  AMBER,
    "Pessimiste (+4.4°C)":     RED,
}
SCENARIO_CO2 = {
    "Optimiste (+1.4°C)":      {2024:422, 2030:430, 2040:438, 2050:428, 2075:400, 2100:390},
    "Intermédiaire (+2.7°C)":  {2024:422, 2030:435, 2040:455, 2050:480, 2075:530, 2100:550},
    "Pessimiste (+4.4°C)":     {2024:422, 2030:445, 2040:490, 2050:550, 2075:750, 2100:1100},
}

# ── Data loaders ──────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_temperatures():
    def _load(path):
        df = pd.read_csv(path, low_memory=False)
        df = df[df["Q_HOM"] == 1].copy()
        df["year"]  = df["YYYYMM"] // 100
        df["month"] = df["YYYYMM"] % 100
        return df
    tx = _load(DATA / "temperatures/SH_TX_metropole_concat.csv")
    tn = _load(DATA / "temperatures/SH_TN_metropole_concat.csv")
    monthly = pd.concat([
        tx.groupby(["year","month"])["VALEUR"].mean().rename("tx"),
        tn.groupby(["year","month"])["VALEUR"].mean().rename("tn"),
    ], axis=1).dropna().reset_index()
    monthly["tmoy"] = (monthly["tx"] + monthly["tn"]) / 2
    annual = monthly.groupby("year")[["tx","tn","tmoy"]].mean().reset_index()
    ref = annual[(annual.year>=1961)&(annual.year<=1990)]["tmoy"].mean()
    annual["anomalie"] = annual["tmoy"] - ref
    return annual, ref

@st.cache_data(show_spinner=False)
def load_co2():
    df = pd.read_csv(DATA / "emissions_gaz/co2_mm_mlo.csv", comment="#")
    df.columns = [c.strip() for c in df.columns]
    return df[df["average"]>0].groupby("year")["average"].mean().reset_index().rename(columns={"average":"co2_ppm"})

@st.cache_data(show_spinner=False)
def load_fires():
    return pd.read_csv(DATA / "feux/incendies_2003_2024.csv", low_memory=False)

@st.cache_data(show_spinner=False)
def load_emissions():
    return pd.read_csv(DATA / "emissions_gaz/emissions_france_1995_2024.csv")

@st.cache_data(show_spinner=False)
def load_empreinte():
    return pd.read_csv(DATA / "emissions_gaz/empreinte_carbone_france_par_habitant_1990_2024.csv")

@st.cache_data(show_spinner=False)
def load_ges_secteur():
    df = pd.read_csv(DATA / "emissions_gaz/sdes_ges_namea.csv", sep=";")
    df.columns = [c.strip() for c in df.columns]
    return df

@st.cache_data(show_spinner=False)
def load_precipitation():
    df = pd.read_csv(DATA / "precipitations/SH_RR_metropole_concat.csv", low_memory=False)
    df = df[df["Q_HOM"]==1].copy()
    df["year"] = df["YYYYMM"] // 100
    annual = df.groupby("year")["VALEUR"].mean().reset_index().rename(columns={"VALEUR":"precip_mm"})
    ref = annual[(annual.year>=1961)&(annual.year<=1990)]["precip_mm"].mean()
    annual["anomalie"] = annual["precip_mm"] - ref
    return annual, ref

@st.cache_data(show_spinner=False)
def load_hot_days_by_dept():
    """Jours TX >= 30°C par département et par an (94 depts, 1950–2024)."""
    df = pd.read_csv(DATA / "temperatures/hot_days_by_dept.csv")
    df["dept"] = df["dept"].astype(str).str.zfill(2)
    return df

@st.cache_data(show_spinner=False)
def load_hot_days():
    """Moyenne nationale des jours TX >= 30°C par an, 1950–2024."""
    df = load_hot_days_by_dept()
    national = df.groupby("year")["jours_30"].mean().reset_index()
    ref = national[(national.year >= 1961) & (national.year <= 1990)]["jours_30"].mean()
    national["anomalie"] = national["jours_30"] - ref
    return national, ref

@st.cache_data(show_spinner=False)
def load_precip_by_dept():
    df = pd.read_csv(DATA / "precipitations/SH_RR_metropole_concat.csv", low_memory=False)
    df = df[df["Q_HOM"] == 1].copy()
    df["year"] = df["YYYYMM"] // 100
    df["dept"] = df["num_poste"].astype(str).str.zfill(8).str[:2]
    annual = (df.groupby(["dept", "year"])["VALEUR"]
                .mean().reset_index()
                .rename(columns={"VALEUR": "precip_mm"}))
    ref = (annual[(annual.year >= 1961) & (annual.year <= 1990)]
           .groupby("dept")["precip_mm"].mean().rename("ref_p"))
    annual = annual.merge(ref, on="dept")
    annual["anomalie"] = annual["precip_mm"] - annual["ref_p"]
    return annual

@st.cache_data(show_spinner=False)
def get_dept_geojson():
    url = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements-version-simplifiee.geojson"
    try:
        return requests.get(url, timeout=8).json()
    except Exception:
        return None

@st.cache_data(show_spinner=False)
def build_model():
    annual, ref = load_temperatures()
    co2 = load_co2()
    df = annual.merge(co2, on="year").dropna()
    df["log_co2"] = np.log(df["co2_ppm"] / 280)

    X = df[["log_co2"]].values
    y = df["anomalie"].values
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, shuffle=False
    )

    def make_models():
        return {
            "Régression linéaire": LinearRegression(),
            "Polynomiale (deg. 2)": Pipeline([
                ("poly", PolynomialFeatures(2, include_bias=False)),
                ("lr", LinearRegression()),
            ]),
            "Random Forest": RandomForestRegressor(100, random_state=42),
            "Gradient Boosting": GradientBoostingRegressor(100, random_state=42),
        }

    metrics = {}
    for name, m in make_models().items():
        m.fit(X_train, y_train)
        pred = m.predict(X_test)
        rmse = float(np.sqrt(mean_squared_error(y_test, pred)))
        mae  = float(mean_absolute_error(y_test, pred))
        mask = y_test != 0
        mape = float(np.mean(np.abs((y_test[mask] - pred[mask]) / y_test[mask])) * 100)
        metrics[name] = {
            "RMSE": round(rmse, 4),
            "MAE":  round(mae,  4),
            "MAPE (%)": round(mape, 1),
        }

    best_name = min(metrics, key=lambda k: metrics[k]["RMSE"])
    best_model = make_models()[best_name]
    best_model.fit(X, y)
    return best_model, ref, metrics, best_name

def project_scenario(model, ref, target_year=2100):
    results = {}
    years = np.arange(2024, target_year + 1)
    for name, anchors in SCENARIO_CO2.items():
        pts = sorted(anchors.items())
        co2 = np.interp(years, [p[0] for p in pts], [p[1] for p in pts])
        anom = model.predict(np.log(co2 / 280).reshape(-1,1))
        results[name] = pd.DataFrame({"year": years, "co2": co2, "anomalie": anom, "tmoy": ref + anom})
    return results

def chart(fig):
    fig.update_layout(**PLOT_LAYOUT)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="padding:0.5rem 0 1.5rem">
        <div style="font-size:0.65rem;font-weight:700;letter-spacing:0.15em;
                    color:{TEXT_DIM};text-transform:uppercase;margin-bottom:0.3rem">
            Dashboard
        </div>
        <div style="font-size:1.2rem;font-weight:700;color:{TEXT};letter-spacing:-0.02em">
            Climat France
        </div>
        <div style="font-size:0.78rem;color:{TEXT_DIM};margin-top:0.2rem">1931 — 2100</div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "nav",
        ["Vue d'ensemble", "Températures & Projections",
         "Feux de forêt", "Émissions & CO₂",
         "Précipitations", "Préconisations"],
        label_visibility="collapsed",
    )
    st.markdown(f"""
    <div style="position:absolute;bottom:2rem;left:1rem;right:1rem">
        <hr style="border-color:{BORDER};margin-bottom:0.8rem">
        <div style="font-size:0.7rem;color:{TEXT_DIM};line-height:1.6">
            Sources : Météo-France · NOAA<br>SDES · GéoRisques · VigiEau<br>
            <span style="color:{TEXT_DIM};opacity:0.5">IPCC AR6 · PNACC 3</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
def page_header(title, sub):
    st.markdown(f"""
    <div class="page-header">
        <p class="page-title">{title}</p>
        <p class="page-sub">{sub}</p>
    </div>
    """, unsafe_allow_html=True)

def kpi(label, value, sub, accent):
    st.markdown(f"""
    <div class="kpi-card" style="--accent:{accent}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

def section(label):
    st.markdown(f'<div class="section-label">{label}</div>', unsafe_allow_html=True)

def reco(title, color, items, source):
    items_html = "".join(f'<div class="reco-item">{i}</div>' for i in items)
    st.markdown(f"""
    <div class="reco-card" style="--accent-reco:{color}">
        <div class="reco-title">{title}</div>
        {items_html}
        <span class="source-tag">{source}</span>
    </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — Vue d'ensemble
# ══════════════════════════════════════════════════════════════════════════════
if page == "Vue d'ensemble":
    page_header(
        "Projections Climatiques — France",
        "Analyse historique 1931–2023 · Modèle IA log-linéaire · Projections IPCC AR6 jusqu'en 2100"
    )

    with st.spinner("Chargement des données..."):
        annual, ref   = load_temperatures()
        co2_df        = load_co2()
        fires_df      = load_fires()
        empreinte     = load_empreinte()
        model, ref_t, _, _  = build_model()
        hot_days, _   = load_hot_days()

    anom_2023  = annual[annual.year==2023]["anomalie"].values[0]
    co2_last   = co2_df["co2_ppm"].iloc[-1]
    fires_surf = fires_df["surface_totale_ha"].sum()
    emp_last   = empreinte["empreinte_carbone_tCO2e_par_habitant"].iloc[-1]
    hot_2023   = hot_days[hot_days.year==2023]["jours_30"].values
    hot_2023   = int(hot_2023[0]) if len(hot_2023) else 0
    hot_ref    = hot_days[(hot_days.year>=1961)&(hot_days.year<=1990)]["jours_30"].mean()

    section("Indicateurs clés 2023-2024")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: kpi("Anomalie température", f"+{anom_2023:.2f}°C", "vs référence 1961–1990", RED)
    with c2: kpi("CO₂ atmosphérique", f"{co2_last:.0f} ppm", "Mauna Loa · NOAA 2024", AMBER)
    with c3: kpi("Surface brûlée cumulée", f"{fires_surf/1e6:.1f} Mha", "Incendies France 2003–2024", "#f97316")
    with c4: kpi("Empreinte carbone", f"{emp_last} t", "CO₂e par habitant · 2024", BLUE)
    with c5: kpi("Jours TX ≥ 30°C", f"{hot_2023} j", f"Paris-Montsouris 2023 · réf. {hot_ref:.0f} j/an", RED)

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

    col_l, col_r = st.columns([3, 2])

    with col_l:
        section("Anomalie de température France 1931 – 2023")
        fig = go.Figure()
        # Barres colorées
        colors = [RED if v > 0 else BLUE for v in annual["anomalie"]]
        fig.add_bar(x=annual["year"], y=annual["anomalie"],
                    marker_color=colors, marker_opacity=0.55, name="Anomalie")
        # Rolling 10 ans
        roll = annual["anomalie"].rolling(10, center=True).mean()
        fig.add_scatter(x=annual["year"], y=roll, mode="lines",
                        line=dict(color="#f8fafc", width=2.5), name="Moyenne 10 ans", opacity=0.9)
        fig.add_hline(y=0, line_color=TEXT_DIM, line_width=1)
        fig.update_layout(height=310, showlegend=True,
                          legend=dict(orientation="h", y=1.12, font=dict(color=TEXT_SUB)),
                          **{k: v for k, v in PLOT_LAYOUT.items() if k not in ("margin", "legend")},
                          margin=dict(t=10, b=30, l=40, r=10))
        chart(fig)

    with col_r:
        section("Concentration CO₂ — jauge")
        fig_g = go.Figure(go.Indicator(
            mode="gauge+number",
            value=co2_last,
            number={"suffix": " ppm", "font": {"size": 36, "color": TEXT, "family": "Inter"}},
            gauge={
                "axis": {"range": [280, 600], "tickwidth": 1,
                         "tickcolor": TEXT_DIM, "tickfont": {"color": TEXT_DIM}},
                "bar": {"color": AMBER, "thickness": 0.25},
                "bgcolor": BG_CARD2,
                "bordercolor": BORDER,
                "steps": [
                    {"range": [280, 350], "color": "rgba(59,130,246,0.15)"},
                    {"range": [350, 450], "color": "rgba(245,158,11,0.15)"},
                    {"range": [450, 600], "color": "rgba(239,68,68,0.15)"},
                ],
                "threshold": {"line": {"color": RED, "width": 2.5}, "value": 450},
            }
        ))
        fig_g.update_layout(height=220, paper_bgcolor="rgba(0,0,0,0)",
                            font=dict(color=TEXT_SUB, family="Inter"),
                            margin=dict(t=20, b=10, l=30, r=30))
        st.plotly_chart(fig_g, use_container_width=True, config={"displayModeBar": False})
        st.markdown(f"""
        <div style="display:flex;gap:0.5rem;margin-top:0.5rem">
            <div style="flex:1;background:{BG_CARD2};border:1px solid {BORDER};border-radius:8px;
                        padding:0.7rem;text-align:center">
                <div style="font-size:0.68rem;color:{TEXT_DIM};text-transform:uppercase;letter-spacing:0.06em">Préindustriel</div>
                <div style="font-size:1.1rem;font-weight:700;color:{BLUE}">280 ppm</div>
            </div>
            <div style="flex:1;background:{BG_CARD2};border:1px solid {BORDER};border-radius:8px;
                        padding:0.7rem;text-align:center">
                <div style="font-size:0.68rem;color:{TEXT_DIM};text-transform:uppercase;letter-spacing:0.06em">+vs 1850</div>
                <div style="font-size:1.1rem;font-weight:700;color:{AMBER}">+{co2_last-280:.0f} ppm</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Projections résumé
    section("Projections 2030 · 2050 · 2100")
    proj = project_scenario(model, ref_t)
    cols = st.columns(3)
    for i, (name, color) in enumerate(SCENARIO_COLORS.items()):
        df_s = proj[name]
        vals = {yr: df_s[df_s.year==yr]["anomalie"].values[0] for yr in [2030, 2050, 2100]}
        with cols[i]:
            st.markdown(f"""
            <div class="kpi-card" style="--accent:{color}">
                <div class="kpi-label">{name}</div>
                <div style="display:flex;gap:1rem;margin-top:0.8rem">
                    <div>
                        <div style="font-size:0.65rem;color:{TEXT_DIM};text-transform:uppercase;letter-spacing:0.06em">2030</div>
                        <div style="font-size:1.4rem;font-weight:700;color:{color}">{vals[2030]:+.1f}°C</div>
                    </div>
                    <div>
                        <div style="font-size:0.65rem;color:{TEXT_DIM};text-transform:uppercase;letter-spacing:0.06em">2050</div>
                        <div style="font-size:1.4rem;font-weight:700;color:{color}">{vals[2050]:+.1f}°C</div>
                    </div>
                    <div>
                        <div style="font-size:0.65rem;color:{TEXT_DIM};text-transform:uppercase;letter-spacing:0.06em">2100</div>
                        <div style="font-size:1.4rem;font-weight:700;color:{color}">{vals[2100]:+.1f}°C</div>
                    </div>
                </div>
                <div class="kpi-sub" style="margin-top:0.6rem">anomalie vs 1961–1990</div>
            </div>
            """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — Températures & Projections
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Températures & Projections":
    page_header(
        "Températures & Projections",
        "4 modèles comparés (Linéaire · Polynomiale · Random Forest · Gradient Boosting) · RMSE / MAE / MAPE · Projections IPCC AR6"
    )

    model, ref_t, model_metrics, best_model_name = build_model()
    annual, _    = load_temperatures()

    target_year = st.slider("Horizon de projection", 2030, 2100, 2060, step=5,
                            help="Faites glisser pour changer l'horizon de projection")
    proj = project_scenario(model, ref_t, target_year)

    section("Anomalie de température — historique & projections")
    fig = go.Figure()
    fig.add_scatter(x=annual["year"], y=annual["anomalie"],
                    mode="lines", line=dict(color=TEXT_DIM, width=1),
                    name="Historique (brut)", opacity=0.5)
    roll = annual["anomalie"].rolling(5, center=True).mean()
    fig.add_scatter(x=annual["year"], y=roll, mode="lines",
                    line=dict(color="#f8fafc", width=2), name="Historique (moy. 5 ans)")
    for name, color in SCENARIO_COLORS.items():
        df_s = proj[name]
        fig.add_scatter(x=df_s["year"], y=df_s["anomalie"], mode="lines",
                        line=dict(color=color, width=2.5), name=name)
        val = df_s[df_s.year==target_year]["anomalie"].values[0]
        fig.add_scatter(x=[target_year], y=[val], mode="markers+text",
                        marker=dict(size=9, color=color, symbol="circle"),
                        text=[f" {val:+.1f}°C"], textposition="middle right",
                        textfont=dict(size=11, color=color, family="Inter"), showlegend=False)

    fig.add_vline(x=2024, line_dash="dot", line_color=TEXT_DIM, line_width=1)
    fig.add_hline(y=0, line_color=TEXT_DIM, line_width=0.7)
    fig.add_vrect(x0=1961, x1=1990, fillcolor=f"rgba(59,130,246,0.06)", line_width=0,
                  annotation_text="Référence", annotation_position="top left",
                  annotation_font=dict(color=TEXT_DIM, size=10))
    fig.update_layout(height=420, legend=dict(orientation="h", y=1.08),
                      **{k:v for k,v in PLOT_LAYOUT.items() if k not in ("margin", "legend")},
                      margin=dict(t=20, b=40, l=50, r=100),
                      yaxis_title="Anomalie (°C vs 1961–1990)",
                      xaxis_title="Année")
    chart(fig)

    # Comparaison des modèles
    section("Comparaison des modèles prédictifs")
    df_metrics = pd.DataFrame(model_metrics).T.reset_index()
    df_metrics.columns = ["Modèle", "RMSE", "MAE", "MAPE (%)"]
    df_metrics["Meilleur"] = df_metrics["Modèle"].apply(
        lambda n: "★ Sélectionné" if n == best_model_name else ""
    )

    fig_m = go.Figure()
    colors_bar = [GREEN if n == best_model_name else BLUE for n in df_metrics["Modèle"]]
    for i, metric in enumerate(["RMSE", "MAE"]):
        fig_m.add_bar(
            name=metric,
            x=df_metrics["Modèle"],
            y=df_metrics[metric],
            marker_color=GREEN if metric == "RMSE" else AMBER,
            opacity=0.75 if i == 0 else 0.55,
        )
    fig_m.update_layout(
        height=280, barmode="group",
        legend=dict(orientation="h", y=1.1),
        yaxis_title="Erreur (°C)",
        **{k: v for k, v in PLOT_LAYOUT.items() if k not in ("margin", "legend")},
        margin=dict(t=10, b=80, l=50, r=20),
    )
    chart(fig_m)

    st.dataframe(
        df_metrics.set_index("Modèle"),
        use_container_width=True,
    )
    st.caption(f"Entraînement sur 80 % des données (1958–2012), test sur 20 % (2013–2023). "
               f"Modèle retenu pour les projections : **{best_model_name}**.")

    # Tableau
    section("Valeurs projetées par scénario")
    rows = []
    for name, color in SCENARIO_COLORS.items():
        df_s = proj[name]
        row = {"Scénario": name}
        for yr in [2030, 2050, 2075, 2100]:
            if yr <= target_year:
                v = df_s[df_s.year==yr]["anomalie"].values[0]
                row[str(yr)] = f"{v:+.2f}°C"
        rows.append(row)
    df_table = pd.DataFrame(rows).set_index("Scénario")
    st.dataframe(df_table, use_container_width=True)

    # TX vs TN
    section("Asymétrie jours / nuits — TXmax vs TNmin")
    ref_tx = annual[(annual.year>=1961)&(annual.year<=1990)]["tx"].mean()
    ref_tn = annual[(annual.year>=1961)&(annual.year<=1990)]["tn"].mean()
    annual["anom_tx"] = (annual["tx"] - ref_tx).rolling(5, center=True).mean()
    annual["anom_tn"] = (annual["tn"] - ref_tn).rolling(5, center=True).mean()
    fig2 = go.Figure()
    fig2.add_scatter(x=annual["year"], y=annual["anom_tx"],
                     name="Tmax — jours", line=dict(color=RED, width=2))
    fig2.add_scatter(x=annual["year"], y=annual["anom_tn"],
                     name="Tmin — nuits", line=dict(color=BLUE, width=2))
    fig2.add_hline(y=0, line_color=TEXT_DIM, line_width=0.7)
    fig2.update_layout(height=280, legend=dict(orientation="h", y=1.12),
                       yaxis_title="°C (moyenne mobile 5 ans)", xaxis_title="Année",
                       **{k:v for k,v in PLOT_LAYOUT.items() if k not in ("margin", "legend")},
                       margin=dict(t=10, b=40, l=50, r=20))
    chart(fig2)

    # Jours TX >= 30°C
    section("Jours TX ≥ 30°C par département — carte & évolution")
    hot_days, hot_ref = load_hot_days()
    hot_dept          = load_hot_days_by_dept()
    geojson_t         = get_dept_geojson()

    col_hmap, col_hts = st.columns([1, 1])

    with col_hmap:
        year_hot = st.slider("Année", 1950, 2024, 2023, key="hot_year")
        dept_yr = hot_dept[hot_dept["year"] == year_hot].copy()
        if geojson_t:
            dept_names_t = {f["properties"]["code"]: f["properties"]["nom"]
                            for f in geojson_t["features"]}
            dept_yr["nom"] = dept_yr["dept"].map(dept_names_t).fillna("")
            fig_hmap = px.choropleth(
                dept_yr, geojson=geojson_t,
                locations="dept", featureidkey="properties.code",
                color="jours_30",
                color_continuous_scale=[[0,"#111827"],[0.3,"#7c2d12"],
                                        [0.6,"#ef4444"],[1,"#fbbf24"]],
                range_color=[0, dept_hot_max := int(hot_dept["jours_30"].quantile(0.99))],
                hover_name="nom",
                hover_data={"dept": True, "jours_30": True, "nom": False},
                labels={"jours_30": "Jours TX≥30°C", "dept": "Dép."},
            )
            fig_hmap.update_geos(fitbounds="locations", visible=False, bgcolor="rgba(0,0,0,0)")
            fig_hmap.update_layout(
                height=380, paper_bgcolor="rgba(0,0,0,0)",
                geo_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=0, b=0, l=0, r=0),
                coloraxis_colorbar=dict(
                    title="Jours", thickness=10,
                    tickfont=dict(color=TEXT_SUB),
                    titlefont=dict(color=TEXT_SUB),
                ),
            )
            hot_event = st.plotly_chart(
                fig_hmap, use_container_width=True,
                config={"displayModeBar": False},
                on_select="rerun", key="hot_dept_map",
                selection_mode="points",
            )
            selected_hot_dept = None
            if hot_event and hot_event.selection and hot_event.selection.points:
                selected_hot_dept = hot_event.selection.points[0].get("location")

            all_depts_h = sorted(hot_dept["dept"].unique())
            dept_labels_h = {d: f"{d} – {dept_names_t.get(d,'')}" for d in all_depts_h}
            sel_h = st.selectbox(
                "Département", ["Tous"] + all_depts_h,
                format_func=lambda x: "Tous (moyenne nationale)" if x == "Tous" else dept_labels_h.get(x, x),
                index=(["Tous"] + all_depts_h).index(selected_hot_dept) if selected_hot_dept in all_depts_h else 0,
                key="hot_dept_sel",
            )
            if sel_h != "Tous":
                selected_hot_dept = sel_h

    with col_hts:
        if selected_hot_dept and selected_hot_dept in hot_dept["dept"].values:
            df_hts  = hot_dept[hot_dept["dept"] == selected_hot_dept].copy()
            ref_hts = df_hts[(df_hts.year >= 1961) & (df_hts.year <= 1990)]["jours_30"].mean()
            nom_h   = dept_names_t.get(selected_hot_dept, selected_hot_dept) if geojson_t else selected_hot_dept
            title_h = f"Dép. {selected_hot_dept} — {nom_h}"
        else:
            df_hts  = hot_days.copy()
            ref_hts = hot_ref
            title_h = "Moyenne nationale"

        section(f"Évolution — {title_h}")
        fig3 = go.Figure()
        fig3.add_bar(x=df_hts["year"], y=df_hts["jours_30"],
                     marker_color=[RED if v > ref_hts else TEXT_DIM for v in df_hts["jours_30"]],
                     marker_opacity=0.7, name="Jours TX≥30°C")
        roll_h = df_hts["jours_30"].rolling(10, center=True).mean()
        fig3.add_scatter(x=df_hts["year"], y=roll_h, mode="lines",
                         line=dict(color="#f8fafc", width=2.5), name="Tendance 10 ans")
        fig3.add_hline(y=ref_hts, line_dash="dot", line_color=BLUE, line_width=1.5,
                       annotation_text=f" Réf. 1961–1990 : {ref_hts:.0f} j/an",
                       annotation_font=dict(size=9, color=BLUE))
        fig3.update_layout(height=380, legend=dict(orientation="h", y=1.1),
                           yaxis_title="Nombre de jours", xaxis_title="Année",
                           **{k:v for k,v in PLOT_LAYOUT.items() if k not in ("margin", "legend")},
                           margin=dict(t=10, b=40, l=50, r=20))
        chart(fig3)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — Feux de forêt
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Feux de forêt":
    page_header("Feux de forêt", "Base BDIFF · 59 618 incendies · France métropolitaine · 2003–2024")

    fires   = load_fires()
    geojson = get_dept_geojson()

    year_range = st.slider("Période d'analyse", 2014, 2024, (2014, 2024))
    df_f = fires[(fires.annee >= year_range[0]) & (fires.annee <= year_range[1])]

    section("Synthèse période sélectionnée")
    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi("Incendies", f"{len(df_f):,}", f"{year_range[0]}–{year_range[1]}", RED)
    with c2: kpi("Surface brûlée", f"{df_f['surface_totale_ha'].sum():,.0f} ha", "total cumulé", "#f97316")
    with c3: kpi("Dont forêt", f"{df_f['surface_foret_ha'].sum():,.0f} ha", f"{df_f['surface_foret_ha'].sum()/df_f['surface_totale_ha'].sum()*100:.0f}% du total", AMBER)
    with c4:
        top_dept = df_f.groupby("departement")["surface_totale_ha"].sum().idxmax()
        top_surf = df_f.groupby("departement")["surface_totale_ha"].sum().max()
        kpi("Dép. le plus touché", f"Dép. {top_dept}", f"{top_surf:,.0f} ha cumulés", BLUE)

    col_l, col_r = st.columns([1, 1])

    with col_l:
        section("Surface brûlée par département")
        dept_agg = df_f.groupby("departement").agg(
            surface=("surface_totale_ha","sum"),
            nb=("surface_totale_ha","count"),
        ).reset_index()
        if geojson:
            fig_map = px.choropleth(
                dept_agg, geojson=geojson,
                locations="departement", featureidkey="properties.code",
                color="surface",
                color_continuous_scale=[[0,"#1a0a00"],[0.3,"#7c2d12"],[0.6,"#ea580c"],[1,"#fbbf24"]],
                hover_data={"nb": True, "surface": ":.0f"},
                labels={"surface":"Surface (ha)","nb":"Incendies"},
            )
            fig_map.update_geos(fitbounds="locations", visible=False,
                                bgcolor="rgba(0,0,0,0)")
            fig_map.update_layout(height=380, paper_bgcolor="rgba(0,0,0,0)",
                                  geo_bgcolor="rgba(0,0,0,0)",
                                  margin=dict(t=0,b=0,l=0,r=0),
                                  coloraxis_colorbar=dict(
                                      title="ha", thickness=10,
                                      tickfont=dict(color=TEXT_SUB),
                                      titlefont=dict(color=TEXT_SUB)))
            st.plotly_chart(fig_map, use_container_width=True, config={"displayModeBar": False})
        else:
            st.dataframe(dept_agg.sort_values("surface", ascending=False).head(15))

    with col_r:
        section("Évolution annuelle")
        by_year = fires.groupby("annee").agg(
            nb=("surface_totale_ha","count"),
            surface=("surface_totale_ha","sum"),
        ).reset_index()
        fig_ts = make_subplots(specs=[[{"secondary_y": True}]])
        fig_ts.add_bar(x=by_year["annee"], y=by_year["surface"],
                       name="Surface (ha)", marker_color=RED, marker_opacity=0.6)
        fig_ts.add_scatter(x=by_year["annee"], y=by_year["nb"],
                           name="Nb incendies", mode="lines+markers",
                           line=dict(color=AMBER, width=2),
                           marker=dict(size=5), secondary_y=True)
        fig_ts.update_layout(height=380, legend=dict(orientation="h", y=1.1,
                                                      font=dict(color=TEXT_SUB)),
                             **{k:v for k,v in PLOT_LAYOUT.items() if k not in ("margin", "legend")},
                             margin=dict(t=10, b=40, l=50, r=50))
        fig_ts.update_yaxes(title_text="Surface (ha)", secondary_y=False,
                            gridcolor="rgba(255,255,255,0.04)", title_font=dict(color=TEXT_SUB))
        fig_ts.update_yaxes(title_text="Nb incendies", secondary_y=True,
                            gridcolor="rgba(255,255,255,0.04)", title_font=dict(color=TEXT_SUB))
        st.plotly_chart(fig_ts, use_container_width=True, config={"displayModeBar": False})

    section("Saisonnalité des incendies")
    fires["mois"] = pd.to_datetime(fires["date_alerte"], errors="coerce").dt.month
    by_month = fires.dropna(subset=["mois"]).groupby("mois")["surface_totale_ha"].sum().reset_index()
    mois_labels = ["Jan","Fév","Mar","Avr","Mai","Jun","Jul","Aoû","Sep","Oct","Nov","Déc"]
    by_month["label"] = by_month["mois"].apply(lambda x: mois_labels[int(x)-1])
    fig_m = go.Figure(go.Bar(
        x=by_month["label"], y=by_month["surface_totale_ha"],
        marker_color=[RED if m in [7,8,9] else AMBER if m in [6,10] else TEXT_DIM
                      for m in by_month["mois"]],
        marker_opacity=0.8,
    ))
    fig_m.update_layout(height=240, yaxis_title="Surface totale (ha)",
                        **{k:v for k,v in PLOT_LAYOUT.items() if k not in ("margin", "legend")},
                        margin=dict(t=10, b=30, l=50, r=10))
    chart(fig_m)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — Émissions & CO₂
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Émissions & CO₂":
    page_header("Émissions & CO₂", "Concentrations NOAA 1958–2026 · Émissions France SDES 1995–2024 · Empreinte carbone par habitant")

    co2  = load_co2()
    emi  = load_emissions()
    emp  = load_empreinte()
    ges  = load_ges_secteur()

    section("Concentration atmosphérique CO₂")
    fig = go.Figure()
    fig.add_scatter(x=co2["year"], y=co2["co2_ppm"],
                    fill="tozeroy", fillcolor="rgba(245,158,11,0.07)",
                    line=dict(color=AMBER, width=2), name="CO₂ ppm")
    for y_val, label, color in [(280,"Préindustriel",TEXT_DIM),(350,"Seuil sécurité",BLUE),(420,"Actuel",RED)]:
        fig.add_hline(y=y_val, line_dash="dot", line_color=color, line_width=1.2,
                      annotation_text=f" {label} · {y_val} ppm",
                      annotation_font=dict(size=9, color=color))
    fig.update_layout(height=300, yaxis_title="ppm", xaxis_title="Année",
                      **{k:v for k,v in PLOT_LAYOUT.items() if k not in ("margin", "legend")},
                      margin=dict(t=10, b=40, l=50, r=20))
    chart(fig)

    col1, col2 = st.columns(2)
    with col1:
        section("Émissions France — production vs importées")
        fig2 = go.Figure()
        fig2.add_scatter(x=emi["annee"], y=emi["emissions_production_interieure_MtCO2e"],
                         name="Intérieures", fill="tozeroy",
                         fillcolor=f"rgba(59,130,246,0.1)",
                         line=dict(color=BLUE, width=2))
        fig2.add_scatter(x=emi["annee"], y=emi["emissions_importees_MtCO2e"],
                         name="Importées", fill="tozeroy",
                         fillcolor=f"rgba(239,68,68,0.1)",
                         line=dict(color=RED, width=2))
        fig2.update_layout(height=300, yaxis_title="MtCO₂e", xaxis_title="Année",
                           legend=dict(orientation="h", y=1.1, font=dict(color=TEXT_SUB)),
                           **{k:v for k,v in PLOT_LAYOUT.items() if k not in ("margin", "legend")},
                           margin=dict(t=10, b=40, l=50, r=20))
        chart(fig2)

    with col2:
        section("Empreinte carbone par habitant")
        fig3 = go.Figure()
        fig3.add_scatter(x=emp["annee"], y=emp["empreinte_carbone_tCO2e_par_habitant"],
                         mode="lines+markers", marker=dict(size=4, color=BLUE),
                         line=dict(color=BLUE, width=2.5), fill="tozeroy",
                         fillcolor="rgba(59,130,246,0.07)")
        fig3.add_hline(y=2, line_dash="dash", line_color=GREEN, line_width=1.5,
                       annotation_text=" Objectif 2050 : 2 tCO₂e",
                       annotation_font=dict(size=9, color=GREEN))
        fig3.update_layout(height=300, yaxis_title="tCO₂e / habitant", xaxis_title="Année",
                           **{k:v for k,v in PLOT_LAYOUT.items() if k not in ("margin", "legend")},
                           margin=dict(t=10, b=40, l=50, r=20))
        chart(fig3)

    section("GES par secteur économique — SDES NAMEA")
    substances = sorted(ges["LIBELLE_SUBSTANCE"].dropna().unique())
    sub_sel = st.selectbox("Substance", substances, index=list(substances).index("Dioxyde de carbone") if "Dioxyde de carbone" in substances else 0)
    df_sec = ges[ges["LIBELLE_SUBSTANCE"]==sub_sel]
    top_sec = df_sec.groupby("LIBELLE_NACE_ET_MENAGES")["MASSE"].sum().nlargest(8).index
    df_sec  = df_sec[df_sec["LIBELLE_NACE_ET_MENAGES"].isin(top_sec)]
    df_piv  = df_sec.groupby(["ANNEE","LIBELLE_NACE_ET_MENAGES"])["MASSE"].sum().reset_index()
    PALETTE = [BLUE,"#7c3aed",AMBER,RED,GREEN,"#06b6d4","#ec4899","#84cc16"]
    fig4 = px.bar(df_piv, x="ANNEE", y="MASSE", color="LIBELLE_NACE_ET_MENAGES",
                  color_discrete_sequence=PALETTE,
                  labels={"MASSE":"Masse (kg)","ANNEE":"Année","LIBELLE_NACE_ET_MENAGES":"Secteur"})
    fig4.update_layout(height=360, legend=dict(orientation="h", y=-0.35, font=dict(size=9, color=TEXT_SUB)),
                       yaxis_title="kg", xaxis_title="Année",
                       **{k:v for k,v in PLOT_LAYOUT.items() if k not in ("margin", "legend")},
                       margin=dict(t=10, b=180, l=60, r=20))
    chart(fig4)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — Précipitations
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Précipitations":
    page_header("Précipitations & Sécheresse",
                "Séries homogénéisées LSH Météo-France · 1947–2023 · Anomalie vs référence 1961–1990 · Cliquer sur un département pour filtrer")

    with st.spinner("Chargement des données pluviométriques..."):
        precip, ref_p   = load_precipitation()
        dept_precip     = load_precip_by_dept()
        geojson         = get_dept_geojson()

    c1, c2, c3 = st.columns(3)
    with c1: kpi("Référence 1961–1990", f"{ref_p:.1f} mm", "précipitation mensuelle moy.", BLUE)
    with c2:
        last = precip.iloc[-1]
        color = BLUE if last["anomalie"] >= 0 else AMBER
        kpi(f"Dernière année ({int(last['year'])})", f"{last['precip_mm']:.1f} mm", f"anomalie : {last['anomalie']:+.1f} mm/mois", color)
    with c3:
        dry = len(precip[precip["anomalie"] < -2])
        kpi("Années en déficit", str(dry), "anomalie < −2 mm/mois", RED)

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    # ── Carte + série temporelle ───────────────────────────────────────────────
    col_map, col_ts = st.columns([1, 1])

    selected_dept = None

    with col_map:
        section("Carte — anomalie moyenne par département")
        dept_avg = (dept_precip.groupby("dept")
                    .agg(anomalie=("anomalie","mean"), precip_mm=("precip_mm","mean"))
                    .reset_index())

        if geojson:
            # Extract dept names from geojson
            dept_names = {f["properties"]["code"]: f["properties"]["nom"]
                          for f in geojson["features"]}
            dept_avg["nom"] = dept_avg["dept"].map(dept_names).fillna("")

            fig_map = px.choropleth(
                dept_avg, geojson=geojson,
                locations="dept", featureidkey="properties.code",
                color="anomalie",
                color_continuous_scale=[[0, "#7c2d12"],[0.35, "#991b1b"],
                                        [0.5, "#111827"],
                                        [0.65, "#1e3a5f"],[1, "#3b82f6"]],
                range_color=[-8, 8],
                hover_name="nom",
                hover_data={"dept": True, "precip_mm": ":.1f", "anomalie": ":.1f", "nom": False},
                labels={"anomalie": "Anomalie (mm/mois)", "precip_mm": "Préc. moy. (mm/mois)", "dept": "Dép."},
            )
            fig_map.update_geos(fitbounds="locations", visible=False, bgcolor="rgba(0,0,0,0)")
            fig_map.update_layout(
                height=440, paper_bgcolor="rgba(0,0,0,0)",
                geo_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=0, b=0, l=0, r=0),
                coloraxis_colorbar=dict(
                    title="Anom.<br>(mm/mois)", thickness=10,
                    tickfont=dict(color=TEXT_SUB),
                    titlefont=dict(color=TEXT_SUB),
                ),
            )
            map_event = st.plotly_chart(
                fig_map, use_container_width=True,
                config={"displayModeBar": False},
                on_select="rerun", key="precip_dept_map",
                selection_mode="points",
            )
            if map_event and map_event.selection and map_event.selection.points:
                pt = map_event.selection.points[0]
                selected_dept = pt.get("location")

        else:
            st.warning("GeoJSON indisponible — utilisez le sélecteur ci-dessous")

        # Fallback selectbox
        all_depts = sorted(dept_precip["dept"].unique())
        dept_labels = {d: f"{d} – {dept_names.get(d,'')}" for d in all_depts} if geojson else {d: d for d in all_depts}
        sel_options = ["Tous"] + all_depts
        sel_labels  = ["Tous (France entière)"] + [dept_labels[d] for d in all_depts]
        sel_idx = sel_options.index(selected_dept) if selected_dept in sel_options else 0
        sel_box = st.selectbox(
            "Département sélectionné",
            options=sel_options,
            format_func=lambda x: "Tous (France entière)" if x == "Tous" else dept_labels.get(x, x),
            index=sel_idx,
            key="precip_dept_sel",
        )
        if sel_box != "Tous":
            selected_dept = sel_box

    with col_ts:
        if selected_dept and selected_dept in dept_precip["dept"].values:
            df_ts   = dept_precip[dept_precip["dept"] == selected_dept].copy()
            nom_dept = dept_names.get(selected_dept, selected_dept) if geojson else selected_dept
            title_ts = f"Dép. {selected_dept} — {nom_dept}"
            anom_col = "anomalie"
            year_col = "year"
        else:
            df_ts    = precip.copy()
            title_ts = "France entière"
            anom_col = "anomalie"
            year_col = "year"

        section(f"Anomalie de précipitation — {title_ts}")
        fig_ts = go.Figure()
        fig_ts.add_bar(x=df_ts[year_col], y=df_ts[anom_col],
                       marker_color=[BLUE if v >= 0 else RED for v in df_ts[anom_col]],
                       marker_opacity=0.6, name="Anomalie")
        roll_ts = df_ts[anom_col].rolling(10, center=True).mean()
        fig_ts.add_scatter(x=df_ts[year_col], y=roll_ts, mode="lines",
                           line=dict(color="#f8fafc", width=2.5), name="Tendance 10 ans")
        fig_ts.add_hline(y=0, line_color=TEXT_DIM, line_width=1)
        fig_ts.update_layout(
            height=440,
            legend=dict(orientation="h", y=1.06, font=dict(color=TEXT_SUB)),
            yaxis_title="Anomalie (mm/mois)", xaxis_title="Année",
            **{k: v for k, v in PLOT_LAYOUT.items() if k not in ("margin", "legend")},
            margin=dict(t=10, b=40, l=50, r=20),
        )
        chart(fig_ts)

    # ── Analyse décennale nationale ────────────────────────────────────────────
    section("Écart à la normale par décennie — France entière")
    precip["decade"] = (precip["year"] // 10) * 10
    by_dec = precip.groupby("decade")["precip_mm"].mean().reset_index()
    by_dec["delta"] = by_dec["precip_mm"] - ref_p
    fig2 = go.Figure(go.Bar(
        x=by_dec["decade"].astype(str).str.cat(["s"] * len(by_dec)),
        y=by_dec["delta"],
        marker_color=[BLUE if v >= 0 else RED for v in by_dec["delta"]],
        marker_opacity=0.75,
        text=[f"{v:+.1f}" for v in by_dec["delta"]],
        textposition="outside",
        textfont=dict(color=TEXT_SUB, size=11),
    ))
    fig2.add_hline(y=0, line_color=TEXT_DIM, line_width=1)
    fig2.update_layout(height=280, yaxis_title="Écart vs réf. (mm/mois)",
                       **{k: v for k, v in PLOT_LAYOUT.items() if k != "margin"},
                       margin=dict(t=30, b=40, l=50, r=20))
    chart(fig2)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 6 — Préconisations
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Préconisations":
    page_header("Préconisations citoyennes",
                "Recommandations alignées PNACC 3 · Earth Action Report 2025 · SNBC · Accord de Paris")

    model, ref_t, _, _ = build_model()
    scenario_sel = st.selectbox("Scénario de référence", list(SCENARIO_COLORS.keys()), index=1)
    color_sel = SCENARIO_COLORS[scenario_sel]
    proj = project_scenario(model, ref_t)
    df_s = proj[scenario_sel]

    section("Projections pour ce scénario")
    cols = st.columns(3)
    for col, yr in zip(cols, [2030, 2050, 2100]):
        v = df_s[df_s.year==yr]["anomalie"].values[0]
        with col:
            kpi(f"Anomalie {yr}", f"{v:+.2f}°C", "vs référence 1961–1990", color_sel)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    col_l, col_r = st.columns(2)
    with col_l:
        reco("Risque accru de feux de forêt", RED, [
            "Respecter l'OLDé — débroussaillement 50m autour des habitations",
            "Privilégier des essences résistantes au feu en zone à risque",
            "Mettre en place des plans d'évacuation et voies d'accès pompiers",
            "Limiter les activités à risque ignition en période de sécheresse",
            "Soutenir la surveillance par drones et détection précoce",
        ], "PNACC 3 — Axe Forêts & Biodiversité")

        reco("Vagues de chaleur & caniculaire", AMBER, [
            "Végétaliser les espaces urbains — arbres, toitures et murs végétalisés",
            "Rénover les bâtiments — isolation, ventilation, protections solaires",
            "Identifier les personnes vulnérables et activer les plans canicule",
            "Développer des îlots de fraîcheur accessibles en ville",
            "Adapter les horaires de travail extérieur aux heures fraîches",
        ], "Earth Action Report 2025 — Adaptation urbaine")

    with col_r:
        reco("Sécheresse & stress hydrique", BLUE, [
            "Réduire la consommation d'eau domestique (objectif −10% d'ici 2030)",
            "Installer des dispositifs de récupération d'eau de pluie",
            "Substituer les cultures intensives par des variétés adaptées",
            "Anticiper les restrictions via la plateforme VigiEau",
            "Renaturer les zones humides pour recharge des nappes phréatiques",
        ], "PNACC 3 — Axe Eau & Milieux aquatiques")

        reco("Réduction de l'empreinte carbone", GREEN, [
            "Objectif national : 2 tCO₂e/hab. d'ici 2050 (actuel : 8.2)",
            "Privilégier la mobilité douce et les transports collectifs",
            "Adopter un régime alimentaire bas-carbone",
            "Accélérer la rénovation énergétique (CEE, MaPrimeRénov)",
            "Réduire les émissions importées via la consommation responsable",
        ], "SNBC — Neutralité carbone 2050")

    section("Alignement réglementaire")
    refs = [
        ("PNACC 3", "Adaptation nationale au changement climatique", "2030", BLUE),
        ("SNBC", "Neutralité carbone France", "2050", GREEN),
        ("Earth Action Report 2025", "Réduction émissions mondiales", "2030", AMBER),
        ("Accord de Paris", "Limiter le réchauffement à +1.5°C", "2100", RED),
        ("Fit for 55 (UE)", "−55% émissions vs 1990", "2030", "#7c3aed"),
    ]
    cols = st.columns(len(refs))
    for col, (name, desc, horizon, c) in zip(cols, refs):
        with col:
            st.markdown(f"""
            <div style="background:{BG_CARD};border:1px solid {BORDER};border-radius:10px;
                        padding:1rem;border-top:2px solid {c}">
                <div style="font-size:0.68rem;font-weight:700;color:{c};text-transform:uppercase;
                            letter-spacing:0.08em;margin-bottom:0.4rem">{name}</div>
                <div style="font-size:0.8rem;color:{TEXT_SUB};line-height:1.4;margin-bottom:0.5rem">{desc}</div>
                <div style="font-size:0.72rem;color:{TEXT_DIM}">Horizon {horizon}</div>
            </div>
            """, unsafe_allow_html=True)
