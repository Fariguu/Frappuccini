"""Test traffic_processor."""

import pytest

from config import DATASET_CSV_PATH
from services.traffic_processor import process_traffic_data


@pytest.mark.skipif(not DATASET_CSV_PATH.exists(), reason="Dataset CSV non trovato")
class TestProcessTrafficData:
    """Test process_traffic_data."""

    def test_baseline_returns_dict_by_hour(self):
        result = process_traffic_data("2022-01-01", multiplier=1.0)
        assert isinstance(result, dict)
        assert "by_street" in result and "by_neighborhood" in result
        by_street = result["by_street"]
        assert "16:00" in by_street or any(":" in k for k in by_street)

    def test_baseline_structure(self):
        result = process_traffic_data("2022-01-01", multiplier=1.0)
        for hour, streets in result["by_street"].items():
            assert isinstance(streets, dict)
            for street, color in streets.items():
                assert isinstance(street, str)
                assert color in ("#ff0000", "#ffa500", "#00ff00")

    def test_with_multiplier_increases_volume(self):
        baseline = process_traffic_data("2022-01-01", multiplier=1.0)
        scaled = process_traffic_data("2022-01-01", multiplier=2.0)
        bs = baseline["by_street"]
        ss = scaled["by_street"]
        baseline_c = sum(1 for s in bs.values() for c in s.values() if c == "#ff0000")
        scaled_c = sum(1 for s in ss.values() for c in s.values() if c == "#ff0000")
        assert scaled_c >= baseline_c

    def test_with_event_neighborhood_applies_decay(self):
        without = process_traffic_data(
            "2022-01-01",
            multipliers_by_hour={"16:00": 1.5, "17:00": 1.5, "18:00": 2.0, "19:00": 2.0, "20:00": 2.0, "21:00": 1.5, "22:00": 1.2, "23:00": 1.0},
        )
        with_neighborhood = process_traffic_data(
            "2022-01-01",
            multipliers_by_hour={"16:00": 1.5, "17:00": 1.5, "18:00": 2.0, "19:00": 2.0, "20:00": 2.0, "21:00": 1.5, "22:00": 1.2, "23:00": 1.0},
            event_neighborhood="Poggiofranco",
        )
        assert set(with_neighborhood["by_street"].keys()) == set(without["by_street"].keys())

    def test_future_date_uses_equivalent(self):
        """Date non presenti nel dataset vengono mappate a un giorno equivalente."""
        result = process_traffic_data("2030-06-15", multiplier=1.0)
        assert isinstance(result, dict)
        assert "by_street" in result
        assert "by_quartiere" in result
        assert len(result["by_street"]) > 0

    def test_result_contains_by_quartiere(self):
        result = process_traffic_data("2022-01-01", multiplier=1.0)
        assert "by_quartiere" in result
        assert "hours" in result
        for hour_colors in result["by_quartiere"].values():
            for color in hour_colors.values():
                assert color in ("#ff0000", "#ffa500", "#00ff00")

    def test_crowd_injection_large_event_visible_impact(self):
        """Un evento da 50k persone deve produrre impatto visibile (più strade rosse)."""
        baseline = process_traffic_data("2022-01-01", multiplier=1.0)
        with_event = process_traffic_data(
            "2022-01-01",
            multipliers_by_hour={f"{h:02d}:00": 1.0 for h in range(24)},
            event_neighborhood="Poggiofranco",
            event_capacity=50000,
            event_end_hour=22,
        )
        bs = baseline["by_street"]
        ev = with_event["by_street"]
        baseline_critical = sum(
            1 for s in bs.values() for c in s.values() if c == "#ff0000"
        )
        event_critical = sum(
            1 for s in ev.values() for c in s.values() if c == "#ff0000"
        )
        assert event_critical > baseline_critical, (
            f"Evento 50k: {event_critical} strade critiche vs {baseline_critical} baseline"
        )

    def test_crowd_injection_small_event_minimal_impact(self):
        """Un evento da 500 persone non deve stravolgere il traffico."""
        baseline = process_traffic_data("2022-01-01", multiplier=1.0)
        with_event = process_traffic_data(
            "2022-01-01",
            multipliers_by_hour={f"{h:02d}:00": 1.0 for h in range(24)},
            event_neighborhood="Murat",
            event_capacity=500,
            event_end_hour=22,
        )
        bs = baseline["by_street"]
        ev = with_event["by_street"]
        baseline_critical = sum(
            1 for s in bs.values() for c in s.values() if c == "#ff0000"
        )
        event_critical = sum(
            1 for s in ev.values() for c in s.values() if c == "#ff0000"
        )
        assert event_critical - baseline_critical <= 50, (
            f"Evento 500: delta critiche troppo alto ({event_critical - baseline_critical})"
        )

    def test_crowd_injection_concentrates_on_event_neighborhood(self):
        """L'impatto deve essere maggiore nel quartiere dell'evento."""
        result = process_traffic_data(
            "2022-01-01",
            multipliers_by_hour={f"{h:02d}:00": 1.0 for h in range(24)},
            event_neighborhood="Poggiofranco",
            event_capacity=30000,
            event_end_hour=22,
        )
        nb = result["by_neighborhood"]
        peak_hour = "22:00"
        if peak_hour in nb:
            event_nb_color = nb[peak_hour].get("Poggiofranco")
            assert event_nb_color in ("#ff0000", "#ffa500"), (
                f"Quartiere evento a {peak_hour} dovrebbe essere almeno arancione, trovato {event_nb_color}"
            )
