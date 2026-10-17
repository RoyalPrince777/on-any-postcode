"""First-party OAP Transport operator gateway.

This module is the single company-owned boundary between OAP rider surfaces and
external transport operators. Provider-specific adapters remain behind this
layer so public OAP routes do not depend on operator implementations directly.
"""
from __future__ import annotations

from typing import Any

from . import shared_bike

DEFAULT_SHARED_BIKE_RADIUS_KM = shared_bike.DEFAULT_RADIUS_KM
AVAILABILITY_CONTRACT = "oap_transport_availability_v1"
SUPPORTED_MODES = ("e-bike", "car", "transit")


def status() -> dict[str, Any]:
    shared = shared_bike.status()
    return {
        "product": "OAP Operator Gateway",
        "owner": "ON ANY POSTCODE LTD",
        "first_party_gateway": True,
        "availability_contract": AVAILABILITY_CONTRACT,
        "supported_modes": list(SUPPORTED_MODES),
        "mode_readiness": {
            "e-bike": "read_only_discovery",
            "car": "adapter_not_configured",
            "transit": "adapter_not_configured",
        },
        "shared_bikes": shared,
        "provider_count": int(shared.get("configured_operator_count") or 0),
        "provider_names": list(shared.get("configured_operators") or ()),
        "external_operator_control": False,
        "read_only_by_default": True,
        "human_authority_final": True,
        "truth_boundary": (
            "OAP owns the gateway and rider-facing contract. External operators "
            "retain physical vehicle, lock, motor, dispatch, billing and fleet "
            "authority unless separately evidenced and authorised."
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


def availability(
    *,
    mode: object,
    radius_km: object = DEFAULT_SHARED_BIKE_RADIUS_KM,
) -> dict[str, Any]:
    """Return one provider-neutral availability contract.

    Only e-bike read-only discovery currently has a configured adapter. Car and
    transit deliberately fail closed until real adapters are installed.
    """
    normalized = str(mode or "").strip().lower()
    if normalized not in SUPPORTED_MODES:
        raise ValueError("unsupported_transport_mode")

    if normalized == "e-bike":
        payload = nearby_shared_bikes_mitcham(radius_km=radius_km)
        vehicles = payload.get("vehicles")
        options = list(vehicles) if isinstance(vehicles, list) else []
        return {
            "contract": AVAILABILITY_CONTRACT,
            "mode": normalized,
            "available": bool(options),
            "option_count": len(options),
            "options": options,
            "source_state": "operator_feed",
            "operator_control_authorised": False,
            "execution_available": False,
            "gateway": {
                "name": "OAP Operator Gateway",
                "first_party": True,
            },
        }

    return {
        "contract": AVAILABILITY_CONTRACT,
        "mode": normalized,
        "available": False,
        "option_count": 0,
        "options": [],
        "source_state": "adapter_not_configured",
        "operator_control_authorised": False,
        "execution_available": False,
        "gateway": {
            "name": "OAP Operator Gateway",
            "first_party": True,
        },
    }
