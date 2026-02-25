"""
Geocoding via Nominatim (OpenStreetMap).
Converte nome luogo -> (lat, lng) senza API key.
Rate limit: 1 richiesta/secondo. User-Agent obbligatorio.
"""

import json
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "Frappuccini-Backend/1.0"

_geocode_cache: dict[str, tuple[float, float]] = {}
_last_request_time: float = 0.0


def geocode_place(query: str) -> tuple[float, float] | None:
    """
    Chiama Nominatim per geocoding. Restituisce (lat, lng) del primo risultato.
    Aggiunge ", Bari, Italy" per disambiguare.
    Usa cache in-memory. Rispetta rate limit 1 req/s.
    """
    if not query or not query.strip():
        return None

    q = query.strip()
    cache_key = q.lower()
    if cache_key in _geocode_cache:
        return _geocode_cache[cache_key]

    # Rate limit: 1 req/s
    global _last_request_time
    elapsed = time.monotonic() - _last_request_time
    if elapsed < 1.0:
        time.sleep(1.0 - elapsed)
    _last_request_time = time.monotonic()

    search_query = f"{q}, Bari, Italy" if "bari" not in q.lower() else q
    url = f"{NOMINATIM_URL}?q={quote(search_query)}&format=json&limit=1"

    req = Request(url, method="GET", headers={"User-Agent": USER_AGENT})

    try:
        with urlopen(req, timeout=10) as resp:
            data = json.load(resp)
    except (URLError, HTTPError, TimeoutError, ValueError):
        return None

    if not data or not isinstance(data, list):
        return None

    first = data[0]
    if not isinstance(first, dict):
        return None

    lat = first.get("lat")
    lon = first.get("lon")
    if lat is None or lon is None:
        return None

    try:
        lat_f = float(lat)
        lon_f = float(lon)
    except (TypeError, ValueError):
        return None

    result = (lat_f, lon_f)
    _geocode_cache[cache_key] = result
    return result
