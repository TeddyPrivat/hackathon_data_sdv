# Descriptif des données récupérées

---

## Météo-France — Observations Paris (dept 75)

### `Q_75_previous-1950-2024_RR-T-Vent.csv.gz`
- Données quotidiennes toutes stations du dept 75, 1950–2024
- Colonnes : date, précipitations (RR), Tmin/Tmax/Tmoy, vent (FFM, FXY...), rafales, durée pluie
- Format : CSV séparateur `;`, ~4 Mo compressé

### `Q_75_latest-2025-2026_RR-T-Vent.csv.gz`
- Même structure, données récentes 2025–2026

---

## Météo-France — LSH Longues Séries Homogénéisées

### `SH_RR_metropole/` (1 279 fichiers CSV)
- Cumul mensuel de précipitations (mm) par station, 1931–2023
- Format : `YYYYMM;VALEUR;Q_HOM`

### `SH_TX_metropole/` (321 fichiers CSV)
- Moyenne mensuelle Tmax (°C) par station, 1931–2023

### `SH_TN_metropole/` (294 fichiers CSV)
- Moyenne mensuelle Tmin (°C) par station, 1931–2023

> Chaque fichier = 1 station identifiée par son NUM_POSTE et NOM_USUEL

---

## Météo-France — Métadonnées

### `stations-meteo-france.csv` (14 729 lignes)
- Toutes les stations : id, nom, lon/lat/alt, dates d'ouverture/fermeture, département, types de mesures disponibles (daily/hourly/minutely)

---

## NOAA — Concentrations atmosphériques

### `co2_mm_mlo.csv` (816 lignes)
- CO₂ Mauna Loa mensuel, 1958–présent
- Colonnes : year, month, decimal date, average (ppm), deseasonalized, sdev

### `co2_mm_gl.csv`
- CO₂ moyenne mondiale mensuelle, 1979–présent
- Colonnes : year, month, decimal, average, average_unc, trend

### `ch4_mm_gl.csv` (510 lignes)
- Méthane (CH₄) mondial mensuel, 1983–présent
- Colonnes : year, month, decimal, average (ppb), average_unc, trend

### `n2o_mm_gl.csv` (300 lignes)
- Protoxyde d'azote (N₂O) mondial mensuel, 2001–présent
- Même structure que CH₄

---

## ADEME — Projections climatiques horaires

### `ademe_projections_2c.csv` (~10 Mo)
- Séries horaires scénario **+2°C** pour 8 zones climatiques françaises
- Colonnes : STATION, LAT/LON/ALT, MOIS, JOUR, HEURE, T2m (temp. air), T-1m (sol), Hur (humidité), RR (pluie), FF (vent), DD (direction), rayonnements (Rgh, Rdn, Rdi), pression (Ps)

### `ademe_projections_4c.csv` (~11 Mo)
- Même structure, scénario **+4°C**

---

## SDES — Émissions GES sectorielles

### `sdes_ges_namea.csv` (19 966 lignes)
- Émissions GES par secteur économique (format NAMEA/Eurostat), 2008–2020
- Colonnes : SUBSTANCE (CH4, CO2, N2O...), CODE_NACE (secteur), MASSE (tonnes), ANNEE, libellés

---

## Événements extrêmes

### `vigieau_arretes_2024.csv` (367 lignes)
- Arrêtés préfectoraux de restriction d'eau 2024 (sécheresses)
- Colonnes : département, dates, statut, zones d'alerte, niveau de gravité (vigilance / alerte / alerte renforcée / crise)

### `vigieau_zones_en_vigueur.geojson`
- Géométries des zones de restriction actuellement en vigueur (GeoJSON, ~10 Mo)

### `explore2_vcn10_region.csv` (164 940 lignes, ~37 Mo)
- Projections de débits fluviaux (VCN10 = débit minimum 10 jours consécutifs) par région
- Colonnes : territoire, scénario de réchauffement (+2°C / +2.7°C / +4°C), indicateur, statistique, résultat
- Référence 1976–2005 + projections jusqu'en 2100
