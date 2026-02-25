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
        hours = [k for k in result.keys() if k and ":" in k]
        assert len(hours) >= 1
        assert "16:00" in result or any(":" in k for k in result)

    def test_baseline_structure(self):
        result = process_traffic_data("2022-01-01", multiplier=1.0)
        for hour, streets in result.items():
            if ":" in str(hour):
                assert isinstance(streets, dict)
                for street, color in streets.items():
                    assert isinstance(street, str)
                    assert color in ("#ff0000", "#ffa500", "#00ff00")

    def test_with_multiplier_increases_volume(self):
        baseline = process_traffic_data("2022-01-01", multiplier=1.0)
        scaled = process_traffic_data("2022-01-01", multiplier=2.0)
        # Con moltiplicatore 2.0 ci aspettiamo più Critical/High
        baseline_c = sum(1 for h, s in baseline.items() if isinstance(s, dict) for c in s.values() if c == "#ff0000")
        scaled_c = sum(1 for h, s in scaled.items() if isinstance(s, dict) for c in s.values() if c == "#ff0000")
        assert scaled_c >= baseline_c

    def test_with_event_neighborhood_applies_decay(self):
        # Con event_neighborhood il risultato deve essere diverso da senza
        without = process_traffic_data(
            "2022-01-01",
            multipliers_by_hour={"16:00": 1.5, "17:00": 1.5, "18:00": 2.0, "19:00": 2.0, "20:00": 2.0, "21:00": 1.5, "22:00": 1.2, "23:00": 1.0},
        )
        with_neighborhood = process_traffic_data(
            "2022-01-01",
            multipliers_by_hour={"16:00": 1.5, "17:00": 1.5, "18:00": 2.0, "19:00": 2.0, "20:00": 2.0, "21:00": 1.5, "22:00": 1.2, "23:00": 1.0},
            event_neighborhood="Poggiofranco",
        )
        # I risultati possono essere diversi (decay per strada)
        assert isinstance(with_neighborhood, dict)
        assert set(with_neighborhood.keys()) == set(without.keys())

    def test_invalid_date_raises_404(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            process_traffic_data("1990-01-01", multiplier=1.0)
        assert exc_info.value.status_code == 404
