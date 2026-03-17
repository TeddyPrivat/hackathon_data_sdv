# Dashboard Climatique France

Dashboard interactif sur les données climatiques françaises (températures, émissions CO₂, incendies, précipitations).

## Lancement rapide

### 1. Prérequis

Python 3.10+ requis.

```bash
pip install -r requirements.txt
```

### 2. Lancer le serveur

**Depuis la racine du projet** (important — les chemins sont relatifs) :

```bash
python flask_app.py
```

Ouvrir ensuite : [http://localhost:8080](http://localhost:8080)

### 3. Chatbot (optionnel)

Le chatbot nécessite une clé API Mistral. Sans elle, tout le reste du dashboard fonctionne normalement.

```bash
cp .env.example .env
# éditer .env et renseigner MISTRAL_API_KEY
```

Puis lancer avec :

```bash
# macOS/Linux
MISTRAL_API_KEY=sk-... python flask_app.py

# Windows PowerShell
$env:MISTRAL_API_KEY="sk-..."; python flask_app.py
```

## Structure des données

```
data/
├── temperatures/      # Températures historiques Météo-France
├── emissions_gaz/     # CO₂, CH₄, N₂O, émissions France
├── feux/              # Incendies de forêt 2003-2024
├── precipitations/    # Précipitations mensuelles
├── projections/       # Scénarios ADEME +2°C / +4°C
└── stations-meteo-france.csv
```

## Alternatives

- **Rapport statique** (pas de serveur nécessaire) :
  ```bash
  python build_dashboard.py
  open dashboard.html
  ```

- **App Streamlit** :
  ```bash
  pip install streamlit
  streamlit run app.py
  ```
