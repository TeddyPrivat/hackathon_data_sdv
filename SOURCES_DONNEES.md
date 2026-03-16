# Sources de données — Projections Climatiques

> Inventaire complet des données ouvertes disponibles pour le projet.

---

## 1. Météo-France / meteo.data.gouv.fr

### Observations quotidiennes
- **Page :** https://www.data.gouv.fr/fr/datasets/donnees-climatologiques-de-base-quotidiennes/
- **Format :** CSV.GZ (626 fichiers, par département et décennie)
- **Contenu :** Tmin/Tmax, précipitations, vent, humidité, pression, neige — toutes stations
- **Période :** ~1850–présent (mise à jour quotidienne)
- **Pattern URL :**
  ```
  https://object.files.data.gouv.fr/meteofrance/data/synchro_ftp/BASE/QUOT/Q_[DEPT]_[PERIOD]_RR-T-Vent.csv.gz
  ```
  Exemple : `Q_75_latest-2025-2026_RR-T-Vent.csv.gz`

### Observations horaires
- **Page :** https://www.data.gouv.fr/fr/datasets/donnees-climatologiques-de-base-horaires/
- **Format :** CSV.GZ (par département et décennie)
- **Contenu :** Toutes variables, toutes stations, contrôle qualité
- **Période :** 1850–présent
- **Pattern URL :**
  ```
  https://object.files.data.gouv.fr/meteofrance/data/synchro_ftp/BASE/HOR/H_[DEPT]_[PERIOD].csv.gz
  ```

### Longues Séries Homogénéisées (LSH) — Référence changement climatique
- **Page :** https://www.data.gouv.fr/fr/datasets/donnees-changement-climatique-lsh-longues-series-homogeneisees/
- **Format :** ZIP/CSV
- **Contenu :** Séries mensuelles homogénéisées (Tmin, Tmax, précipitations, ensoleillement) — **référence officielle pour études climatiques**
- **Période :** 1931–2023
- **Téléchargements directs :**
  - Tmax métropole : https://object.files.data.gouv.fr/meteofrance/data/synchro_ftp/REF_CC/LSH/SH_TX_metropole.zip
  - Tmin métropole : https://object.files.data.gouv.fr/meteofrance/data/synchro_ftp/REF_CC/LSH/SH_TN_metropole.zip
  - Précipitations métropole : https://object.files.data.gouv.fr/meteofrance/data/synchro_ftp/REF_CC/LSH/SH_RR_metropole.zip
  - Ensoleillement métropole : https://object.files.data.gouv.fr/meteofrance/data/synchro_ftp/REF_CC/LSH/SH_IN_metropole.zip
  - Outre-mer Tmax/Tmin/RR : idem avec `_Outremer.zip`

### Données SYNOP — Stations principales (temps réel)
- **Page :** https://www.data.gouv.fr/fr/datasets/donnees-d-observation-des-principales-stations-meteorologiques/
- **Format :** CSV (intervalle 3h, maj quotidienne)
- **Contenu :** Température, humidité, vent, pression, précipitations, nébulosité
- **Période :** 1996–présent
- **Téléchargement :** https://www.data.gouv.fr/api/1/datasets/r/66f4cfd9-240d-4c6e-8c0b-532d26c2c1dc

