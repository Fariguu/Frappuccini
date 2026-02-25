"""Endpoint per la mappa stradale GeoJSON."""

import json
from functools import lru_cache

import geopandas as gpd
from fastapi import APIRouter, HTTPException

from config import GEOJSON_PATH
from services.street_matching import build_street_mapping

router = APIRouter(prefix="/api", tags=["map"])


@lru_cache(maxsize=1)
def _build_enriched_geojson() -> dict:
    """Carica il GeoJSON, lo riproietta in WGS84 e aggiunge street_name da CSV matching."""
    gdf = gpd.read_file(GEOJSON_PATH)
    if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)
    geojson = json.loads(gdf.to_json())

    mapping = build_street_mapping()
    for feature in geojson.get("features", []):
        denom = feature.get("properties", {}).get("denominazi", "")
        feature["properties"]["street_name"] = mapping.get(denom)

    return geojson


@router.get("/map")
async def get_map():
    """Restituisce il GeoJSON arricchito con street_name per matching traffico."""
    if not GEOJSON_PATH.exists():
        raise HTTPException(status_code=500, detail="File mappa non trovato")
    return _build_enriched_geojson()
