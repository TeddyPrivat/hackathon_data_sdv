# Accès Azure Blob Storage — Données climatiques

## Informations de connexion

- **Storage account :** `hackathonclimadata`
- **Container :** `data`
- **URL de base :** `https://hackathonclimadata.blob.core.windows.net/data`
- **SAS Token (valide jusqu'au 20/03/2026) :**
  ```
  se=2026-03-20&sp=rl&sv=2026-02-06&ss=b&srt=sco&sig=tcvoluktCxYmfClwqj37nruFECYvzJ09ylN29l2eLa8%3D
  ```

## Utilisation en Python

```bash
pip install azure-storage-blob
```

```python
from azure.storage.blob import BlobServiceClient
import pandas as pd
from io import StringIO, BytesIO

SAS_TOKEN = "se=2026-03-20&sp=rl&sv=2026-02-06&ss=b&srt=sco&sig=tcvoluktCxYmfClwqj37nruFECYvzJ09ylN29l2eLa8%3D"
ACCOUNT_URL = "https://hackathonclimadata.blob.core.windows.net"

client = BlobServiceClient(account_url=ACCOUNT_URL, credential=SAS_TOKEN)

def read_csv(filename):
    blob = client.get_blob_client(container="data", blob=filename)
    data = blob.download_blob().readall()
    return pd.read_csv(BytesIO(data))

# Exemples
df_co2 = read_csv("co2_mm_mlo.csv")
df_ademe = read_csv("ademe_projections_2c.csv")
df_stations = read_csv("stations-meteo-france.csv")
```

## Fichiers disponibles

Voir [DONNEES.md](DONNEES.md) pour le descriptif complet de chaque fichier.
