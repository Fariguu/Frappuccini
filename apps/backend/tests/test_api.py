"""Test API endpoints con TestClient."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test endpoint health."""

    def test_api_root(self):
        r = client.get("/api")
        assert r.status_code == 200

    def test_hello(self):
        r = client.get("/api/hello")
        assert r.status_code == 200


class TestBaseline:
    """Test /api/baseline."""

    def test_baseline_valid_date(self):
        r = client.get("/api/baseline?date=2022-01-01")
        if r.status_code == 500 and "Dataset non trovato" in (r.json().get("detail") or ""):
            pytest.skip("Dataset non disponibile")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict)

    def test_baseline_missing_date(self):
        r = client.get("/api/baseline")
        assert r.status_code == 422  # validation error


class TestSimulateDay:
    """Test /api/simulate-day."""

    @pytest.fixture
    def minimal_event(self):
        return {
            "event_name": "Test Event",
            "capacity": 1000,
            "vip_names": [],
            "date": "2022-01-01",
            "multiplier": 1.5,
        }

    def test_simulate_minimal(self, minimal_event):
        r = client.post("/api/simulate-day", json=minimal_event)
        if r.status_code == 500 and "Dataset non trovato" in (r.json().get("detail") or ""):
            pytest.skip("Dataset non disponibile")
        if r.status_code == 500 and "GOOGLE_API_KEY" in (r.json().get("detail") or ""):
            pytest.skip("GOOGLE_API_KEY non configurata")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict)

    def test_simulate_with_event_position(self, minimal_event):
        minimal_event["event_position"] = {"neighborhood": "Poggiofranco"}
        r = client.post("/api/simulate-day", json=minimal_event)
        if r.status_code == 500:
            detail = r.json().get("detail", "")
            if "Dataset" in detail or "GOOGLE" in detail:
                pytest.skip("Config non disponibile")
        assert r.status_code == 200

    def test_simulate_with_event_venue_mocked(self, minimal_event):
        minimal_event["event_venue"] = "Stadio San Nicola, Bari"
        minimal_event.pop("event_position", None)
        with patch("services.event_position.geocode_place", return_value=(41.08, 16.85)):
            r = client.post("/api/simulate-day", json=minimal_event)
        if r.status_code == 500:
            detail = r.json().get("detail", "")
            if "Dataset" in detail or "GOOGLE" in detail:
                pytest.skip("Config non disponibile")
        assert r.status_code == 200

    def test_simulate_invalid_payload(self):
        r = client.post("/api/simulate-day", json={})
        assert r.status_code == 422

    def test_simulate_missing_required_field(self):
        r = client.post(
            "/api/simulate-day",
            json={
                "event_name": "Test",
                "capacity": 1000,
                "vip_names": [],
                # date mancante
            },
        )
        assert r.status_code == 422
