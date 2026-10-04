from __future__ import annotations

from pathlib import Path

from mission_control import operator_gateway


def test_operator_gateway_is_first_party_and_fail_closed(monkeypatch):
    monkeypatch.delenv("OAP_SHARED_BIKE_LIME_GBFS_URL", raising=False)
    monkeypatch.delenv("OAP_SHARED_BIKE_FOREST_GBFS_URL", raising=False)
    monkeypatch.delenv("OAP_SHARED_BIKE_ALLOWED_HOSTS", raising=False)

    state = operator_gateway.status()
    assert state["product"] == "OAP Operator Gateway"
    assert state["owner"] == "ON ANY POSTCODE LTD"
    assert state["first_party_gateway"] is True
    assert state["provider_count"] == 0
    assert state["external_operator_control"] is False
    assert state["read_only_by_default"] is True
    assert state["network_transport_modes"] == ["bus", "rail", "metro", "tram", "ferry", "coach"]
    assert state["ride_modes"] == ["car", "e-bike"]
    assert state["map_modes"] == ["walk", "bicycle"]
    assert state["gateway_levels"][-1] == "ACTION_AUTHORISED"
    assert state["data_available_does_not_mean_action_authorised"] is True
    assert state["scheduled_is_not_live"] is True
    assert state["human_authority_final"] is True


def test_gateway_wraps_shared_bike_result(monkeypatch):
    monkeypatch.setattr(
        operator_gateway.shared_bike,
        "nearby_mitcham",
        lambda *, radius_km: {
            "product": "OAP Shared E-Bikes",
            "radius_km": float(radius_km),
            "vehicles": [],
            "vehicle_count": 0,
        },
    )

    result = operator_gateway.nearby_shared_bikes_mitcham(radius_km=3)
    assert result["radius_km"] == 3.0
    assert result["gateway"] == {
        "name": "OAP Operator Gateway",
        "first_party": True,
        "operator_control_authorised": False,
    }


def test_public_transport_view_uses_gateway_not_provider_adapter():
    source = Path("mission_control/global_transport_views.py").read_text(encoding="utf-8")

    assert "operator_gateway.shared_bikes_status()" in source
    assert "operator_gateway.nearby_shared_bikes_mitcham(" in source
    assert "shared_bike.nearby_mitcham(" not in source
    assert "shared_bike.status()" not in source
    assert "operator_gateway.DEFAULT_SHARED_BIKE_RADIUS_KM" in source
