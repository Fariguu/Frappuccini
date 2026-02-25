"""
Integrazione Stradario (shapefile) con vie bari.csv.
Legge Stradario.shp, fa matching con Odonimo, produce vie_bari_arricchite.csv
con lunghezza_m e road_type quando disponibili.

Uso:
  pip install geopandas
  python dataset/scripts/integrate_stradario_vie.py
"""

import os
import re
import unicodedata
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
DATASET_ROOT = SCRIPT_DIR.parent
VIE_CSV = DATASET_ROOT / "sources" / "vie_bari.csv"
STRADARIO_SHP = DATASET_ROOT / "sources" / "stradario" / "Stradario.shp"
OUTPUT_CSV = DATASET_ROOT / "processed" / "vie_bari_arricchite.csv"

# Prefissi da rimuovere per normalizzazione nome strada
PREFIXES = (
    "via ", "corso ", "viale ", "piazza ", "largo ", "lungomare ", "lung.re ",
    "piazzale ", "sottovia ", "ponte ", "traversa ", "vico ", "giardino ",
    "largo ", "piazzetta ", "strada ", "circonvallazione ", "raccordo ",
)


def normalize_name(name: str) -> str:
    """Normalizza nome strada per matching: minuscole, no accenti, no prefissi."""
    if not name or pd.isna(name):
        return ""
    s = str(name).strip().lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"\s+", " ", s)
    for p in PREFIXES:
        if s.startswith(p):
            s = s[len(p) :].strip()
            break
    s = s.split("(")[0].strip()
    s = re.sub(r"[,;.]", "", s)
    return s


def load_vie_bari() -> pd.DataFrame:
    """Carica vie bari.csv."""
    try:
        df = pd.read_csv(VIE_CSV, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(VIE_CSV, encoding="latin-1")
    df.columns = [c.strip() for c in df.columns]
    return df


def load_stradario() -> pd.DataFrame | None:
    """Carica shapefile Stradario e restituisce DataFrame con nome e lunghezza."""
    if not STRADARIO_SHP.exists():
        print(f"[WARNING] {STRADARIO_SHP} non trovato. Salto integrazione shapefile.")
        return None

    try:
        import geopandas as gpd
    except ImportError:
        print("[WARNING] geopandas non installato. Esegui: pip install geopandas")
        return None

    try:
        gdf = gpd.read_file(STRADARIO_SHP)
    except Exception as e:
        print(f"[WARNING] Errore lettura shapefile: {e}")
        return None

    # Cerca colonna nome (NOME, NAME, TOPONIMO, STRADA, etc.)
    name_col = None
    for c in gdf.columns:
        if c.upper() in ("NOME", "NAME", "TOPONIMO", "STRADA", "ODONIMO", "DENOM"):
            name_col = c
            break
    if name_col is None:
        for c in gdf.columns:
            if "nome" in c.lower() or "name" in c.lower() or "strada" in c.lower():
                name_col = c
                break
    if name_col is None:
        name_col = gdf.columns[0]

    # Lunghezza: colonna esplicita o da geometria
    length_col = None
    for c in gdf.columns:
        if c.upper() in ("LUNGHEZZA", "LENGTH", "SHAPE_LEN", "LEN"):
            length_col = c
            break
    if length_col is None:
        for c in gdf.columns:
            if "lung" in c.lower() or "len" in c.lower():
                length_col = c
                break

    gdf = gdf.to_crs("EPSG:4326") if gdf.crs else gdf
    if length_col and length_col in gdf.columns:
        lengths = gdf[length_col].astype(float)
    else:
        # Geometria in gradi: approssimazione metri (1 grado ~111320m a lat Bari)
        lengths = gdf.geometry.length * 111320

    records = []
    for idx, row in gdf.iterrows():
        name = str(row.get(name_col, "")).strip()
        if not name or name == "nan":
            continue
        len_val = float(lengths.loc[idx])
        records.append({
            "name_raw": name,
            "name_norm": normalize_name(name),
            "lunghezza_m": round(len_val, 1),
        })

    return pd.DataFrame(records)


def main():
    print("=== Integrazione Stradario → vie bari ===\n")

    df_vie = load_vie_bari()
    df_vie["Odonimo_clean"] = df_vie["Odonimo"].apply(
        lambda x: str(x).strip().split("(")[0].strip() if pd.notna(x) else ""
    )
    df_vie["Odonimo_norm"] = df_vie["Odonimo_clean"].apply(normalize_name)

    df_stradario = load_stradario()

    df_vie["lunghezza_m"] = None
    if df_stradario is not None and not df_stradario.empty:
        print(f"Stradario: {len(df_stradario)} segmenti caricati")
        # Aggrega per nome normalizzato (strade con più segmenti)
        agg = df_stradario.groupby("name_norm").agg({
            "lunghezza_m": "sum",
            "name_raw": "first",
        }).reset_index()

        matched = 0
        for idx, row in df_vie.iterrows():
            norm = row["Odonimo_norm"]
            if not norm:
                continue
            match = agg[agg["name_norm"] == norm]
            if not match.empty:
                df_vie.at[idx, "lunghezza_m"] = match["lunghezza_m"].iloc[0]
                matched += 1

        print(f"Match: {matched}/{len(df_vie)} strade da vie bari.csv")

    # Mantieni colonne originali + lunghezza_m
    out_cols = [c for c in df_vie.columns if c not in ("Odonimo_clean", "Odonimo_norm")]
    df_out = df_vie[out_cols].copy()
    if "lunghezza_m" not in df_out.columns:
        df_out["lunghezza_m"] = None

    df_out.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
    print(f"Salvataggio → {OUTPUT_CSV}")
    print("OK")


if __name__ == "__main__":
    main()
