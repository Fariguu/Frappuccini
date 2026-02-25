"""Test servizio event_position."""

from unittest.mock import patch

import pytest

from models.schemas import EventPosition
from services.event_position import (
    event_position_to_neighborhood,
    get_decay_factor,
    point_in_neighborhood,
)


class TestPointInNeighborhood:
    """Test point_in_neighborhood."""

    def test_poggiofranco_bbox(self):
        # Poggiofranco bbox: [16.835, 41.075, 16.865, 41.095]
        n = point_in_neighborhood(16.85, 41.08)
        assert n == "Poggiofranco"

    def test_s_nicola_bbox(self):
        # S.Nicola bbox: [16.858, 41.120, 16.878, 41.135]
        n = point_in_neighborhood(16.87, 41.125)
        assert n == "S.Nicola"

    def test_outside_bari_returns_none(self):
        n = point_in_neighborhood(10.0, 45.0)
        assert n is None


class TestEventPositionToNeighborhood:
    """Test event_position_to_neighborhood."""

    def test_from_neighborhood(self):
        pos = EventPosition(neighborhood="Poggiofranco")
        n = event_position_to_neighborhood(pos, None)
        assert n == "Poggiofranco"

    def test_from_lat_lng(self):
        pos = EventPosition(lat=41.08, lng=16.85)
        n = event_position_to_neighborhood(pos, None)
        assert n == "Poggiofranco"

    def test_none_position_none_venue(self):
        assert event_position_to_neighborhood(None, None) is None

    def test_venue_calls_geocoding(self):
        # Mock geocode per evitare chiamata esterna
        with patch(
            "services.event_position.geocode_place",
            return_value=(41.08, 16.85),
        ) as mock_geocode:
            n = event_position_to_neighborhood(None, "Stadio San Nicola, Bari")
            mock_geocode.assert_called_once_with("Stadio San Nicola, Bari")
            assert n == "Poggiofranco"

    def test_venue_priority_over_position(self):
        with patch(
            "services.event_position.geocode_place",
            return_value=(41.08, 16.85),
        ):
            pos = EventPosition(neighborhood="S.Nicola")
            n = event_position_to_neighborhood(pos, "Stadio San Nicola")
            assert n == "Poggiofranco"

    def test_venue_geocode_fails_returns_none(self):
        with patch(
            "services.event_position.geocode_place",
            return_value=None,
        ):
            n = event_position_to_neighborhood(None, "Luogo Inesistente XYZ")
            assert n is None

    def test_venue_outside_bari_returns_none(self):
        """Coordinate da Nominatim fuori bbox Bari vengono rifiutate."""
        with patch(
            "services.event_position.geocode_place",
            return_value=(45.46, 9.19),  # Milano
        ):
            n = event_position_to_neighborhood(None, "Duomo Milano")
            assert n is None


class TestGetDecayFactor:
    """Test get_decay_factor."""

    def test_same_neighborhood(self):
        assert get_decay_factor("Poggiofranco", "Poggiofranco") == 1.0
        assert get_decay_factor("S.Nicola", "S.Nicola") == 1.0

    def test_tier1_vicino(self):
        assert get_decay_factor("Carrassi", "Poggiofranco") == 0.6
        assert get_decay_factor("Libertà", "Poggiofranco") == 0.6

    def test_tier2_medio(self):
        assert get_decay_factor("S.Nicola", "Poggiofranco") == 0.3
        assert get_decay_factor("S. Pasquale", "Poggiofranco") == 0.3

    def test_lontano(self):
        assert get_decay_factor("Loseto", "Poggiofranco") == 0.15
        assert get_decay_factor("Torre A Mare", "Poggiofranco") == 0.15

    def test_nomi_composti(self):
        assert get_decay_factor("LibertàPicone(Municipio 2)", "Libertà") == 1.0

    def test_empty_returns_min(self):
        assert get_decay_factor("", "Poggiofranco") == 0.15
        assert get_decay_factor("Poggiofranco", "") == 0.15