### Métadonnées des stations
- **Format :** CSV
- **Contenu :** 14 729 stations (coordonnées, altitude, dates d'ouverture/fermeture)
- **Téléchargement direct :** https://static.data.gouv.fr/resources/stations-meteo-france/20250104-124154/stations-meteo-france.csv

---

## 2. Projections climatiques DRIAS

### DRIAS — Portail officiel
- **Portail :** https://www.drias-climat.fr/
- **Téléchargement :** https://www.drias-climat.fr/commande *(compte gratuit requis)*
- **Format :** NetCDF
- **Scénarios disponibles :**
  - RCP 2.6, 4.5, 8.5 (DRIAS-2020)
  - Trajectoires TRACC : +2°C, +2,7°C, +4°C (TRACC-2023)
- **Horizons temporels :** 2021–2050 (proche), 2041–2070 (moyen), 2071–2100 (lointain) + continu 1950–2100
- **Variables :** Température, précipitations, vent, événements extrêmes, risque feux, hydrologie

### Projections climatiques Socle Métropole — Hackathon 2025 (data.gouv.fr)
- **Page :** https://www.data.gouv.fr/fr/datasets/projections-climatiques-pour-le-hackathon-2025-socle-metropole/
- **Format :** NetCDF
- **Contenu :** Projections régionalisées France métropolitaine (RCM, CPRCM, modèles neuronaux)
- **Période :** 1850–2100
- **Accès S3 :** https://console.object.files.data.gouv.fr/browser/meteofrance-drias/SocleM-Climat-2025/

### Projections DRIAS sur data.gouv.fr
- **Page :** https://www.data.gouv.fr/fr/datasets/drias-projections-climatiques-pour-ladaptation-de-nos-societes/

---

## 3. CITEPA / Secten — Émissions GES

- **Page principale :** https://www.citepa.org/fr/secten/
- **Rapport Secten 2025 (PDF) :** https://www.citepa.org/wp-content/uploads/2025/06/Citepa_Secten-2025.pdf

| Fichier | Contenu | URL |
|---|---|---|
| GES éd. 2025 | CO2, CH4, N2O, HFC, PFC, SF6 par gaz | https://www.citepa.org/wp-content/uploads/2025/06/Citepa2025_gaz_a_effet_de_serre.zip |
| Polluants atm. 2025 | SO2, NOx, NH3, particules, métaux | https://www.citepa.org/wp-content/uploads/2025/06/Citepa2025_polluants.zip |
| Données par secteur 2025 | Transport, énergie, industrie, agriculture… | https://www.citepa.org/wp-content/uploads/2025/06/Citepa2025_donnees_par_secteur.zip |

- **Archives historiques :** https://ressources.citepa.org/historiques/secten/ *(toutes éditions depuis ~2010)*

---

## 4. NOAA — Concentrations atmosphériques

### CO2 — Mauna Loa (MLO)
- **Période :** 1958–présent
- Mensuel : https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_mm_mlo.csv
- Quotidien : https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_daily_mlo.csv
- Annuel : https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_annmean_mlo.csv

### CO2 — Moyenne mondiale
- Mensuel global : https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_mm_gl.csv
- Annuel global : https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_annmean_gl.csv

### CH4 — Méthane mondial
- **Période :** 1983–présent
- Mensuel : https://gml.noaa.gov/webdata/ccgg/trends/ch4/ch4_mm_gl.csv
- Annuel : https://gml.noaa.gov/webdata/ccgg/trends/ch4/ch4_annmean_gl.csv
- Page : https://gml.noaa.gov/ccgg/trends_ch4/

### N2O — Protoxyde d'azote mondial
- **Période :** 1983–2024
- Mensuel : https://gml.noaa.gov/webdata/ccgg/trends/n2o/n2o_mm_gl.csv
- Annuel : https://gml.noaa.gov/webdata/ccgg/trends/n2o/n2o_annmean_gl.csv

### SF6
- Page : https://gml.noaa.gov/ccgg/trends_sf6/

---

## 5. Copernicus / ERA5 (ECMWF)

> **Accès :** Compte gratuit requis sur https://cds.climate.copernicus.eu
> **Installation API Python :** `pip install cdsapi`

| Dataset | Résolution | Période | URL |
|---|---|---|---|
| ERA5 hourly single-levels | 0.25°, 1h | 1940–présent | https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels |
| ERA5 hourly pressure-levels | 0.25°, 1h | 1940–présent | https://cds.climate.copernicus.eu/datasets/reanalysis-era5-pressure-levels |
| ERA5 monthly single-levels | 0.25°, mensuel | 1940–présent | https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels-monthly-means |
| ERA5-Land hourly | 0.1°, 1h | 1950–présent | https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land |
| ERA5-Land monthly | 0.1°, mensuel | 1950–présent | https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land-monthly-means |
| CERRA (Europe régional) | haute résolution | 1984–présent | https://cds.climate.copernicus.eu/datasets/reanalysis-cerra-single-levels |
| CMIP6 (SSP1.9→SSP8.5) | global | 1850–2100 | https://cds.climate.copernicus.eu/datasets/projections-cmip6 |

- **Format :** GRIB (primaire) ou NetCDF4
- **CMIP6 scénarios :** SSP1-1.9, SSP1-2.6, SSP2-4.5, SSP3-7.0, SSP5-8.5 (+ historical)

---

## 6. ADEME — Données climatiques et carbone

### Données climatiques prospectives (bâtiment/TRACC)
- **Contenu :** Séries horaires (17 paramètres : température, rayonnement, humidité, vent…) pour 8 zones climatiques françaises
- **Scénarios :** +2°C, +2,7°C, +4°C (avec et sans vague de chaleur)

| Scénario | URL directe |
|---|---|
| +2°C | https://data.ademe.fr/data-fair/api/v1/datasets/donnees-climatiques-prospectives-france-2c/raw |
| +2,7°C | https://data.ademe.fr/data-fair/api/v1/datasets/donnees-climatiques-prospectives-france-27c/raw |
| +4°C | https://data.ademe.fr/data-fair/api/v1/datasets/donnees-climatiques-prospectives-france-4c/raw |
| +2°C + canicule | https://data.ademe.fr/data-fair/api/v1/datasets/donnees-climatiques-prospectives-france-2c-vague-de-chaleur/raw |
| +4°C + canicule | https://data.ademe.fr/data-fair/api/v1/datasets/donnees-climatiques-prospectives-france-4c-vague-de-chaleur/raw |

### Base Carbone® (facteurs d'émission officiels)
- **Page data.gouv.fr :** https://www.data.gouv.fr/fr/datasets/base-carbone/
- **CSV direct :** https://data.ademe.fr/data-fair/api/v1/datasets/base-carboner/raw

### Bilan GES des collectivités
- **Portail :** https://bilans-ges.ademe.fr/
- **Format :** CSV (53 MB, 10 887 organisations)

---

## 7. SDES / INSEE — Empreinte carbone et statistiques

### Empreinte carbone de la France
- **Page SDES :** https://www.statistiques.developpement-durable.gouv.fr/empreinte-carbone-de-la-france
- **Portail DiDo :** https://data.statistiques.developpement-durable.gouv.fr/
- **Contenu :** Émissions basées sur la consommation (production domestique + émissions importées) par catégorie de consommation
- **Période :** 1995–2022

### GES format AEA/NAMEA
- **Page :** https://www.data.gouv.fr/fr/datasets/gaz-a-effet-de-serre-et-polluants-atmospheriques-au-format-aea-ex-namea/
- **CSV direct :** https://www.data.gouv.fr/api/1/datasets/r/3e33c154-b738-488a-bdd9-18b7deaef182
- **Contenu :** Émissions nationales GES + polluants liées aux secteurs économiques (format Eurostat)
- **Période :** 2008–2020

### Conjoncture mensuelle de l'énergie
- **Page :** https://www.data.gouv.fr/fr/datasets/conjoncture-mensuelle-de-lenergie/
- **Contenu :** Offre/consommation énergétique mensuelle (charbon, pétrole, gaz, électricité, bois)
- **Période :** 1980–2026

### Indicateurs territoriaux de développement durable
- **Page :** https://www.data.gouv.fr/fr/datasets/indicateurs-territoriaux-de-developpement-durable-itdd/
- **Contenu :** 98+ indicateurs ODD à l'échelle nationale/régionale/départementale/communale
- **Période :** 1954–2025

---

## 8. Événements extrêmes

### Sécheresses — VigiEau (arrêtés de restriction)
- **Page :** https://www.data.gouv.fr/fr/datasets/donnee-secheresse-vigieau/
- **Format :** CSV, GeoJSON
- **Contenu :** Zones d'alerte sécheresse et arrêtés préfectoraux de restriction d'eau, mis à jour quotidiennement
- **Période :** 2013–présent
- **Téléchargements :**
  - Arrêtés 2024 : https://static.data.gouv.fr/resources/donnee-secheresse-vigieau/20260316-060938/arretes-2024.csv
  - Historique communes (2013–2025) : https://static.data.gouv.fr/resources/donnee-secheresse-vigieau/20260225-062330/historique-communes.zip *(471 MB)*
  - Carte en vigueur (GeoJSON) : https://regleau.s3.gra.perf.cloud.ovh.net/geojson/zones_arretes_en_vigueur.geojson

### Feux de forêt — BDIFF
- **Portail :** https://bdiff.agriculture.gouv.fr/
- **Page data.gouv.fr :** https://www.data.gouv.fr/fr/datasets/base-de-donnees-sur-les-incendies-de-forets-en-france-bdiff/
- **Contenu :** Points d'ignition et périmètres de feux, agrégés à la commune
- **Période :** 2006–2022 (national); 1949–2024 (certains départements)
- **Licence :** ODbL 2.0

### Submersion marine — Zones inondables (Directive Inondation)
- **Format :** GIS (Shapefile, MapInfo)
- **Contenu :** Cartographie des zones inondables par submersion marine sur les TRI côtiers
- **Exemple Bordeaux :** https://telechargement.sigena.fr/download/b89b0e33-8bb4-44b1-97ef-0013f45b30d5

### Hydrologie future — Explore2/TRACC (débits fluviaux)
- **Page :** https://www.data.gouv.fr/fr/datasets/indicateurs-de-debits-futurs-explore2-tracc-avec-detail-des-points-de-simulation/
- **Format :** CSV, Parquet
- **Contenu :** Projections de débits futurs (débit annuel moyen, crues, étiages) issues de 100+ modèles, par commune/département/EPCI
- **Période :** Référence 1976–2005 ; projections jusqu'en 2100

### Hub'Eau — API hydrométrie
- **URL API :** https://hubeau.eaufrance.fr/api/v2/hydrometrie/
- **Format :** JSON, CSV
- **Contenu :** Données temps réel et historiques de hauteur d'eau et débits (~5 000 stations)
- **Période :** Historique depuis 1900 ; temps réel toutes les 5 min

### GES EU-ETS (installations industrielles)
- **Page :** https://www.data.gouv.fr/fr/datasets/emissions-de-gaz-a-effet-de-serre-des-installations-soumises-a-quota-de-lue/
- **Format :** CSV, GeoJSON, Parquet
- **Contenu :** Émissions vérifiées des installations soumises aux quotas européens, géolocalisées
- **Période :** 2005–2024

---

## 9. IGN / ONF — Forêts et territoire

### Inventaire Forestier National (IFN)
- **Portail :** https://inventaire-forestier.ign.fr/dataIFN/
- **Format :** ZIP/CSV
- **Contenu :** Données parcellaires de l'inventaire forestier (espèces, diamètres, hauteurs, volumes, type de forêt)
- **Période :** 2005–2024 (campagnes annuelles)
- **Téléchargements :**
  - Historique complet 2005–2024 : https://inventaire-forestier.ign.fr/dataifn/data/export_dataifn_2005_2024.zip
  - Dernière campagne 2024 : https://inventaire-forestier.ign.fr/dataifn/data/export_dataifn_2024.zip

### BD TOPO Historique (IGN)
- **Page :** https://www.data.gouv.fr/fr/datasets/bd-topo-r-historique/
- **Format :** GIS (multiples formats)
- **Contenu :** Occupation du sol, bâtiments, hydrographie (analyse des changements d'usage)
- **Période :** 1993–2009

---

## 10. Tableau récapitulatif

| Source | Données | Format | Accès |
|---|---|---|---|
| Météo-France | Obs. quotidiennes (1850–présent) | CSV.GZ | Direct (pattern URL dept.) |
| Météo-France | LSH homogénéisées (1931–2023) | ZIP/CSV | Direct |
| Météo-France/DRIAS | Projections Socle Hackathon 2025 | NetCDF | data.gouv.fr (S3) |
| DRIAS | Projections RCP/TRACC | NetCDF | Compte gratuit drias-climat.fr |
| CITEPA/Secten | GES par gaz et secteur 1990–2023 | ZIP/Excel | Direct citepa.org |
| NOAA GML | CO2 Mauna Loa 1958–présent | CSV | Direct gml.noaa.gov |
| NOAA GML | CH4/N2O/SF6 mondial | CSV | Direct gml.noaa.gov |
| Copernicus ERA5 | Réanalyse météo mondiale 1940–présent | GRIB/NetCDF | Compte CDS gratuit |
| Copernicus CMIP6 | Projections SSP 1850–2100 | NetCDF | Compte CDS gratuit |
| ADEME | Projections climatiques +2/+4°C | CSV | Direct data.ademe.fr |
| ADEME | Base Carbone® facteurs émission | CSV | Direct data.ademe.fr |
| SDES | Empreinte carbone France 1995–2022 | Excel/CSV | DiDo SDES |
| SDES | GES format NAMEA 2008–2020 | CSV | Direct data.gouv.fr |
| VigiEau | Sécheresses 2013–présent | CSV/GeoJSON | Direct data.gouv.fr |
| BDIFF | Incendies forêts 2006–2022 | API | bdiff.agriculture.gouv.fr |
| Hub'Eau | Débits fluviaux 1900–présent | JSON/CSV | API hubeau.eaufrance.fr |
| Explore2/TRACC | Débits futurs jusqu'en 2100 | CSV/Parquet | data.gouv.fr |
| IGN IFN | Inventaire forêts 2005–2024 | ZIP/CSV | Direct inventaire-forestier.ign.fr |

---

## Notes d'accès

- **DRIAS :** Compte gratuit sur drias-climat.fr nécessaire pour télécharger les NetCDF
- **Copernicus CDS :** Compte gratuit sur cds.climate.copernicus.eu + `pip install cdsapi`
- **meteo.data.gouv.fr :** Interface JS uniquement ; tous les fichiers sont directement accessibles sur `object.files.data.gouv.fr`
- **SDES empreinte carbone :** Tableaux détaillés sur https://data.statistiques.developpement-durable.gouv.fr — rechercher "empreinte carbone"
