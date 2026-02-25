"""
Schemi Pydantic per le richieste e risposte API.
"""

from pydantic import BaseModel, model_validator


class EventPosition(BaseModel):
    """Posizione evento: coordinate WGS84 o nome quartiere."""

    lat: float | None = None
    lng: float | None = None
    neighborhood: str | None = None  # es. "S.Nicola", "Poggiofranco"

    @model_validator(mode="after")
    def check_at_least_one(self):
        if self.lat is None and self.lng is None and self.neighborhood is None:
            return self
        if self.neighborhood is not None:
            return self
        if self.lat is not None and self.lng is not None:
            return self
        raise ValueError("Fornire (lat, lng) oppure neighborhood")


class SimulateDayRequest(BaseModel):
    """
    Richiesta di simulazione traffico per una data con evento.

    Attributes:
        event_name: Nome dell'evento (es. "Concerto Stadio San Nicola").
        capacity: Capacità massima in persone.
        vip_names: Lista nomi ospiti VIP che influenzano l'impatto.
        date: Data in formato YYYY-MM-DD.
        event_end_time: Orario fine evento (es. "22:00"); l'esodo si concentra
            nelle ore successive (50% ora fine, 30% ora+1, 20% ora-1).
        event_position: Posizione evento (coordinate o quartiere).
        event_venue: Nome luogo per geocoding (es. "Stadio San Nicola, Bari").
        multiplier: Opzionale; se fornito bypassa Gemini (utile per test).
    """

    event_name: str
    capacity: int
    vip_names: list[str]
    date: str  # YYYY-MM-DD
    event_end_time: str = "22:00"  # Orario fine evento (esodo nelle ore successive)
    event_position: EventPosition | None = None
    event_venue: str | None = None  # Nome luogo per geocoding (Nominatim)
    multiplier: float | None = None  # Opzionale: bypassa Gemini per test
