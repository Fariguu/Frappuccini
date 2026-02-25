#!/usr/bin/env python3
"""
Test E2E dell'endpoint /api/simulate-day.
Avvia prima il backend: npm run dev
Poi: python tests/test_simulate_e2e.py (da apps/backend)
"""

import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE_URL = "http://localhost:8000"

# Mappa colore -> livello abbreviato
COLOR_TO_LEVEL = {
    "#ff0000": "C",  # Critical
    "#ffa500": "H",  # High
    "#00ff00": "N",  # Normal
}


def color_to_level(color: str) -> str:
    return COLOR_TO_LEVEL.get(color, "?")


def _extract_by_street(data: dict) -> dict:
    """Estrae by_street dalla risposta API (formato nuovo)."""
    return data.get("by_street", data)


def fetch_baseline(date: str) -> dict:
    url = f"{BASE_URL}/api/baseline?date={date}"
    req = Request(url, method="GET")
    with urlopen(req) as resp:
        return _extract_by_street(json.load(resp))


def fetch_simulate(date: str, event: dict) -> dict:
    url = f"{BASE_URL}/api/simulate-day"
    data = json.dumps(event).encode("utf-8")
    req = Request(url, data=data, method="POST", headers={"Content-Type": "application/json"})
    with urlopen(req) as resp:
        return _extract_by_street(json.load(resp))


def build_comparison_table(baseline: dict, with_event: dict):
    """Restituisce (headers, rows) per la tabella."""
    hours = sorted([k for k in baseline.keys() if k and ":" in k])
    all_streets = set()
    for h in hours:
        all_streets.update(baseline.get(h, {}).keys())
        all_streets.update(with_event.get(h, {}).keys())
    streets = sorted(all_streets)

    rows = []
    for street in streets:
        row = [street[:28] + ".." if len(street) > 30 else street]
        for h in hours:
            b_color = baseline.get(h, {}).get(street, "#00ff00")
            e_color = with_event.get(h, {}).get(street, "#00ff00")
            b = color_to_level(b_color)
            e = color_to_level(e_color)
            row.append(f"{b}→{e}" if b != e else b)
        rows.append(row)

    return ["Strada"] + hours, rows


def build_summary(baseline: dict, with_event: dict) -> dict:
    """Calcola riepilogo per picco evento (18-20) vs resto (16-17, 21-23)."""
    peak_hours = ["18:00", "19:00", "20:00"]
    rest_hours = ["16:00", "17:00", "21:00", "22:00", "23:00"]

    def count_by_level(data: dict, hours: list) -> dict:
        counts = {"C": 0, "H": 0, "N": 0}
        for h in hours:
            for street, color in data.get(h, {}).items():
                level = color_to_level(color)
                counts[level] = counts.get(level, 0) + 1
        return counts

    return {
        "picco_baseline": count_by_level(baseline, peak_hours),
        "picco_evento": count_by_level(with_event, peak_hours),
        "resto_baseline": count_by_level(baseline, rest_hours),
        "resto_evento": count_by_level(with_event, rest_hours),
    }


def main() -> None:
    event = {
        "event_name": "Concerto Stadio San Nicola",
        "capacity": 50000,
        "vip_names": ["Vasco Rossi"],
        "date": "2022-01-01",
        "event_position": {"neighborhood": "Poggiofranco"},
    }
    date = event["date"]

    print("=" * 80)
    print("TEST SIMULAZIONE EVENTO - Backend /api/simulate-day")
    print("=" * 80)
    print(f"\nEvento: {event['event_name']}")
    print(f"Capacità: {event['capacity']} persone")
    print(f"Ospiti: {event['vip_names']}")
    print(f"Luogo: {event.get('event_position') or event.get('event_venue', 'non specificato')}")
    print(f"Data: {date}")
    print(f"\nLegenda: N=Normal, H=High, C=Critical | Cella: baseline→con evento")
    print()

    try:
        print("Connessione al backend...")
        baseline = fetch_baseline(date)
        print("  ✓ Baseline (senza evento) ricevuta")
        with_event = fetch_simulate(date, event)
        print("  ✓ Simulazione con evento ricevuta")
    except URLError as e:
        print(f"\nERRORE: Impossibile connettersi al backend su {BASE_URL}")
        print("Assicurati che il server sia avviato: cd apps/backend && npm run dev")
        print(f"Dettaglio: {e}")
        sys.exit(1)
    except HTTPError as e:
        try:
            body = e.fp.read().decode(errors="replace") if e.fp else ""
        except Exception:
            body = ""
        print(f"\nERRORE HTTP {e.code}: {e.reason}")
        if body:
            print("Dettaglio:", body[:500])
        sys.exit(1)

    summary = build_summary(baseline, with_event)

    print("\n" + "─" * 80)
    print("RIEPILOGO: Picco evento (18:00-20:00) vs Resto della giornata (16:00-17:00, 21:00-23:00)")
    print("─" * 80)
    print("                    | Picco evento (18-20)     | Resto giornata (16-17, 21-23)")
    print("                    | Baseline  | Con evento   | Baseline  | Con evento")
    print("─" * 80)
    print(f"  Critical (C)      | {summary['picco_baseline']['C']:^9} | {summary['picco_evento']['C']:^11} | {summary['resto_baseline']['C']:^9} | {summary['resto_evento']['C']:^11}")
    print(f"  High (H)          | {summary['picco_baseline']['H']:^9} | {summary['picco_evento']['H']:^11} | {summary['resto_baseline']['H']:^9} | {summary['resto_evento']['H']:^11}")
    print(f"  Normal (N)        | {summary['picco_baseline']['N']:^9} | {summary['picco_evento']['N']:^11} | {summary['resto_baseline']['N']:^9} | {summary['resto_evento']['N']:^11}")
    print("─" * 80)
    print("  (Conteggio strade×ore per fascia)")
    print()

    headers, rows = build_comparison_table(baseline, with_event)
    col_widths = [max(len(headers[0]), 30)] + [7] * (len(headers) - 1)

    print("\nTABELLA DETTAGLIATA: Baseline vs Con evento (per strada e ora)")
    print("─" * 80)
    header_row = "".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    print(header_row)
    print("─" * 80)

    for row in rows[:25]:  # Prime 25 strade
        print("".join(str(c).ljust(col_widths[i]) for i, c in enumerate(row)))

    if len(rows) > 25:
        print(f"... e altre {len(rows) - 25} strade")
    print("─" * 80)
    print("\nOK - Test completato.")


if __name__ == "__main__":
    main()
