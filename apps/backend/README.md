# Backend Frappuccini

API FastAPI per la simulazione del traffico a Bari in presenza di eventi.

## Requisiti

- Python 3.11+
- Virtual environment (venv)

## Setup

1. Copia il file di esempio delle variabili d'ambiente:
   ```bash
   cp env.example .env
   ```

2. Inserisci la tua `GOOGLE_API_KEY` nel file `.env` (richiesta per la stima dell'impatto evento via Gemini).

## Avvio

Da `apps/backend`:

```bash
npm run dev
```

Oppure con uvicorn direttamente:

```bash
uvicorn main:app --reload --port 8000
```

Il backend sarà disponibile su `http://localhost:8000`. Documentazione API: `http://localhost:8000/docs`.

## API principali

| Endpoint | Metodo | Descrizione |
|----------|--------|-------------|
| `/api` | GET | Health check |
| `/api/hello` | GET | Health check esteso |
| `/api/map` | GET | GeoJSON mappa stradale Bari |
| `/api/baseline` | GET | Traffico baseline (senza evento) per una data |
| `/api/simulate-day` | POST | Simulazione traffico con evento |

### Esempio richiesta `/api/simulate-day`

```json
{
  "event_name": "Concerto Stadio San Nicola",
  "capacity": 50000,
  "vip_names": ["Vasco Rossi"],
  "date": "2022-01-01",
  "event_end_time": "22:00",
  "event_venue": "Stadio San Nicola, Bari",
  "event_position": { "neighborhood": "Poggiofranco" }
}
```

- **event_venue** (opzionale): nome del luogo per geocoding via Nominatim (es. "Stadio San Nicola, Bari")
- **event_position** (opzionale): posizione diretta — `{"neighborhood": "Poggiofranco"}` o `{"lat": 41.08, "lng": 16.85}`

Se forniti, l'impatto sul traffico viene attenuato per le strade lontane dall'evento (decay spaziale).

## Dati

- **Dataset traffico**: `dataset/output/bari_traffic_simulated_22_25.csv` (monorepo)
- **GeoJSON mappa**: `data/strade_bari.geojson`

## Script

- `python scripts/dbf_summary.py` — Analizza file DBF nella cartella dataset e genera `scripts/dataset_report.md`
- `python scripts/shapefile_to_geojson.py` — Converte Shapefile in GeoJSON (richiede geopandas, matplotlib)

## Test

Test unitari (pytest):

```bash
npm run test
```

Test E2E dell'endpoint di simulazione (avvia prima il backend):

```bash
npm run test:e2e
```

## Struttura

```
apps/backend/
├── main.py           # Entry point FastAPI
├── config.py        # Configurazione (path, env, costanti)
├── api/routes/      # Endpoint (health, map, traffic)
├── services/        # Logica business (traffico, esodo, Gemini)
├── models/          # Schemi Pydantic
├── data/            # GeoJSON mappa
├── scripts/         # Script standalone
└── tests/           # Test E2E
```
