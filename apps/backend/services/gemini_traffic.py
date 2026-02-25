"""
Servizio per stimare l'impatto sul traffico di un evento usando Gemini.
"""

import re

import google.generativeai as genai
from fastapi import HTTPException

from config import get_google_api_key

# Cache: calcolato una sola volta per (event_name, capacity, vip_names)
_gemini_multiplier_cache: dict[tuple, float] = {}


def get_event_traffic_multiplier(
    event_name: str, capacity: int, vip_names: list[str]
) -> float:
    """
    Stima l'impatto sul traffico di un evento usando Gemini.
    Ritorna un moltiplicatore tra 1.0 (impatto nullo) e 3.0 (paralisi totale).
    Usa cache per (event_name, capacity, vip_names) per evitare chiamate ripetute.
    """
    cache_key = (event_name, capacity, tuple(sorted(vip_names)))
    if cache_key in _gemini_multiplier_cache:
        return _gemini_multiplier_cache[cache_key]

    api_key = get_google_api_key()
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
        _gemini_multiplier_cache[cache_key] = multiplier
        return multiplier
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Errore chiamata Gemini: {str(e)}. Verifica GOOGLE_API_KEY.",
        )
