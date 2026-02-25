"""
Mapping posizione evento -> quartiere e decay factor per strada.
"""

import json
from pathlib import Path

from models.schemas import EventPosition
from services.geocoding import geocode_place

BACKEND_ROOT = Path(__file__).resolve().parent.parent
BBOX_PATH = BACKEND_ROOT / "data" / "neighborhoods_bbox.json"

# Normalizza varianti di nome quartiere per confronto
NEIGHBORHOOD_NORMALIZE = {
    "torre a mare": "Torre A Mare",
    "torre a mare ": "Torre A Mare",
    "ceglie del campo": "Ceglie del Campo",
    "s.nicola": "S.Nicola",
    "s. nicola": "S.Nicola",
    "s. pasquale": "S. Pasquale",
}

# Quartieri vicini (tier 1) e medi (tier 2) per decay
NEIGHBORHOOD_PROXIMITY: dict[str, tuple[list[str], list[str]]] = {
    "S.Nicola": (["Murat", "Madonnella"], ["Libertà", "Poggiofranco", "Carrassi"]),
    "Murat": (["S.Nicola", "Madonnella"], ["Libertà", "Poggiofranco"]),
    "Madonnella": (["S.Nicola", "Murat"], ["Libertà", "Japigia"]),
    "Poggiofranco": (["Carrassi", "Libertà"], ["S.Nicola", "Murat", "S. Pasquale"]),
    "Carrassi": (["Poggiofranco", "Stanic"], ["S.Nicola", "Ceglie del Campo"]),
    "Libertà": (["Murat", "Poggiofranco", "S. Pasquale"], ["Madonnella", "Japigia"]),
    "Japigia": (["Madonnella", "Carbonara"], ["Libertà", "Loseto"]),
    "Stanic": (["Carrassi", "Ceglie del Campo"], ["Poggiofranco", "Loseto"]),
    "Torre A Mare": (["Japigia"], ["Carbonara", "Libertà"]),
    "Ceglie del Campo": (["Stanic", "Loseto"], ["Carrassi", "Carbonara"]),
    "Loseto": (["Ceglie del Campo", "Carbonara"], ["Stanic", "Japigia"]),
    "Palese": (["S. Pasquale", "Santo Spirito"], ["Libertà", "Poggiofranco"]),
    "Santo Spirito": (["Palese", "S. Pasquale"], ["Libertà"]),
    "Carbonara": (["Japigia", "Loseto"], ["Stanic", "Ceglie del Campo"]),
    "S. Pasquale": (["Libertà", "Palese"], ["Poggiofranco", "Santo Spirito"]),
}


def _load_bbox() -> dict[str, list[float]]:
    """Carica bbox da JSON. Formato: [min_lng, min_lat, max_lng, max_lat]."""
    if not BBOX_PATH.exists():
        return {}
    try:
        with open(BBOX_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _normalize_neighborhood(name: str) -> str:
    """Normalizza nome quartiere per confronto."""
    if not name:
        return ""
    n = str(name).strip()
    return NEIGHBORHOOD_NORMALIZE.get(n.lower(), n)


def point_in_neighborhood(lng: float, lat: float) -> str | None:
    """
    Restituisce il quartiere contenente il punto (lng, lat) WGS84.
    Ritorna None se il punto non cade in nessun bbox noto.
    """
    bbox = _load_bbox()
    for neighborhood, coords in bbox.items():
        if len(coords) != 4:
            continue
        min_lng, min_lat, max_lng, max_lat = coords
        if min_lng <= lng <= max_lng and min_lat <= lat <= max_lat:
            return neighborhood
    return None


def event_position_to_neighborhood(
    position: EventPosition | None, venue: str | None
) -> str | None:
    """
    Estrae il quartiere dell'evento da event_position o event_venue.
    Priorità: venue (Nominatim) > position.neighborhood > position.lat/lng.
    """
    if venue and venue.strip():
        coords = geocode_place(venue.strip())
        if coords:
            lat, lng = coords
            return point_in_neighborhood(lng, lat)

    if position is None:
        return None

    if position.neighborhood:
        return _normalize_neighborhood(position.neighborhood) or position.neighborhood

    if position.lat is not None and position.lng is not None:
        return point_in_neighborhood(position.lng, position.lat)

    return None


def _extract_base_neighborhood(name: str) -> str:
    """Estrae quartiere base da nomi composti (es. 'LibertàPicone(Municipio 2)' -> 'Libertà')."""
    n = str(name).strip()
    for base in [
        "Libertà", "S.Nicola", "Murat", "Madonnella", "Poggiofranco", "Carrassi",
        "Japigia", "Stanic", "Torre A Mare", "Ceglie del Campo", "Loseto",
        "Palese", "Santo Spirito", "Carbonara", "S. Pasquale",
    ]:
        if base.lower() in n.lower():
            return base
    return _normalize_neighborhood(n) or n


def get_decay_factor(street_neighborhood: str, event_neighborhood: str) -> float:
    """
    Restituisce fattore di decay (0.15-1.0) in base alla vicinanza.
    - stesso quartiere: 1.0
    - quartiere vicino (tier 1): 0.6
    - quartiere medio (tier 2): 0.3
    - altro: 0.15
    """
    street_n = _extract_base_neighborhood(street_neighborhood)
    event_n = _normalize_neighborhood(event_neighborhood)

    if not street_n or not event_n:
        return 0.15

    if street_n == event_n:
        return 1.0

    proximity = NEIGHBORHOOD_PROXIMITY.get(event_n)
    if not proximity:
        return 0.15

    tier1, tier2 = proximity
    if street_n in tier1:
        return 0.6
    if street_n in tier2:
        return 0.3
    return 0.15
