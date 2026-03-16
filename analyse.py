import pandas as pd

# Chargement en ignorant les lignes de méta-données
df = pd.read_csv('/Users/matteocherief/Desktop/hackathon_data_sdv/data/SH_RR_metropole/SH_MRR313005003.csv', sep=';', comment='#')

# Aperçu pour vérifier
print(df.head())
# Convertir YYYYMM en objet Date (ex: 195901 -> 1959-01-01)
df['DATE'] = pd.to_datetime(df['YYYYMM'].astype(str), format='%Y%m')

# Trier par date au cas où
df = df.sort_values('DATE')