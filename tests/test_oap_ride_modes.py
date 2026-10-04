from __future__ import annotations

from pathlib import Path

from mission_control import oap_ride_modes


def test_unified_ride_exposes_car_and_ebike_modes():
    state = oap_ride_modes.status()

    assert state["product"] == "OAP Ride"
    assert state["first_party_surface"] is True
    assert state["mode_count"] == 2
    assert set(state["modes"]) == {"car", "ebike"}

    car = state["modes"]["car"]
    assert car["label"] == "Car Ride"
    assert car["request_route"] == "/transport/ride/request"
    assert car["external_dispatch_performed"] is False

    ebike = state["modes"]["ebike"]
    assert ebike["label"] == "E-Bike"
    assert ebike["availability_route"] == "/transport/ride/ebikes/mitcham"
    assert ebike["provider_gateway"] == "OAP Operator Gateway"
    assert ebike["operator_control_authorised"] is False
    assert ebike["unlock_enabled"] is False
    assert ebike["payment_enabled"] is False
    assert ebike["motor_control_enabled"] is False


def test_ebike_mode_stays_behind_operator_gateway(monkeypatch):
    monkeypatch.setattr(
        oap_ride_modes.operator_gateway,
        "nearby_shared_bikes_mitcham",
        lambda *, radius_km: {
            "vehicle_count": 1,
            "vehicles": [{"oap_vehicle_id": "oap-bike-test"}],
            "radius_km": float(radius_km),
        },
    )

    result = oap_ride_modes.nearby_ebikes_mitcham(radius_km=4)
    assert result["ride_mode"] == "ebike"
    assert result["ride_surface"] == "OAP Ride"
    assert result["vehicle_count"] == 1
    assert result["radius_km"] == 4.0


def test_transport_ride_route_uses_unified_mode_contract():
    source = Path("mission_control/global_transport_views.py").read_text(encoding="utf-8")

    assert "jsonify(oap_ride_modes.status())" in source
    assert '@bp.get("/transport/ride/ebikes/mitcham")' in source
    assert "oap_ride_modes.nearby_ebikes_mitcham(" in source
