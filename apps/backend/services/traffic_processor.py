"""
Elaborazione dati traffico: caricamento CSV, applicazione moltiplicatori,
iniezione volume evento basata su capacità, livelli congestione.
"""

import json
from datetime import date as date_type, timedelta
from pathlib import Path

import pandas as pd
from fastapi import HTTPException

from config import CONGESTION_COLOR_MAP, DATASET_CSV_PATH, GEOJSON_QUARTIERE_MAP
from services.event_position import get_decay_factor
from services.exodus_curve import get_time_fractions

_COLOR_PRIORITY = {"#ff0000": 3, "#ffa500": 2, "#00ff00": 1}

_df_cache: pd.DataFrame | None = None


def _load_dataset() -> pd.DataFrame:
    global _df_cache
    if _df_cache is None:
        _df_cache = pd.read_csv(DATASET_CSV_PATH, parse_dates=["timestamp"])
    return _df_cache

CROWD_THRESHOLD = 1
PEOPLE_TO_TRAFFIC_FACTOR = 2.0


def _find_equivalent_date(target_date: date_type) -> date_type:
    """
    Mappa una data (tipicamente futura) a un giorno equivalente nel dataset
    (Gennaio 2022), mantenendo lo stesso giorno della settimana.
    """
    target_dow = target_date.weekday()
    base = date_type(2022, 1, 1)
    for i in range(31):
        candidate = base + timedelta(days=i)
        if candidate.weekday() == target_dow:
            return candidate
    return base


_CONGESTION_THRESHOLDS: dict[str, tuple[float, float]] = {
    "Highway": (5000, 7000),
    "Main Road": (2000, 2800),
    "Local Road": (1000, 1400),
}


def _compute_congestion_level(volume: float, road_type: str = "Local Road") -> str:
    high_thresh, crit_thresh = _CONGESTION_THRESHOLDS.get(
        road_type, _CONGESTION_THRESHOLDS["Local Road"]
    )
    if volume > crit_thresh:
        return "Critical"
    if volume > high_thresh:
        return "High"
    return "Normal"


def _inject_event_crowd_volume(
    df: pd.DataFrame,
    capacity: int,
    event_neighborhood: str,
    end_hour: int,
    duration: int = 3,
) -> None:
    """
    Inietta volume di traffico aggiuntivo sulle strade basato sulla
    capacità dell'evento.  Le persone vengono distribuite nel tempo
    (arrivo + esodo) e nello spazio (decay per quartiere).

    Se una strada riceve >= CROWD_THRESHOLD persone aggiuntive dall'evento
    l'iniezione viene applicata garantendo un impatto visibile.
    """
    start_hour = end_hour - duration
    time_frac_map = get_time_fractions(start_hour, end_hour)
    df["_time_frac"] = df["hour"].map(time_frac_map).fillna(0.0)

    neighborhoods = df["neighborhood"].unique()
    decay_map = {
        nb: get_decay_factor(str(nb), event_neighborhood) for nb in neighborhoods
    }
    df["_decay"] = df["neighborhood"].map(decay_map).fillna(0.15)

    streets_per_nb = df.groupby("neighborhood")["street_name"].transform("nunique")
    streets_per_nb = streets_per_nb.clip(lower=1)

    df["_additional"] = (
        capacity * PEOPLE_TO_TRAFFIC_FACTOR * df["_time_frac"] * df["_decay"]
    ) / streets_per_nb

    mask = df["_additional"] >= CROWD_THRESHOLD
    df.loc[mask, "traffic_volume"] += df.loc[mask, "_additional"]

    if mask.any():
        for rt in (
            df.loc[mask, "road_type"].unique() if "road_type" in df.columns else ["Local Road"]
        ):
            rt_mask = mask & (df.get("road_type", "Local Road") == rt)
            high_thresh = _CONGESTION_THRESHOLDS.get(rt, _CONGESTION_THRESHOLDS["Local Road"])[0]
            df.loc[rt_mask, "traffic_volume"] = df.loc[rt_mask, "traffic_volume"].clip(
                lower=high_thresh
            )

    df.drop(columns=["_time_frac", "_decay", "_additional"], inplace=True)


def _build_quartiere_colors(
    result_by_neighborhood: dict[str, dict[str, str]],
) -> dict[str, dict[str, str]]:
    """
    Mappa i colori dei quartieri CSV alle macro-aree del GeoJSON (quartiere_).
    Usa la media dei livelli di congestione tra i quartieri costituenti
    per evitare che un singolo quartiere critico colori tutta la macro-area.
    """
    color_to_score = {"#00ff00": 1, "#ffa500": 2, "#ff0000": 3}
    result: dict[str, dict[str, str]] = {}
    for time_str, nb_colors in result_by_neighborhood.items():
        q_colors: dict[str, str] = {}
        for quartiere, csv_neighborhoods in GEOJSON_QUARTIERE_MAP.items():
            scores: list[int] = []
            for nb in csv_neighborhoods:
                color = nb_colors.get(nb)
                if color is not None:
                    scores.append(color_to_score.get(color, 1))
            if not scores:
                continue
            scores.sort(reverse=True)
            top_score = scores[0]
            avg = sum(scores) / len(scores)
            if top_score == 3 and avg >= 1.8:
                q_colors[quartiere] = "#ff0000"
            elif top_score >= 2 or avg >= 1.2:
                q_colors[quartiere] = "#ffa500"
            else:
                q_colors[quartiere] = "#00ff00"
        result[time_str] = q_colors
    return result


