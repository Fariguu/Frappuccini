import json
import os
import re
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

COLOR_MAP = {
    "Critical": "#ff0000",
    "High": "#ffa500",
    "Normal": "#00ff00",
}

# Cache moltiplicatore: calcolato una sola volta per (event_name, capacity, vip_names)
_multiplier_cache: dict[tuple, float] = {}


class SimulateDayRequest(BaseModel):
    event_name: str
    capacity: int
    vip_names: list[str]
    date: str  # YYYY-MM-DD
    event_end_time: str = "22:00"  # Orario fine evento (esodo nelle ore successive)
    event_location: str | None = None  # Placeholder per futura integrazione geografica
    multiplier: float | None = None  # Opzionale: bypassa Gemini per test


def get_traffic_multiplier(event_name: str, capacity: int, vip_names: list[str]) -> float:
    cache_key = (event_name, capacity, tuple(sorted(vip_names)))
    if cache_key in _multiplier_cache:
        return _multiplier_cache[cache_key]

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GOOGLE_API_KEY non configurata. Imposta la variabile d'ambiente.",
        )

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")

    prompt = (
        f"Valuta l'impatto sul traffico di questo evento a Bari: {event_name} "
        f"con {capacity} persone e ospiti {vip_names}. "
        "Restituisci SOLO un numero float da 1.0 (impatto nullo) a 3.0 (paralisi totale della città)."
    )

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        match = re.search(r"(\d+\.?\d*)", text)
        if match:
            value = float(match.group(1))
            multiplier = max(1.0, min(3.0, value))
        else:
            multiplier = 1.0
        _multiplier_cache[cache_key] = multiplier
        return multiplier
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Errore chiamata Gemini: {str(e)}. Verifica GOOGLE_API_KEY.",
        )


def compute_exodus_curve(
    event_end_time: str,
    base_multiplier: float,
    hours: list[int],
) -> dict[str, float]:
    """
    Calcola il moltiplicatore per ora in base alla curva di esodo.
    Picco: 50% in ora fine, 30% in ora+1, 20% nell'ora prima.
    """
    try:
        parts = event_end_time.strip().split(":")
        end_hour = int(parts[0]) if parts else 22
    except (ValueError, IndexError):
        end_hour = 22

    extra = base_multiplier - 1.0
    hour_set = set(hours)
    result = {}
    for h in hours:
        if h < end_hour - 1:
            result[f"{h:02d}:00"] = 1.0
        elif h == end_hour - 1:
            result[f"{h:02d}:00"] = 1.0 + 0.2 * extra
        elif h == end_hour:
            # Se non c'è ora+1 nel range, concentra 50%+30% nell'ora fine
            if (end_hour + 1) in hour_set:
                result[f"{h:02d}:00"] = 1.0 + 0.5 * extra
            else:
                result[f"{h:02d}:00"] = 1.0 + 0.8 * extra
        elif h == end_hour + 1:
            result[f"{h:02d}:00"] = 1.0 + 0.3 * extra
        else:
            result[f"{h:02d}:00"] = 1.0
    return result


def process_traffic_data(
    date: str,
    multiplier: float | None = None,
    multipliers_by_hour: dict[str, float] | None = None,
) -> dict:
    dataset_path = (
        Path(__file__).resolve().parent.parent.parent
        / "dataset"
        / "output"
        / "bari_traffic_simulated_22_25.csv"
    )

    if not dataset_path.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Dataset non trovato: {dataset_path}",
        )

    df = pd.read_csv(dataset_path, parse_dates=["timestamp"])
    df["date"] = df["timestamp"].dt.date
    df["hour"] = df["timestamp"].dt.hour
    df["time_str"] = df["timestamp"].dt.strftime("%H:%M")

    target_date = pd.to_datetime(date).date()
    df_filtered = df[
        (df["date"] == target_date) & (df["hour"] >= 16) & (df["hour"] <= 23)
    ]

    if df_filtered.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Nessun dato trovato per la data {date}. Il dataset copre 2022-2025.",
        )

    df_filtered = df_filtered.copy()
    if multipliers_by_hour:
        df_filtered["mult"] = df_filtered["time_str"].map(multipliers_by_hour)
        df_filtered["mult"] = df_filtered["mult"].fillna(1.0)
        df_filtered["traffic_volume"] = df_filtered["traffic_volume"] * df_filtered["mult"]
    else:
        mult = multiplier if multiplier is not None else 1.0
        df_filtered["traffic_volume"] = df_filtered["traffic_volume"] * mult

    def recalc_congestion(volume: float) -> str:
        if volume > 2000:
            return "Critical"
        if volume > 1500:
            return "High"
        return "Normal"

    df_filtered["congestion_level"] = df_filtered["traffic_volume"].apply(
        recalc_congestion
    )

    df_agg = (
        df_filtered.groupby(["time_str", "street_name"], as_index=False)
        .agg({"traffic_volume": "mean"})
        .copy()
    )
    df_agg["congestion_level"] = df_agg["traffic_volume"].apply(recalc_congestion)

    result = {}
    for time_str in sorted(df_agg["time_str"].unique()):
        subset = df_agg[df_agg["time_str"] == time_str]
        result[time_str] = {
            row["street_name"]: COLOR_MAP[row["congestion_level"]]
            for _, row in subset.iterrows()
        }

    return result


@app.get("/api")
async def root():
    return {"message": "Hello from FastAPI"}


@app.get("/api/hello")
async def hello():
    return {"message": "Hello from the backend!"}


@app.get("/api/map")
async def get_map():
    """Restituisce il GeoJSON della mappa stradale di Bari per il frontend."""
    geojson_path = Path(__file__).resolve().parent / "strade_bari.geojson"
    if not geojson_path.exists():
        raise HTTPException(status_code=500, detail="File mappa non trovato")
    with open(geojson_path, encoding="utf-8") as f:
        return json.load(f)


@app.get("/api/baseline")
async def get_baseline(date: str):
    """Restituisce il traffico senza moltiplicatore evento (baseline) per confronto."""
    return process_traffic_data(date, multiplier=1.0)


@app.post("/api/simulate-day")
async def simulate_day(req: SimulateDayRequest):
    if req.multiplier is not None:
        base_multiplier = max(1.0, min(3.0, req.multiplier))
    else:
        base_multiplier = get_traffic_multiplier(
            req.event_name, req.capacity, req.vip_names
        )
    # Curva di esodo: picco nelle ore successive a event_end_time
    multipliers_by_hour = compute_exodus_curve(
        req.event_end_time,
        base_multiplier,
        hours=list(range(16, 24)),
    )
    result = process_traffic_data(
        req.date,
        multipliers_by_hour=multipliers_by_hour,
    )
    return result
