"""Unified first-party OAP Ride mode contract.

Car rides and shared e-bikes appear behind one OAP Ride surface while preserving
their different execution authorities. OAP owns the rider-facing contract;
operator-controlled actions remain fail-closed unless separately authorised.
"""
from __future__ import annotations

from typing import Any

from . import oap_ride, operator_gateway

RIDE_MODES = ("car", "ebike")


def status() -> dict[str, Any]:
    return {
        "product": "OAP Ride",
        "first_party_surface": True,
        "modes": {
            "car": {
                "label": "Car Ride",
                "journey_core": oap_ride.status(),
                "request_route": "/transport/ride/request",
                "availability_route": "/transport/ride/driver/availability",
                "external_dispatch_performed": False,
            },
            "ebike": {
                "label": "E-Bike",
                "availability_route": "/transport/ride/ebikes/mitcham",
                "provider_gateway": "OAP Operator Gateway",
                "operator_control_authorised": False,
                "unlock_enabled": False,
                "payment_enabled": False,
                "motor_control_enabled": False,
            },
        },
        "mode_count": len(RIDE_MODES),
        "guardian_transport": True,
        "human_authority_final": True,
        "truth_boundary": (
            "Car Ride uses OAP's governed ride-request state machine. E-Bike uses "
            "operator availability behind the first-party OAP Operator Gateway. "
            "Operator-controlled unlock, billing and motor actions remain disabled."
        ),
    }


def nearby_ebikes_mitcham(*, radius_km: object = operator_gateway.DEFAULT_SHARED_BIKE_RADIUS_KM) -> dict[str, Any]:
    payload = operator_gateway.nearby_shared_bikes_mitcham(radius_km=radius_km)
    payload["ride_mode"] = "ebike"
    payload["ride_surface"] = "OAP Ride"
    return payload
