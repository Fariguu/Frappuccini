"""
Elaborazione dati traffico: caricamento CSV, applicazione moltiplicatori, livelli congestione.
"""

import pandas as pd
from fastapi import HTTPException

from config import CONGESTION_COLOR_MAP, DATASET_CSV_PATH
from services.event_position import get_decay_factor


def _compute_congestion_level(volume: float) -> str:
    """
    Mappa traffic_volume in Critical/High/Normal secondo soglie.
    Soglie: >2000 Critical, >1500 High, altrimenti Normal.
    """
    if volume > 2000:
        return "Critical"
    if volume > 1500:
        return "High"
    return "Normal"


def process_traffic_data(
    date: str,
    multiplier: float | None = None,
    multipliers_by_hour: dict[str, float] | None = None,
    event_neighborhood: str | None = None,
) -> dict:
    """
    Carica il dataset, applica moltiplicatori per ora o globali,
    calcola livelli di congestione e restituisce {time_str: {street_name: color}}.
    Se event_neighborhood è fornito, applica decay spaziale (impatto maggiore vicino all'evento).
    """
    if not DATASET_CSV_PATH.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Dataset non trovato: {DATASET_CSV_PATH}",
        )

    df = pd.read_csv(DATASET_CSV_PATH, parse_dates=["timestamp"])
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
        df_filtered["traffic_volume_multiplier"] = df_filtered["time_str"].map(
            multipliers_by_hour
        )
        df_filtered["traffic_volume_multiplier"] = df_filtered[
            "traffic_volume_multiplier"
        ].fillna(1.0)

        if event_neighborhood and "neighborhood" in df_filtered.columns:
            # Decay spaziale: impatto attenuato per strade lontane dall'evento
            def apply_decay(row: pd.Series) -> float:
                hour_mult = row["traffic_volume_multiplier"]
                decay = get_decay_factor(
                    str(row.get("neighborhood", "")),
                    event_neighborhood,
                )
                return 1.0 + (hour_mult - 1.0) * decay

            df_filtered["effective_multiplier"] = df_filtered.apply(apply_decay, axis=1)
            df_filtered["traffic_volume"] = (
                df_filtered["traffic_volume"] * df_filtered["effective_multiplier"]
            )
        else:
            df_filtered["traffic_volume"] = (
                df_filtered["traffic_volume"] * df_filtered["traffic_volume_multiplier"]
            )
    else:
        traffic_volume_multiplier = multiplier if multiplier is not None else 1.0
        df_filtered["traffic_volume"] = (
            df_filtered["traffic_volume"] * traffic_volume_multiplier
        )

    df_filtered["congestion_level"] = df_filtered["traffic_volume"].apply(
        _compute_congestion_level
    )

    df_agg = (
        df_filtered.groupby(["time_str", "street_name"], as_index=False)
        .agg({"traffic_volume": "mean"})
        .copy()
    )
    df_agg["congestion_level"] = df_agg["traffic_volume"].apply(
        _compute_congestion_level
    )

    result = {}
    for time_str in sorted(df_agg["time_str"].unique()):
        subset = df_agg[df_agg["time_str"] == time_str]
        result[time_str] = {
            row["street_name"]: CONGESTION_COLOR_MAP[row["congestion_level"]]
            for _, row in subset.iterrows()
        }

    return result
