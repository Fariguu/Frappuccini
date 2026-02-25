"""
Curva di arrivo + esodo: distribuzione del traffico nelle ore
precedenti (arrivo) e successive (esodo) all'evento.
"""


def get_time_fractions(start_hour: int, end_hour: int) -> dict[int, float]:
    """
    Restituisce le frazioni temporali per ogni ora (arrivo + esodo).
    Fonte unica di verità usata sia per i moltiplicatori che per l'iniezione volume.
    """
    time_frac_map: dict[int, float] = {
        start_hour - 2: 0.15,
        start_hour - 1: 0.35,
        start_hour: 0.50,
        end_hour: 0.60,
        end_hour + 1: 0.35,
        end_hour + 2: 0.15,
    }
    for h in range(start_hour + 1, end_hour):
        time_frac_map[h] = 0.20
    return time_frac_map


def compute_exodus_curve(
    event_end_time: str,
    base_multiplier: float,
    hours: list[int],
    event_duration_hours: int = 3,
) -> dict[str, float]:
    """
    Calcola il moltiplicatore per ora in base alla curva arrivo + esodo.

    Fasi modellate:
      - Arrivo anticipato   (start - 2):  15 % dell'extra
      - Arrivo principale   (start - 1):  35 %
      - Inizio evento       (start):      50 %
      - Durante evento      (start..end): 20 %
      - Picco esodo         (end):        60 %
      - Esodo continuato    (end + 1):    35 %
      - Coda esodo          (end + 2):    15 %

    ``event_duration_hours`` (default 3) serve a calcolare l'ora di inizio.
    """
    try:
        parts = event_end_time.strip().split(":")
        end_hour = int(parts[0]) if parts else 22
    except (ValueError, IndexError):
        end_hour = 22

    start_hour = end_hour - event_duration_hours
    extra = base_multiplier - 1.0
    time_frac_map = get_time_fractions(start_hour, end_hour)
    result: dict[str, float] = {}

    for h in hours:
        frac = time_frac_map.get(h, 0.0)
        result[f"{h:02d}:00"] = 1.0 + frac * extra

    return result
