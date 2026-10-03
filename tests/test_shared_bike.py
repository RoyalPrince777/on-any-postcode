from __future__ import annotations

from mission_control import shared_bike


def test_shared_bike_status_is_read_only_when_unconfigured(monkeypatch):
    monkeypatch.delenv("OAP_SHARED_BIKE_LIME_GBFS_URL", raising=False)
    monkeypatch.delenv("OAP_SHARED_BIKE_FOREST_GBFS_URL", raising=False)
    monkeypatch.delenv("OAP_SHARED_BIKE_ALLOWED_HOSTS", raising=False)

    state = shared_bike.status()
    assert state["area"] == "Mitcham / CR4"
    assert state["protocol"] == "GBFS"
    assert state["configured_operator_count"] == 0
    assert state["feed_configured"] is False
    assert state["live_feed_connected"] is False
    assert state["unlock_enabled"] is False
    assert state["lock_enabled"] is False
    assert state["payment_enabled"] is False
    assert state["motor_control_enabled"] is False


def test_mitcham_discovery_normalizes_public_gbfs_without_control(monkeypatch):
    monkeypatch.setenv("OAP_SHARED_BIKE_ALLOWED_HOSTS", "feeds.example")
    monkeypatch.setenv(
        "OAP_SHARED_BIKE_LIME_GBFS_URL",
        "https://feeds.example/london/gbfs.json",
    )
    discovery = {
        "data": {
            "feeds": [
                {
                    "name": "vehicle_status",
                    "url": "https://feeds.example/london/vehicle_status.json",
                }
            ]
        }
    }
    vehicles = {
        "data": {
            "vehicles": [
                {
                    "vehicle_id": "bike-near",
                    "lat": 51.404,
                    "lon": -0.169,
                    "is_reserved": False,
                    "is_disabled": False,
                    "rental_uris": {
                        "android": "operator://bike-near",
                    },
                },
                {
                    "vehicle_id": "bike-far",
                    "lat": 51.60,
                    "lon": -0.169,
                    "is_reserved": False,
                    "is_disabled": False,
                },
            ]
        }
    }

    def fake_fetch(url: str):
        return discovery if url.endswith("/gbfs.json") else vehicles

    monkeypatch.setattr(shared_bike, "_fetch_json", fake_fetch)

    state = shared_bike.nearby_mitcham(radius_km=5)
    assert state["configured_operator_count"] == 1
    assert state["operators"]["lime"]["connected"] is True
    assert state["vehicle_count"] == 1
    vehicle = state["vehicles"][0]
    assert vehicle["operator"] == "lime"
    assert vehicle["source"] == "operator_public_gbfs"
    assert vehicle["read_only"] is True
    assert vehicle["unlock_performed"] is False
    assert vehicle["lock_performed"] is False
    assert vehicle["payment_performed"] is False
    assert vehicle["motor_control_performed"] is False
    assert vehicle["oap_vehicle_id"].startswith("oap-bike-")
    assert "bike-near" not in vehicle["oap_vehicle_id"]


def test_shared_bike_rejects_unapproved_feed_host(monkeypatch):
    monkeypatch.setenv("OAP_SHARED_BIKE_ALLOWED_HOSTS", "approved.example")
    monkeypatch.setenv(
        "OAP_SHARED_BIKE_FOREST_GBFS_URL",
        "https://unapproved.example/gbfs.json",
    )
    assert shared_bike.configured_operators() == {}


def test_shared_bike_radius_is_bounded():
    try:
        shared_bike.nearby_mitcham(radius_km=99)
    except ValueError as exc:
        assert str(exc) == "invalid_radius_km"
    else:
        raise AssertionError("oversized radius should be rejected")
