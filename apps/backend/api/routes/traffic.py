"""Endpoint per traffico baseline e simulazione evento."""

from fastapi import APIRouter

from models.schemas import SimulateDayRequest
from services.event_position import event_position_to_neighborhood
from services.exodus_curve import compute_exodus_curve
from services.gemini_traffic import get_event_traffic_multiplier
from services.traffic_processor import process_traffic_data

router = APIRouter(prefix="/api", tags=["traffic"])


@router.get("/baseline")
async def get_baseline(date: str):
    """Restituisce il traffico senza moltiplicatore evento (baseline) per confronto."""
    return process_traffic_data(date, multiplier=1.0)


@router.post("/simulate-day")
async def simulate_day(req: SimulateDayRequest):
    """
    Simula il traffico per una data con evento.
    Usa curva di esodo e moltiplicatore Gemini (o bypass con req.multiplier per test).
    Se event_venue o event_position sono forniti, applica decay spaziale (impatto maggiore vicino al luogo).
    """
    if req.multiplier is not None:
        base_multiplier = max(1.0, min(3.0, req.multiplier))
    else:
        base_multiplier = get_event_traffic_multiplier(
            req.event_name, req.capacity, req.vip_names
        )
    multipliers_by_hour = compute_exodus_curve(
        req.event_end_time,
        base_multiplier,
        hours=list(range(16, 24)),
    )
    event_neighborhood = event_position_to_neighborhood(
        req.event_position, req.event_venue
    )
    result = process_traffic_data(
        req.date,
        multipliers_by_hour=multipliers_by_hour,
        event_neighborhood=event_neighborhood,
    )
    return result
