"""Test servizio geocoding (Nominatim)."""

import io
from unittest.mock import patch

import pytest

from services.geocoding import geocode_place


class TestGeocodePlace:
    """Test geocode_place."""

    def test_empty_query_returns_none(self):
        assert geocode_place("") is None
        assert geocode_place("   ") is None

    def test_valid_response_returns_coords(self):
        json_body = b'[{"lat": "41.08", "lon": "16.85"}]'
        with patch("services.geocoding.urlopen") as mock_urlopen:
            mock_urlopen.return_value.__enter__.return_value = io.BytesIO(json_body)
            result = geocode_place("Stadio San Nicola, Bari")
            assert result == (41.08, 16.85)

    def test_empty_response_returns_none(self):
        with patch("services.geocoding.urlopen") as mock_urlopen:
            mock_urlopen.return_value.__enter__.return_value = io.BytesIO(b"[]")
            assert geocode_place("Luogo Inesistente XYZ") is None

    def test_invalid_json_returns_none(self):
        with patch("services.geocoding.urlopen") as mock_urlopen:
            mock_urlopen.return_value.__enter__.return_value = io.BytesIO(b"invalid")
            result = geocode_place("Test Query")
            assert result is None
