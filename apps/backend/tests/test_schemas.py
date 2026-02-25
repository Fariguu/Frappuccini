"""Test schemi Pydantic."""

import pytest
from pydantic import ValidationError

from models.schemas import EventPosition, SimulateDayRequest


class TestEventPosition:
    """Test EventPosition."""

    def test_neighborhood_only(self):
        p = EventPosition(neighborhood="Poggiofranco")
        assert p.neighborhood == "Poggiofranco"
        assert p.lat is None
        assert p.lng is None

    def test_lat_lng_only(self):
        p = EventPosition(lat=41.08, lng=16.85)
        assert p.lat == 41.08
        assert p.lng == 16.85
        assert p.neighborhood is None

    def test_all_none_valid(self):
        p = EventPosition()
        assert p.lat is None and p.lng is None and p.neighborhood is None

    def test_lat_only_invalid(self):
        with pytest.raises(ValidationError, match="Fornire"):
            EventPosition(lat=41.08)

    def test_lng_only_invalid(self):
        with pytest.raises(ValidationError, match="Fornire"):
            EventPosition(lng=16.85)


class TestSimulateDayRequest:
    """Test SimulateDayRequest."""

    def test_minimal_valid(self):
        r = SimulateDayRequest(
            event_name="Test",
            capacity=1000,
            vip_names=[],
            date="2022-01-01",
        )
        assert r.event_position is None
        assert r.event_venue is None
        assert r.event_end_time == "22:00"

    def test_with_event_position(self):
        r = SimulateDayRequest(
            event_name="Test",
            capacity=1000,
            vip_names=[],
            date="2022-01-01",
            event_position=EventPosition(neighborhood="Poggiofranco"),
        )
        assert r.event_position is not None
        assert r.event_position.neighborhood == "Poggiofranco"

    def test_with_event_venue(self):
        r = SimulateDayRequest(
            event_name="Test",
            capacity=1000,
            vip_names=[],
            date="2022-01-01",
            event_venue="Stadio San Nicola, Bari",
        )
        assert r.event_venue == "Stadio San Nicola, Bari"

    def test_with_multiplier(self):
        r = SimulateDayRequest(
            event_name="Test",
            capacity=1000,
            vip_names=[],
            date="2022-01-01",
            multiplier=2.0,
        )
        assert r.multiplier == 2.0
