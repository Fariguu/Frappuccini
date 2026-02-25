"""
Curva di esodo: distribuzione del traffico nelle ore successive alla fine evento.
"""


def compute_exodus_curve(
    event_end_time: str,
    base_multiplier: float,
    hours: list[int],
) -> dict[str, float]:
    """
    Calcola il moltiplicatore per ora in base alla curva di esodo.
    Distribuzione percentuale: 50% nell'ora di fine, 30% nell'ora+1, 20% nell'ora prima.
    """
    try:
        parts = event_end_time.strip().split(":")
        end_hour = int(parts[0]) if parts else 22
    except (ValueError, IndexError):
        end_hour = 22

    extra = base_multiplier - 1.0
    hour_set = set(hours)
    result = {}
    for h in hours:
        if h < end_hour - 1:
            result[f"{h:02d}:00"] = 1.0
        elif h == end_hour - 1:
            # 20% dell'impatto nell'ora prima della fine
            result[f"{h:02d}:00"] = 1.0 + 0.2 * extra
        elif h == end_hour:
            # 50% nell'ora fine; se non c'è ora+1 nel range, concentra 50%+30%
            if (end_hour + 1) in hour_set:
                result[f"{h:02d}:00"] = 1.0 + 0.5 * extra
            else:
                result[f"{h:02d}:00"] = 1.0 + 0.8 * extra
        elif h == end_hour + 1:
            # 30% nell'ora successiva
            result[f"{h:02d}:00"] = 1.0 + 0.3 * extra
        else:
            result[f"{h:02d}:00"] = 1.0
    return result
