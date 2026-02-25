"""
Costruisce un elenco completo di vie di Bari a partire da:
- GeoJSON stradale (`apps/backend/data/strade_bari.geojson`)
- CSV esistente (`dataset/processed/vie_bari_arricchite.csv` se esiste, altrimenti `dataset/vie bari.csv`)

Output:
- Aggiorna `dataset/processed/vie_bari_arricchite.csv` con tutte le vie denominate del GeoJSON
- Scrive anche `dataset/vie_bari_arricchite.csv` come CSV principale usato dal generatore di traffico.
"""

from __future__ import annotations

import json
import os
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
GEOJSON_PATH = REPO_ROOT / "apps" / "backend" / "data" / "strade_bari.geojson"

# Percorsi CSV
CSV_PROCESSED = SCRIPT_DIR / "processed" / "vie_bari_arricchite.csv"
CSV_RAW = SCRIPT_DIR / "vie bari.csv"
CSV_MAIN = SCRIPT_DIR / "vie_bari_arricchite.csv"


# Prefissi da rimuovere per normalizzazione nome strada
PREFIXES = (
    "via ",
    "corso ",
    "viale ",
    "piazza ",
    "largo ",
    "lungomare ",
    "lung.re ",
    "piazzale ",
    "sottovia ",
    "ponte ",
    "traversa ",
    "vico ",
    "giardino ",
    "largo ",
    "piazzetta ",
    "strada ",
    "circonvallazione ",
    "raccordo ",
)


def normalize_name(name: str) -> str:
    """Normalizza nome strada come in integrate_stradario.normalize_name."""
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


