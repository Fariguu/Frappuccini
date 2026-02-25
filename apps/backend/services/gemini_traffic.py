"""
Servizio per stimare l'impatto sul traffico di un evento usando Gemini.
Include sia il moltiplicatore semplice (legacy) sia l'estrazione
conversazionale completa usata dall'endpoint /api/chat.
"""

import json
import re

import google.generativeai as genai
from fastapi import HTTPException

from config import get_google_api_key
from models.schemas import ChatMessage, ExtractedParams

_gemini_multiplier_cache: dict[tuple, float] = {}

CHAT_SYSTEM_PROMPT = """\
Sei un assistente esperto di mobilità urbana e previsione del traffico per la città di Bari, Italia.
Il tuo compito è aiutare l'utente a configurare una simulazione di traffico legata a un evento.

### Cosa devi fare
1. **Estrarre i parametri dell'evento** dalla conversazione: nome evento, venue/luogo, data (YYYY-MM-DD), orario di fine (HH:MM), capacità (numero intero di persone), lista nomi VIP.
2. **Analizzare l'impatto dei VIP** sul traffico: valuta la popolarità di ogni ospite, la dimensione della fanbase, il tipo di pubblico che attraggono, e quanto questo influenzerà la mobilità. Questa analisi è fondamentale e deve essere approfondita. Metti TUTTA l'analisi VIP dettagliata nel campo "vip_analysis", NON nella "reply".
3. **Stimare un moltiplicatore di traffico** (float da 1.0 a 3.0):
   - 1.0 = nessun impatto aggiuntivo
   - 1.5 = impatto moderato (evento locale, < 5000 persone)
   - 2.0 = impatto significativo (artista nazionale, 10-30k persone)
   - 2.5 = impatto forte (star internazionale, > 30k persone)
   - 3.0 = paralisi totale (evento eccezionale, > 50k persone con VIP di fama mondiale)
   La capacità non è un impatto fisso ma un fattore moltiplicativo: un evento da 50k con un artista locale avrà meno impatto di uno da 30k con una superstar.
4. **Chiedere informazioni mancanti** quando necessario.

### Venue principali di Bari
- Stadio San Nicola: capienza ~58.000 (quartiere S.Nicola/Poggiofranco)
- Palaflorio: capienza ~6.000 (quartiere Poggiofranco)
- Teatro Petruzzelli: capienza ~1.200 (quartiere Murat)
- Fiera del Levante: capienza variabile fino a 30.000 (quartiere Libertà)
- Arena della Vittoria: capienza ~3.000 (quartiere Madonnella)
- Piazza Libertà: capienza variabile fino a 15.000

### REGOLE per il campo "reply"
- Massimo 2-3 frasi brevi e dirette.
- NON ripetere nella reply ciò che è già nei parametri estratti (nome, data, venue, etc.): il frontend li mostra separatamente in una card.
- NON ripetere nella reply l'analisi VIP: va nel campo "vip_analysis".
- Se mancano informazioni, chiedi SOLO quelle mancanti in modo conciso.
- NON usare markdown (no **, no #, no elenchi). Solo testo piano.
- Tono amichevole, breve, professionale.

### Formato risposta
Rispondi SEMPRE con un JSON valido (e nient'altro) con questa struttura:
{
  "reply": "Breve risposta conversazionale (2-3 frasi max). Niente markdown.",
  "extracted_params": {
    "event_name": "string o null",
    "venue": "string o null",
    "date": "YYYY-MM-DD o null",
    "end_time": "HH:MM o null",
    "capacity": intero o null,
    "vip_names": ["lista", "nomi"],
    "vip_analysis": "Analisi dettagliata dell'impatto dei VIP sulla mobilità (popolarità, fanbase, tipo pubblico, impatto stimato). Questo campo può essere lungo e dettagliato.",
    "estimated_multiplier": float 1.0-3.0 o null,
    "confidence": "low | medium | high"
  },
  "ready_to_simulate": true/false,
  "missing_info": ["lista informazioni ancora mancanti"]
}

"ready_to_simulate" è true solo quando hai almeno: event_name, date, capacity e estimated_multiplier.
Se mancano venue o end_time, usa valori di default ragionevoli ma segnalalo.
"""


def _get_model():
    api_key = get_google_api_key()
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GOOGLE_API_KEY non configurata. Imposta la variabile d'ambiente.",
        )
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-2.5-flash")


def get_event_traffic_multiplier(
    event_name: str, capacity: int, vip_names: list[str]
) -> float:
    """Legacy: restituisce un moltiplicatore semplice 1.0-3.0."""
    cache_key = (event_name, capacity, tuple(sorted(vip_names)))
    if cache_key in _gemini_multiplier_cache:
        return _gemini_multiplier_cache[cache_key]

    model = _get_model()
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


def chat_extract_event(messages: list[ChatMessage]) -> dict:
    """
    Invia la conversazione a Gemini con system prompt strutturato.
    Restituisce il dict con reply, extracted_params, ready_to_simulate, missing_info.
    """
    model = _get_model()

    gemini_messages = [{"role": "user", "parts": [CHAT_SYSTEM_PROMPT]}]
    gemini_messages.append(
        {"role": "model", "parts": ['{"reply": "Ciao! Sono il tuo assistente per la simulazione del traffico a Bari. Descrivimi l\'evento che vuoi simulare: nome, luogo, data, orario, capacità e ospiti VIP.", "extracted_params": {"event_name": null, "venue": null, "date": null, "end_time": null, "capacity": null, "vip_names": [], "vip_analysis": null, "estimated_multiplier": null, "confidence": null}, "ready_to_simulate": false, "missing_info": ["event_name", "date", "capacity"]}']}
    )

    for msg in messages:
        role = "user" if msg.role == "user" else "model"
        gemini_messages.append({"role": role, "parts": [msg.content]})

    try:
        response = model.generate_content(gemini_messages)
        raw = response.text.strip()

        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)

        parsed = json.loads(raw)

        params = parsed.get("extracted_params", {})
        if params.get("estimated_multiplier") is not None:
            params["estimated_multiplier"] = max(
                1.0, min(3.0, float(params["estimated_multiplier"]))
            )

        return {
            "reply": parsed.get("reply", ""),
            "extracted_params": ExtractedParams(**params).model_dump(),
            "ready_to_simulate": bool(parsed.get("ready_to_simulate", False)),
            "missing_info": parsed.get("missing_info", []),
        }
    except json.JSONDecodeError:
        return {
            "reply": raw if 'raw' in dir() else "Errore nel parsing della risposta.",
            "extracted_params": ExtractedParams().model_dump(),
            "ready_to_simulate": False,
            "missing_info": ["Errore di comunicazione con l'IA, riprova."],
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Errore chiamata Gemini: {str(e)}",
        )
