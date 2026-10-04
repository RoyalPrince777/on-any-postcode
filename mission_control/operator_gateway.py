"""First-party OAP Transport operator gateway.

This module is the single company-owned boundary between OAP rider surfaces and
external transport operators. Provider-specific adapters remain behind this
layer so public OAP routes do not depend on operator implementations directly.
"""
from __future__ import annotations

from typing import Any

from . import journey_engine, shared_bike

DEFAULT_SHARED_BIKE_RADIUS_KM = shared_bike.DEFAULT_RADIUS_KM


def status() -> dict[str, Any]:
    shared = shared_bike.status()
    return {
        "product": "OAP Operator Gateway",
        "owner": "ON ANY POSTCODE LTD",
        "first_party_gateway": True,
        "shared_bikes": shared,
        "network_transport_modes": list(journey_engine.NETWORK_MODES),
        "ride_modes": list(journey_engine.RIDE_MODES),
        "map_modes": list(journey_engine.MAP_MODES),
        "gateway_levels": list(journey_engine.GATEWAY_LEVELS),
        "journey_engine": journey_engine.status(),
        "provider_count": int(shared.get("configured_operator_count") or 0),
        "provider_names": list(shared.get("configured_operators") or ()),
        "external_operator_control": False,
        "read_only_by_default": True,
        "data_available_does_not_mean_action_authorised": True,
        "scheduled_is_not_live": True,
        "human_authority_final": True,
        "truth_boundary": (
            "OAP owns the gateway and rider-facing contract. External operators "
            "retain physical bike, lock, motor, billing and fleet authority unless "
            "separately evidenced and authorised."
        ),
    }


def shared_bikes_status() -> dict[str, Any]:
    return shared_bike.status()


def nearby_shared_bikes_mitcham(
    *, radius_km: object = DEFAULT_SHARED_BIKE_RADIUS_KM
) -> dict[str, Any]:
    payload = shared_bike.nearby_mitcham(radius_km=radius_km)
    payload["gateway"] = {
        "name": "OAP Operator Gateway",
        "first_party": True,
        "operator_control_authorised": False,
    }
    return payload
