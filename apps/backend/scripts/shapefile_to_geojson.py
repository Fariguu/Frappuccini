"""
Script per convertire Shapefile stradario in GeoJSON.
Legge dataset/sources/stradario/Stradario.shp, filtra per Bari e salva in data/strade_bari.geojson.
Richiede: geopandas, matplotlib (per i plot opzionali).
Esegui da apps/backend: python scripts/shapefile_to_geojson.py
"""

import geopandas as gpd
import matplotlib.pyplot as plt
from pathlib import Path

# Path output: data/strade_bari.geojson (relativo alla root backend)
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_ROOT.parent.parent
OUTPUT_PATH = BACKEND_ROOT / "data" / "strade_bari.geojson"

# Shapefile: dataset/sources/stradario/
SHAPEFILE_PATH = PROJECT_ROOT / "dataset" / "sources" / "stradario" / "Stradario.shp"

# ===========================================
# 1. APRI SHAPEFILE
# ===========================================
print("Caricamento stradario...")
gdf = gpd.read_file(str(SHAPEFILE_PATH))
print(f"Dataset caricato! {len(gdf)} strade")
print("Colonne disponibili:", gdf.columns.tolist())
print("\nPrime 5 righe:")
print(gdf.head())

# 2. INFO BASE
print(f"\nSistema di coordinate: {gdf.crs}")
print(f"Estensione geografica: {gdf.total_bounds}")

# ===========================================
# 3. PLOT MAPPA COMPLETA
# ===========================================
fig, ax = plt.subplots(1, 1, figsize=(12, 10))
gdf.plot(ax=ax, linewidth=0.5, color='lightblue', edgecolor='black', alpha=0.7)
plt.title("Stradario Bari - Mappa Completa", fontsize=16)
plt.axis('off')
plt.tight_layout()
plt.show()

# ===========================================
# 4. FILTRA PER BARI (se hai colonna 'comune' o simile)
# ===========================================
# Sostituisci 'comune' con il nome effettivo dalla tua colonna
if 'comune' in gdf.columns:
    gdf_bari = gdf[gdf['comune'].str.contains('Bari', na=False)]
elif 'COD_COMUNE' in gdf.columns:
    gdf_bari = gdf[gdf['COD_COMUNE'] == '072021']  # ISTAT Bari
else:
    gdf_bari = gdf  # tutto il dataset se non trovi filtro
    print("Attenzione: non trovata colonna per filtrare Bari")

print(f"\nStrade Bari trovate: {len(gdf_bari)}")

# 5. PLOT SOLO BARI
if len(gdf_bari) > 0:
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    gdf_bari.plot(ax=ax, linewidth=0.8, edgecolor='darkblue', alpha=0.8)
    plt.title(f"Stradario Bari ({len(gdf_bari)} strade)", fontsize=16)
    plt.axis('off')
    plt.tight_layout()
    plt.show()

# ===========================================
# 6. STATISTICHE per HACKATHON (classificazione strade)
# ===========================================
# Cerca colonne tipo 'tipo', 'classe', 'gerarchia', 'categoria'
class_cols = [col for col in gdf.columns if any(x in col.lower() for x in ['tipo', 'classe', 'gerarchia', 'categoria', 'livello'])]
print("\nColonne di classificazione trovate:", class_cols)

if class_cols:
    col = class_cols[0]
    print(f"\nDistribuzione per {col}:")
    print(gdf[col].value_counts().head(10))
    
    # Plot per tipo strada
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    gdf.plot(ax=ax, column=col, linewidth=0.3, edgecolor='black', 
             cmap='tab20', legend=True, alpha=0.7)
    plt.title(f"Strade per {col}", fontsize=16)
    plt.axis('off')
    plt.tight_layout()
    plt.show()

# 7. SALVA come GeoJSON (per app Flutter/web)
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
gdf_bari.to_file(str(OUTPUT_PATH), driver='GeoJSON')
print(f"\nSalvato '{OUTPUT_PATH}'!")
