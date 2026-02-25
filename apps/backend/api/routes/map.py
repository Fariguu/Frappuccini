"""Endpoint per la mappa stradale GeoJSON."""

import json

from fastapi import APIRouter, HTTPException

from config import GEOJSON_PATH

router = APIRouter(prefix="/api", tags=["map"])


@router.get("/map")
async def get_map():
    """Restituisce il GeoJSON della mappa stradale di Bari per il frontend."""
    if not GEOJSON_PATH.exists():
        raise HTTPException(status_code=500, detail="File mappa non trovato")
    with open(GEOJSON_PATH, encoding="utf-8") as f:
        return json.load(f)
