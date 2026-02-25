"""Endpoint per la mappa stradale GeoJSON."""

import json

import geopandas as gpd
from fastapi import APIRouter, HTTPException

from config import GEOJSON_PATH

router = APIRouter(prefix="/api", tags=["map"])


@router.get("/map")
async def get_map():
    """Restituisce il GeoJSON della mappa stradale di Bari per il frontend (WGS84)."""
    if not GEOJSON_PATH.exists():
        raise HTTPException(status_code=500, detail="File mappa non trovato")
    gdf = gpd.read_file(GEOJSON_PATH)
    if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)
    return json.loads(gdf.to_json())
