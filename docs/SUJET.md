# Hackathon – Projections Climatiques & IA

## Contexte

Projet destiné aux apprenants en **Mastère Informatique – Big Data & IA**.
Objectif : concevoir une solution complète allant de l'ingestion de données massives jusqu'à la production de **prédictions climatiques** et de **recommandations citoyennes actionnables**.

---

## Étapes du projet

### Étape 4 – Data Visualisation Impactante

Produire des projections climatiques pour **2030 / 2050 / 2100** sur au minimum trois scénarios :

| Scénario | Variation |
|---|---|
| Optimiste | +1,4°C |
| Intermédiaire | – |
| Pessimiste | +4,4°C |

**Dashboard final – contenu obligatoire :**
- Cartographie interactive multi-niveaux
- Graphiques comparant passé / présent / futur
- Indicateurs clés (jauges, alertes)
- Simulations personnalisables (slider temporel)

**Outils recommandés :** Streamlit, Dash, Power BI, Leaflet, Mapbox, Kepler.gl, Plotly

---

### Étape 5 – Préconisations Citoyennes

Transformer les résultats en actions concrètes selon les risques identifiés :

#### Risque Accru de Feux
- Débroussaillage
- Aménagement anti-incendie
- Procédures d'urgence

#### Sécheresse Accrue
- Réduction consommation d'eau
- Plantes résistantes
- Récupération d'eau

#### Augmentation Caniculaire
- Végétalisation
- Comportements individuels
- Dispositifs de rafraîchissement urbain

#### Réduction Empreinte Carbone
- Mobilité douce
- Alimentation bas carbone
- Rénovation énergétique

> Les préconisations doivent s'aligner avec : **PNACC 3**, **Earth Action Report 2025**, **Objectifs nationaux de neutralité carbone**

---

## Sources de données

### Sources Obligatoires

| Source | Contenu |
|---|---|
| Météo France / meteo.data.gouv.fr | Données climatiques historiques |
| Secten – CITEPA | Émissions de gaz à effet de serre |
| DRIAS | Projections climatiques (scénarios RCP/SSP) |
| NOAA | Concentrations CO₂/CH₄ |
| – | Événements extrêmes (feux, sécheresses, niveau de la mer) |
| Insee/SDES | Empreinte carbone française |

### Sources Optionnelles

- ERA5 (Copernicus), données satellitaires
- Données rurales/forestières (IGN, ONF)
- Biodiversité, surfaces brûlées
- Données socio-économiques (Insee)

---

## Livrables

### 1. Rapport Analytique
- Analyse historique du territoire
- Sélection et justification des indicateurs
- Méthodologie de modélisation IA
- Projections futures (2030, 2050, 2100)
- Recommandations climat-territoire

### 2. Dashboard Interactif
- Cartes interactives multi-échelles
- Graphiques comparant passé / présent / futur
- Simulations personnalisables
- Section actions citoyennes

### 3. Modèles IA & Pipeline
- Notebook(s) commenté(s)
- Artefacts modèles (MLflow)
- Documentation technique complète

### 4. Pitch
- Démonstration du Dashboard
- Narration Data-Driven
- Recommandations finales et impact citoyen

---

## Rôles

### Data (Data Engineers / Data Scientists)
- Définition du territoire d'études
- Sélection des indicateurs climatiques
- Modélisation IA
- Datavisualisation

### Chef de Projets IT
- Cadrer le périmètre fonctionnel (MVP réaliste)
- Prioriser les fonctionnalités (pipeline, modèles, Dashboard, recommandations)
- Découper le projet en lots et répartir les tâches
- Estimer les ressources (stockage, calcul, hébergement)
- Anticiper la mise en ligne (data.gouv.fr, publics cibles, lisibilité)

---

## Valeur Ajoutée

- Mobilisation de compétences techniques avancées
- Production d'un outil réellement utilisable pour la sensibilisation citoyenne
- Conformité avec : Chiffres clés du climat 2024, Earth Action Report 2025, PNACC 3, Projections DRIAS

### Valorisation optionnelle
Publier une réutilisation sur **data.gouv.fr** pour :
- Visibilité accrue
- Retours constructifs
- Dialogue avec producteurs de données
- Inspiration de la communauté data

---

## Ressources clés

- [meteo.data.gouv.fr](https://meteo.data.gouv.fr) – données météo et climatiques
- [DRIAS – Les futurs du climat](https://www.drias-climat.fr)
- [Secten – CITEPA](https://www.citepa.org/fr/secten/)
- [IPCC – Climate Change 2023 Synthesis Report](https://www.ipcc.ch/report/ar6/syr/)
- Rapport annuel 2025 – Haut conseil pour le climat
- Rapport France Stratégie 2025 – La France s'adapte (PNACC 3)
- Earth Action Report 2025 – KPMG
- Chiffres clés du climat France, Europe et Monde 2024 – Ministère des Territoires

---

> **Niveau de difficulté :** Confirmé
> **Principale difficulté identifiée :** Choix et utilisation des modèles de prédiction climatique
