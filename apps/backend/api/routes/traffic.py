"""Endpoint per traffico baseline, simulazione evento e chat IA."""

from datetime import date as date_type

from fastapi import APIRouter, HTTPException

from models.schemas import ChatRequest, SimulateDayRequest
from services.event_position import event_position_to_neighborhood
from services.exodus_curve import compute_exodus_curve
from services.gemini_traffic import chat_extract_event, get_event_traffic_multiplier
from services.traffic_processor import process_traffic_data

router = APIRouter(prefix="/api", tags=["traffic"])


def _parse_end_hour(event_end_time: str) -> int:
    try:
        return int(event_end_time.strip().split(":")[0])
    except (ValueError, IndexError):
        return 22


@router.get("/baseline")
async def get_baseline(date: str):
    """Restituisce il traffico senza moltiplicatore evento (baseline) per confronto."""
    return process_traffic_data(date, multiplier=1.0)


@router.post("/chat")
async def chat(req: ChatRequest):
    """
    Endpoint conversazionale: riceve i messaggi della chat e usa Gemini
    per estrarre parametri evento, analizzare impatto VIP e guidare l'utente.
    """
    if not req.messages:
        raise HTTPException(status_code=400, detail="Nessun messaggio fornito.")
    return chat_extract_event(req.messages)


@router.post("/simulate-day")
async def simulate_day(req: SimulateDayRequest):
    """
    Simula il traffico per una data futura con evento.
    Accetta un multiplier diretto (dal chat flow) oppure lo calcola via Gemini.
    Inietta anche volume di traffico aggiuntivo basato sulla capacità.
    """
    try:
        req_date = date_type.fromisoformat(req.date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato data non valido. Usare YYYY-MM-DD.")

    if req_date < date_type.today():
        raise HTTPException(
            status_code=400,
            detail="La simulazione è disponibile solo per date odierne o future.",
        )

    if req.multiplier is not None:
        base_multiplier = max(1.0, min(3.0, req.multiplier))
    else:
        base_multiplier = get_event_traffic_multiplier(
            req.event_name, req.capacity, req.vip_names
        )

    multipliers_by_hour = compute_exodus_curve(
        req.event_end_time,
        base_multiplier,
        hours=list(range(24)),
    )

    event_neighborhood = event_position_to_neighborhood(
        req.event_position, req.event_venue
    )

    end_hour = _parse_end_hour(req.event_end_time)

    result = process_traffic_data(
        req.date,
        multipliers_by_hour=multipliers_by_hour,
        event_neighborhood=event_neighborhood,
        event_capacity=req.capacity,
        event_end_hour=end_hour,
    )
    return result
