from __future__ import annotations

import pytest

from mission_control import routing


def test_routing_requires_https_and_explicit_host_allowlist(monkeypatch):
    monkeypatch.setenv("OAP_OSRM_BASE_URL", "https://router.example.test")
    monkeypatch.delenv("OAP_OSRM_ALLOWED_HOSTS", raising=False)
    assert routing.configured() is False

    monkeypatch.setenv("OAP_OSRM_ALLOWED_HOSTS", "router.example.test")
    assert routing.configured() is True

    monkeypatch.setenv("OAP_OSRM_BASE_URL", "http://router.example.test")
    assert routing.configured() is False


def test_routing_rejects_credentials_and_unapproved_host(monkeypatch):
    monkeypatch.setenv("OAP_OSRM_ALLOWED_HOSTS", "router.example.test")
    monkeypatch.setenv(
        "OAP_OSRM_BASE_URL", "https://user:pass@router.example.test"
    )
    assert routing.configured() is False

    monkeypatch.setenv("OAP_OSRM_BASE_URL", "https://other.example.test")
    assert routing.configured() is False


def test_route_returns_eta_distance_without_geometry_or_dispatch(monkeypatch):
    monkeypatch.setenv("OAP_OSRM_BASE_URL", "https://router.example.test")
    monkeypatch.setenv("OAP_OSRM_ALLOWED_HOSTS", "router.example.test")
    captured = {}

    def fake_request(url, *, expected_host):
        captured["url"] = url
        captured["host"] = expected_host
        return {"code": "Ok", "routes": [{"distance": 1234.56, "duration": 321.4}]}

    monkeypatch.setattr(routing, "_request_json", fake_request)
    result = routing.route(
        pickup_latitude=51.4,
        pickup_longitude=-0.2,
        destination_latitude=51.5,
        destination_longitude=-0.1,
        profile="driving",
    )

    assert result == {
        "distance_m": 1234.6,
        "duration_s": 321.4,
        "profile": "driving",
        "provider": "OSRM-compatible routing",
        "geometry_exposed": False,
        "dispatch_performed": False,
    }
    assert captured["host"] == "router.example.test"
    assert "overview=false" in captured["url"]
    assert "steps=false" in captured["url"]
    assert "geometr" not in captured["url"].lower()


def test_route_rejects_invalid_coordinates_and_profile(monkeypatch):
    monkeypatch.setenv("OAP_OSRM_BASE_URL", "https://router.example.test")
    monkeypatch.setenv("OAP_OSRM_ALLOWED_HOSTS", "router.example.test")

    with pytest.raises(ValueError, match="invalid_pickup_latitude"):
        routing.route(
            pickup_latitude=100,
            pickup_longitude=0,
            destination_latitude=0,
            destination_longitude=0,
        )

    with pytest.raises(ValueError, match="invalid_route_profile"):
        routing.route(
            pickup_latitude=51,
            pickup_longitude=0,
            destination_latitude=52,
            destination_longitude=0,
            profile="spaceship",
        )


def test_route_fails_closed_when_provider_is_not_configured(monkeypatch):
    monkeypatch.delenv("OAP_OSRM_BASE_URL", raising=False)
    monkeypatch.delenv("OAP_OSRM_ALLOWED_HOSTS", raising=False)

    with pytest.raises(
        routing.RoutingUnavailable, match="routing_provider_not_configured"
    ):
        routing.route(
            pickup_latitude=51,
            pickup_longitude=0,
            destination_latitude=52,
            destination_longitude=0,
        )
