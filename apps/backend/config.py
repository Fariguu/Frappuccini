"""
Configurazione centralizzata del backend.
Path, variabili d'ambiente e costanti condivise.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Root del monorepo (Frappuccini/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Root del backend
BACKEND_ROOT = Path(__file__).resolve().parent

# Path del dataset traffico (CSV simulato 2022-2025)
DATASET_CSV_PATH = PROJECT_ROOT / "dataset" / "output" / "bari_traffic_simulated_22_25.csv"

# Path del GeoJSON mappa stradale Bari
GEOJSON_PATH = BACKEND_ROOT / "data" / "strade_bari.geojson"

# Mappa livelli di congestione -> colore hex per il frontend
CONGESTION_COLOR_MAP = {
    "Critical": "#ff0000",
    "High": "#ffa500",
    "Normal": "#00ff00",
}

# Mapping GeoJSON quartiere_ (macro-area) -> quartieri CSV del dataset
GEOJSON_QUARTIERE_MAP: dict[str, list[str]] = {
    "BARI": [
        "S.Nicola", "Murat", "Madonnella", "Poggiofranco", "Carrassi",
        "Libertà", "LibertàPicone(Municipio 2)", "S. Pasquale", "Stanic", "Japigia",
    ],
    "TORRE A MARE": ["Torre A Mare", "Torre a Mare"],
    "CARBONARA": ["Carbonara"],
    "CEGLIE DEL CAMPO": ["Ceglie del Campo"],
    "LOSETO": ["Loseto"],
    "PALESE": ["Palese"],
    "SANTO SPIRITO": ["Santo Spirito"],
}

# Origini CORS consentite (frontend dev)
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


def get_google_api_key() -> str | None:
    """Restituisce GOOGLE_API_KEY dalle variabili d'ambiente."""
    return os.getenv("GOOGLE_API_KEY")
