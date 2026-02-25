"""
Matching tra denominazi GeoJSON e street_name del dataset CSV.
Costruisce una lookup table cached: denominazi -> csv_street_name.
"""

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

import pandas as pd

from config import DATASET_CSV_PATH, GEOJSON_PATH

PREFIXES = (
    "via ", "corso ", "viale ", "piazza ", "largo ", "lungomare ", "lung.re ",
    "piazzale ", "sottovia ", "ponte ", "traversa ", "vico ", "giardino ",
    "piazzetta ", "strada ", "circonvallazione ", "raccordo ", "stradella ",
    "arco ", "contrada ", "chiasso ", "cala ", "corte ",
)

SUFFIXES_TO_STRIP = (" da bari", " di bari")


def _normalize(name: str) -> str:
    if not name:
        return ""
    s = str(name).strip().lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"\s+", " ", s)
    for p in PREFIXES:
        if s.startswith(p):
            s = s[len(p):].strip()
            break
    for sfx in SUFFIXES_TO_STRIP:
        if s.endswith(sfx):
            s = s[: -len(sfx)].strip()
    s = s.split("(")[0].strip()
    s = re.sub(r"[,;.']", "", s)
    return s


def _tokens(name: str) -> frozenset[str]:
    return frozenset(_normalize(name).split())


def _load_csv_street_names() -> set[str]:
    df = pd.read_csv(DATASET_CSV_PATH, usecols=["street_name"])
    return set(df["street_name"].dropna().unique())


def _load_geojson_denominazi() -> set[str]:
    with open(GEOJSON_PATH, encoding="utf-8") as f:
        gj = json.load(f)
    out: set[str] = set()
    for feat in gj["features"]:
        d = feat.get("properties", {}).get("denominazi", "")
        if d:
            out.add(d)
    return out


@lru_cache(maxsize=1)
def build_street_mapping() -> dict[str, str]:
    """
    Restituisce dict[denominazi_geojson -> csv_street_name].
    Strategia (in ordine di priorità):
      1. Match esatto case-insensitive
      2. Match per nome normalizzato (strip prefissi/suffissi)
      3. Match per token-set (tutti i token del nome più corto
         presenti nel più lungo)
    """
    csv_names = _load_csv_street_names()
    geojson_denoms = _load_geojson_denominazi()

    csv_upper = {n.strip().upper(): n for n in csv_names}
    csv_norm = {}
    csv_tokens: dict[frozenset[str], str] = {}
    for n in csv_names:
        norm = _normalize(n)
        if norm:
            csv_norm[norm] = n
            csv_tokens[_tokens(n)] = n

    mapping: dict[str, str] = {}

    for denom in geojson_denoms:
        d_upper = denom.strip().upper()
        if d_upper in csv_upper:
            mapping[denom] = csv_upper[d_upper]
            continue

        d_norm = _normalize(denom)
        if d_norm in csv_norm:
            mapping[denom] = csv_norm[d_norm]
            continue

        d_toks = _tokens(denom)
        if not d_toks:
            continue

        best_match: str | None = None
        best_score = 0
        for c_toks, c_name in csv_tokens.items():
            if not c_toks:
                continue
            smaller, larger = (d_toks, c_toks) if len(d_toks) <= len(c_toks) else (c_toks, d_toks)
            if smaller <= larger:
                score = len(smaller)
                if score > best_score:
                    best_score = score
                    best_match = c_name
        if best_match is not None:
            mapping[denom] = best_match

    return mapping