def process_traffic_data(
    date: str,
    multiplier: float | None = None,
    multipliers_by_hour: dict[str, float] | None = None,
    event_neighborhood: str | None = None,
    event_capacity: int | None = None,
    event_end_hour: int | None = None,
) -> dict:
    """
    Carica il dataset, applica moltiplicatori per ora o globali,
    inietta volume aggiuntivo basato sulla capacità dell'evento,
    calcola livelli di congestione e restituisce i dati per fasce orarie.
    """
    if not DATASET_CSV_PATH.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Dataset non trovato: {DATASET_CSV_PATH}",
        )

    df = _load_dataset()
    df["date"] = df["timestamp"].dt.date
    df["hour"] = df["timestamp"].dt.hour
    df["time_str"] = df["timestamp"].dt.strftime("%H:%M")

    target_date = pd.to_datetime(date).date()
    df_filtered = df[df["date"] == target_date]

    if df_filtered.empty:
        equiv = _find_equivalent_date(target_date)
        df_filtered = df[df["date"] == equiv]

    if df_filtered.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Nessun dato equivalente trovato per la data {date}.",
        )

    df_filtered = df_filtered.copy()
    # #region agent log
    _log = Path("/Users/flaviodemusso/Desktop/Frappuccini/.cursor/debug.log")
    try:
        _h1 = sorted(multipliers_by_hour.keys()) if multipliers_by_hour else []
        _ts_sample = df_filtered["time_str"].dropna().unique()[:5].tolist()
        with _log.open("a", encoding="utf-8") as _f:
            _f.write(json.dumps({"hypothesisId":"A","message":"multipliers vs time_str sample","data":{"multiplier_keys":_h1,"time_str_sample":_ts_sample,"event_end_hour":event_end_hour}})+"\n")
    except Exception:
        pass
    # #endregion
    if multipliers_by_hour:
        df_filtered["traffic_volume_multiplier"] = df_filtered["time_str"].map(
            multipliers_by_hour
        )
        # #region agent log
        try:
            _nan_count = df_filtered["traffic_volume_multiplier"].isna().sum()
            with _log.open("a", encoding="utf-8") as _f:
                _f.write(json.dumps({"hypothesisId":"B","message":"NaN after map","data":{"nan_count":int(_nan_count),"total_rows":len(df_filtered)}})+"\n")
        except Exception:
            pass
        # #endregion
        df_filtered["traffic_volume_multiplier"] = df_filtered[
            "traffic_volume_multiplier"
        ].fillna(1.0)

        if event_neighborhood and "neighborhood" in df_filtered.columns:
            def apply_decay(row: pd.Series) -> float:
                hour_mult = row["traffic_volume_multiplier"]
                decay = get_decay_factor(
                    str(row.get("neighborhood", "")),
                    event_neighborhood,
                )
                decay_effective = max(decay, 0.25)
                return 1.0 + (hour_mult - 1.0) * decay_effective

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

    if (
        event_capacity
        and event_capacity > 0
        and event_neighborhood
        and event_end_hour is not None
    ):
        _inject_event_crowd_volume(
            df_filtered, event_capacity, event_neighborhood, event_end_hour
        )

    df_filtered["congestion_level"] = df_filtered.apply(
        lambda r: _compute_congestion_level(r["traffic_volume"], r.get("road_type", "Local Road")),
        axis=1,
    )

    group_cols = ["time_str", "street_name", "neighborhood"]
    if "road_type" in df_filtered.columns:
        group_cols.append("road_type")
    df_agg = (
        df_filtered.groupby(group_cols, as_index=False)
        .agg({"traffic_volume": "mean"})
        .copy()
    )
    if "road_type" not in df_agg.columns:
        df_agg["road_type"] = "Local Road"
    df_agg["congestion_level"] = df_agg.apply(
        lambda r: _compute_congestion_level(r["traffic_volume"], r["road_type"]),
        axis=1,
    )

    result_by_street: dict[str, dict[str, str]] = {}
    result_by_neighborhood: dict[str, dict[str, str]] = {}
    crit_order = {"Critical": 3, "High": 2, "Normal": 1}

    for time_str in sorted(df_agg["time_str"].unique()):
        subset = df_agg[df_agg["time_str"] == time_str]
        result_by_street[time_str] = {
            row["street_name"]: CONGESTION_COLOR_MAP[row["congestion_level"]]
            for _, row in subset.iterrows()
        }
        nb_best: dict[str, str] = {}
        for _, row in subset.iterrows():
            nb = str(row.get("neighborhood", "")).strip()
            if not nb:
                continue
            lvl = row["congestion_level"]
            if nb not in nb_best or crit_order.get(lvl, 0) > crit_order.get(
                nb_best[nb], 0
            ):
                nb_best[nb] = lvl
        result_by_neighborhood[time_str] = {
            nb: CONGESTION_COLOR_MAP[lvl] for nb, lvl in nb_best.items()
        }

    result_by_quartiere = _build_quartiere_colors(result_by_neighborhood)

    # #region agent log
    try:
        _hours_out = sorted(df_agg["time_str"].unique())
        _first_5 = _hours_out[:5]
        _has_00 = "00:00" in _hours_out
        _by_street_first = len(result_by_street.get(_first_5[0] if _first_5 else "", {})) if _first_5 else 0
        with _log.open("a", encoding="utf-8") as _f:
            _f.write(json.dumps({"hypothesisId":"C","message":"output hours and by_street","data":{"hours_count":len(_hours_out),"first_5":_first_5,"has_00":_has_00,"by_street_first_len":_by_street_first}})+"\n")
    except Exception:
        pass
    # #endregion

    return {
        "hours": sorted(df_agg["time_str"].unique()),
        "by_street": result_by_street,
        "by_neighborhood": result_by_neighborhood,
        "by_quartiere": result_by_quartiere,
    }
