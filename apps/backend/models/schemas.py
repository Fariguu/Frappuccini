"""
Schemi Pydantic per le richieste e risposte API.
"""

from pydantic import BaseModel, model_validator


class EventPosition(BaseModel):
    """Posizione evento: coordinate WGS84 o nome quartiere."""

    lat: float | None = None
    lng: float | None = None
    neighborhood: str | None = None

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
    event_name: str
    capacity: int
    vip_names: list[str]
    date: str
    event_end_time: str = "22:00"
    event_position: EventPosition | None = None
    event_venue: str | None = None
    multiplier: float | None = None


# --------------- Chat models ---------------

class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]


class ExtractedParams(BaseModel):
    event_name: str | None = None
    venue: str | None = None
    date: str | None = None
    end_time: str | None = None
    capacity: int | None = None
    vip_names: list[str] = []
    vip_analysis: str | None = None
    estimated_multiplier: float | None = None
    confidence: str | None = None


class ChatResponse(BaseModel):
    reply: str
    extracted_params: ExtractedParams
    ready_to_simulate: bool
    missing_info: list[str] = []