def load_geojson_vie(path: Path = GEOJSON_PATH) -> pd.DataFrame:
    """Estrae vie denominate dal GeoJSON e le aggrega per nome normalizzato."""
    if not path.exists():
        raise FileNotFoundError(f"GeoJSON non trovato: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    features: List[Dict[str, Any]] = data.get("features", [])
    rows: List[Dict[str, Any]] = []

    for feat in features:
        props = feat.get("properties", {}) or {}
        denom_raw = (props.get("denominazi") or "").strip()
        if not denom_raw:
            continue

        upper = denom_raw.upper()
        # Escludi strade senza denominazione reale
        if "SENZA DENOMINAZIONE" in upper or "SENZA NOME" in upper:
            continue

        denom_norm = normalize_name(denom_raw)
        if not denom_norm:
            continue

        quartiere = props.get("quartier_1") or props.get("quartiere_") or None
        length_val = props.get("lunghezza")
        try:
            lunghezza = float(length_val) if length_val is not None else None
        except (TypeError, ValueError):
            lunghezza = None

        rows.append(
            {
                "denominazi_raw": denom_raw,
                "denominazi_norm": denom_norm,
                "quartiere_geojson": quartiere,
                "lunghezza": lunghezza,
            }
        )

    if not rows:
        raise RuntimeError("Nessuna via denominata trovata nel GeoJSON.")

    df = pd.DataFrame(rows)

    # Aggregazione per via normalizzata
    def mode_or_none(series: pd.Series) -> Optional[Any]:
        vals = [v for v in series.dropna().tolist() if v != ""]
        if not vals:
            return None
        cnt = Counter(vals)
        return cnt.most_common(1)[0][0]

    grouped = (
        df.groupby("denominazi_norm", as_index=False)
        .agg(
            denominazi_canonical=("denominazi_raw", "first"),
            quartiere_geojson=("quartiere_geojson", mode_or_none),
            lunghezza_m_geo=("lunghezza", "sum"),
        )
        .copy()
    )

    grouped["lunghezza_m_geo"] = grouped["lunghezza_m_geo"].round(1)

    return grouped


def load_base_vie_csv() -> pd.DataFrame:
    """Carica il CSV base delle vie da processed o dal CSV originale."""
    # Preferisci processed se esiste (più aggiornato), altrimenti CSV grezzo
    if CSV_PROCESSED.exists():
        path = CSV_PROCESSED
    elif CSV_RAW.exists():
        path = CSV_RAW
    else:
        raise FileNotFoundError(
            f"Nessun CSV vie trovato. Attesi: {CSV_PROCESSED} o {CSV_RAW}"
        )

    try:
        df = pd.read_csv(path, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(path, encoding="latin-1")

    df.columns = [c.strip() for c in df.columns]

    if "Odonimo" not in df.columns:
        raise ValueError(f"Colonna 'Odonimo' mancante in {path}")

    # Colonne di lavoro per normalizzazione, come in integrate_stradario
    df["Odonimo_clean"] = df["Odonimo"].apply(
        lambda x: str(x).strip().split("(")[0].strip() if pd.notna(x) else ""
    )
    df["Odonimo_norm"] = df["Odonimo_clean"].apply(normalize_name)

    return df


def merge_geojson_into_vie(df_vie: pd.DataFrame, df_geo: pd.DataFrame) -> pd.DataFrame:
    """Integra le vie dal GeoJSON nel CSV esistente, aggiornando lunghezze e aggiungendo nuove vie."""
    # Join per aggiornare lunghezze dove mancano
    df_merge = df_vie.merge(
        df_geo[["denominazi_norm", "lunghezza_m_geo"]],
        left_on="Odonimo_norm",
        right_on="denominazi_norm",
        how="left",
    )

    # Colonna lunghezza_m potrebbe non esistere ancora
    if "lunghezza_m" not in df_merge.columns:
        df_merge["lunghezza_m"] = pd.NA

    def choose_length(row: pd.Series) -> Any:
        cur = row.get("lunghezza_m")
        geo = row.get("lunghezza_m_geo")
        if pd.notna(cur) and str(cur).strip() != "" and float(cur) > 0:
            return cur
        return geo

    df_merge["lunghezza_m"] = df_merge.apply(choose_length, axis=1)

    # Vie presenti solo nel GeoJSON
    odonimi_norm_set = set(df_vie["Odonimo_norm"].dropna().unique())
    df_geo_only = df_geo[~df_geo["denominazi_norm"].isin(odonimi_norm_set)].copy()

    if not df_geo_only.empty:
        base_cols = list(df_merge.columns)
        new_rows: List[Dict[str, Any]] = []

        for _, row in df_geo_only.iterrows():
            record: Dict[str, Any] = {c: pd.NA for c in base_cols}
            record["Odonimo"] = row["denominazi_canonical"]
            if "Quartiere (Località)" in record:
                record["Quartiere (Località)"] = row.get("quartiere_geojson")
            if "Ubicazione" in record:
                record["Ubicazione"] = ""
            record["Odonimo_clean"] = row["denominazi_canonical"]
            record["Odonimo_norm"] = row["denominazi_norm"]
            record["lunghezza_m"] = row["lunghezza_m_geo"]
            new_rows.append(record)

        df_new = pd.DataFrame(new_rows, columns=base_cols)
        df_all = pd.concat([df_merge, df_new], ignore_index=True)
    else:
        df_all = df_merge

    # Rimuovi colonne tecniche di lavoro dal CSV finale
    drop_cols = [c for c in ("Odonimo_clean", "Odonimo_norm", "denominazi_norm", "lunghezza_m_geo") if c in df_all.columns]
    df_all = df_all.drop(columns=drop_cols, errors="ignore")

    return df_all


def main() -> None:
    print("=== Costruzione vie complete da GeoJSON + CSV ===\n")
    print(f"GeoJSON: {GEOJSON_PATH}")
    print(f"CSV base (processed/raw): {CSV_PROCESSED} | {CSV_RAW}\n")

    df_geo = load_geojson_vie()
    print(f"Vie denominate uniche dal GeoJSON: {len(df_geo)}")

    df_vie = load_base_vie_csv()
    print(f"Vie uniche nel CSV base: {df_vie['Odonimo'].nunique()}")

    df_all = merge_geojson_into_vie(df_vie, df_geo)

    unique_csv_final = df_all["Odonimo"].nunique()
    print(f"Vie uniche nel CSV finale: {unique_csv_final}")

    # Salvataggio: processed + main
    CSV_PROCESSED.parent.mkdir(parents=True, exist_ok=True)
    df_all.to_csv(CSV_PROCESSED, index=False, encoding="utf-8")
    print(f"\nSalvataggio CSV completo → {CSV_PROCESSED}")

    df_all.to_csv(CSV_MAIN, index=False, encoding="utf-8")
    print(f"Salvataggio CSV principale → {CSV_MAIN}")

    # Piccola validazione copertura
    print("\n--- Validazione copertura (rapida) ---")
    denom_geo_set = set(df_geo["denominazi_norm"].unique())

    # Per il CSV finale, ricalcola Odonimo_norm con la stessa funzione
    df_tmp = df_all.copy()
    df_tmp["Odonimo_clean"] = df_tmp["Odonimo"].apply(
        lambda x: str(x).strip().split("(")[0].strip() if pd.notna(x) else ""
    )
    df_tmp["Odonimo_norm"] = df_tmp["Odonimo_clean"].apply(normalize_name)
    denom_csv_set = set(df_tmp["Odonimo_norm"].dropna().unique())

    missing_in_csv = sorted(denom_geo_set - denom_csv_set)
    print(f"Vie denominate GeoJSON (norm): {len(denom_geo_set)}")
    print(f"Vie nel CSV finale (norm):    {len(denom_csv_set)}")
    print(f"Vie GeoJSON non presenti nel CSV finale (norm): {len(missing_in_csv)}")
    if missing_in_csv:
        sample = missing_in_csv[:10]
        print("Esempi mancanti (max 10):")
        for name in sample:
            print(f"  - {name}")
    else:
        print("Copertura completa: tutte le vie denominate del GeoJSON sono nel CSV.")


if __name__ == "__main__":
    main()

