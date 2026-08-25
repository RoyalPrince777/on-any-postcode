"""Governed provider fabric for OAP external-service integrations.

The provider fabric gives OAP one stable contract for outside services without
hard-wiring product code to a vendor. It records what capability each provider
may supply, whether the code path is wired, and whether runtime delivery has
actually been observed. It never exposes credentials and never turns on a
real-world mutation merely because configuration exists.

Read-only location and weather providers already used by OAP are represented
here as wired adapters. Routing, telecom/eSIM, payments, fleet/dispatch and
other consequential operations remain fail-closed until a lawful provider,
compliance checks and Human Authority approval are connected.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from . import location_intelligence

HUMAN_APPROVAL_REQUIRED = True

PROVIDER_SLOTS: tuple[dict[str, Any], ...] = (
    {
        "id": "postcode",
        "name": "Postcode hierarchy",
        "risk": "read_only",
        "purpose": "Resolve UK postcodes into the OAP location hierarchy.",
        "required_for": ("The Spot", "OAP World"),
    },
    {
        "id": "geocoding",
        "name": "Global geocoding",
        "risk": "read_only",
        "purpose": "Resolve approved place searches into coarse map coordinates and hierarchy context.",
        "required_for": ("The Spot", "OAP World", "Movement"),
    },
    {
        "id": "weather",
        "name": "Weather",
        "risk": "read_only",
        "purpose": "Provide bounded current and short-range weather awareness.",
        "required_for": ("The Spot", "Movement"),
    },
    {
        "id": "routing",
        "name": "Routing",
        "risk": "read_only",
        "purpose": "Calculate routes and ETAs without dispatching a person or vehicle.",
        "required_for": ("Movement", "OAP Ride", "OAP Delivery"),
    },
    {
        "id": "telecom",
        "name": "Telecom / eSIM",
        "risk": "consequential",
        "purpose": "Provision approved managed connectivity for certified Movement devices.",
        "required_for": ("OAP eSIM Connectivity",),
    },
    {
        "id": "payments",
        "name": "Payments",
        "risk": "consequential",
        "purpose": "Authorize compliant monetary payment flows outside SIKA internal value records.",
        "required_for": ("Movement", "Market"),
    },
    {
        "id": "dispatch",
        "name": "Fleet / dispatch",
        "risk": "consequential",
        "purpose": "Match approved drivers, riders, couriers and fleet assets to governed jobs.",
        "required_for": ("OAP Ride", "OAP E-Bike", "OAP Delivery"),
    },
    {
        "id": "communications",
        "name": "Operational communications",
        "risk": "protected",
        "purpose": "Carry protected trip and job communication through OAP-owned Link Up boundaries.",
        "required_for": ("Movement", "Link Up"),
    },
)

# These adapters describe code paths that already exist in production. A wired
# adapter is not the same as a successful runtime delivery; delivery evidence
# comes from the provider-specific module and is kept separate below.
WIRED_ADAPTERS: tuple[dict[str, Any], ...] = (
    {
        "id": "postcodes_io",
        "slot_id": "postcode",
        "name": "UK Postcode Service",
        "host": "api.postcodes.io",
        "mode": "read_only",
        "wired": True,
        "mutation_enabled": False,
        "credential_required": False,
    },
    {
        "id": "open_meteo_geocoding",
        "slot_id": "geocoding",
        "name": "Global Place Service",
        "host": "geocoding-api.open-meteo.com",
        "mode": "read_only",
        "wired": True,
        "mutation_enabled": False,
        "credential_required": False,
    },
    {
        "id": "open_meteo_weather",
        "slot_id": "weather",
        "name": "Live Weather Service",
        "host": "api.open-meteo.com",
        "mode": "read_only",
        "wired": True,
        "mutation_enabled": False,
        "credential_required": False,
    },
)

CONSEQUENTIAL_CONTROLS: dict[str, bool] = {
    "routing_execution_enabled": False,
    "telecom_provisioning_enabled": False,
    "payment_capture_enabled": False,
    "dispatch_enabled": False,
    "carrier_switch_enabled": False,
    "remote_esim_install_enabled": False,
}


def _duplicate_ids(items: Iterable[Mapping[str, Any]]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for item in items:
        item_id = str(item.get("id", "")).strip().casefold()
        if not item_id or item_id in seen:
            duplicates.add(item_id or "<empty>")
        seen.add(item_id)
    return duplicates


def _runtime_evidence() -> dict[str, bool]:
    """Translate existing location provider evidence into provider slots.

    This function performs no network call. It only reads evidence already
    recorded by location_intelligence after genuine requests.
    """

    state = location_intelligence.status()
    return {
        "postcode": bool(state.get("postcode_provider_verified")),
        "geocoding": bool(state.get("global_provider_verified")),
        "weather": bool(state.get("weather_provider_verified")),
    }


def validate_provider_fabric(
    slots: Iterable[Mapping[str, Any]] = PROVIDER_SLOTS,
    adapters: Iterable[Mapping[str, Any]] = WIRED_ADAPTERS,
) -> dict[str, Any]:
    """Validate uniqueness, slot ownership and fail-closed mutation controls."""

    slot_list = tuple(slots)
    adapter_list = tuple(adapters)
    slot_duplicates = _duplicate_ids(slot_list)
    adapter_duplicates = _duplicate_ids(adapter_list)
    slot_ids = {str(item.get("id", "")).strip().casefold() for item in slot_list}
    unknown_slots = {
        str(item.get("slot_id", "")).strip().casefold()
        for item in adapter_list
        if str(item.get("slot_id", "")).strip().casefold() not in slot_ids
    }
    mutation_adapters = [item for item in adapter_list if item.get("mutation_enabled")]
    privileged_enabled = [
        key for key, enabled in CONSEQUENTIAL_CONTROLS.items() if bool(enabled)
    ]

    errors: list[str] = []
    if slot_duplicates:
        errors.append("Duplicate provider slot IDs: " + ", ".join(sorted(slot_duplicates)))
    if adapter_duplicates:
        errors.append("Duplicate provider adapter IDs: " + ", ".join(sorted(adapter_duplicates)))
    if unknown_slots:
        errors.append("Adapters reference unknown slots: " + ", ".join(sorted(unknown_slots)))
    if mutation_adapters:
        errors.append("Provider adapters may not enable mutation before approval")
    if privileged_enabled:
        errors.append("Consequential provider controls must remain fail-closed")
    if not HUMAN_APPROVAL_REQUIRED:
        errors.append("Human Authority approval must remain required")

    return {
        "passed": not errors,
        "errors": errors,
        "checks": {
            "slots": len(slot_list),
            "wired_adapters": len(adapter_list),
            "duplicate_slot_ids": len(slot_duplicates),
            "duplicate_adapter_ids": len(adapter_duplicates),
            "unknown_slot_links": len(unknown_slots),
            "mutation_adapters": len(mutation_adapters),
            "privileged_controls_enabled": len(privileged_enabled),
        },
    }


def _slot_projection() -> tuple[dict[str, Any], ...]:
    evidence = _runtime_evidence()
    adapters_by_slot: dict[str, list[dict[str, Any]]] = {}
    for adapter in WIRED_ADAPTERS:
        adapters_by_slot.setdefault(str(adapter["slot_id"]), []).append(dict(adapter))

    projected: list[dict[str, Any]] = []
    for slot in PROVIDER_SLOTS:
        slot_id = str(slot["id"])
        adapters = adapters_by_slot.get(slot_id, [])
        wired = bool(adapters)
        runtime_verified = bool(evidence.get(slot_id, False))
        if runtime_verified:
            status = "Runtime verified"
            state = "healthy"
        elif wired:
            status = "Wired · awaiting runtime evidence"
            state = "ready"
        else:
            status = "Provider required"
            state = "degraded"
        projected.append(
            {
                **dict(slot),
                "status": status,
                "state": state,
                "wired": wired,
                "runtime_verified": runtime_verified,
                "adapters": tuple(
                    {
                        "id": item["id"],
                        "name": item["name"],
                        "host": item["host"],
                        "mode": item["mode"],
                        "credential_required": item["credential_required"],
                    }
                    for item in adapters
                ),
            }
        )
    return tuple(projected)


def get_private_provider_fabric() -> dict[str, Any]:
    """Return the redacted Mission Control provider view.

    The projection deliberately contains no environment values, API keys,
    tokens, account identifiers or carrier profile data.
    """

    slots = _slot_projection()
    return {
        "name": "OAP Provider Fabric",
        "law": "Capability contract → provider adapter → evidence → approval → execution",
        "slots": slots,
        "validation": validate_provider_fabric(),
        "summary": {
            "slots": len(slots),
            "wired": sum(bool(item["wired"]) for item in slots),
            "runtime_verified": sum(bool(item["runtime_verified"]) for item in slots),
            "provider_required": sum(not bool(item["wired"]) for item in slots),
        },
        "execution": dict(CONSEQUENTIAL_CONTROLS),
        "human_authority_required": HUMAN_APPROVAL_REQUIRED,
        "principles": (
            "OAP owns the capability contract; providers remain replaceable adapters.",
            "No provider credential or customer/carrier identifier is exposed by status views.",
            "Configuration does not equal runtime proof.",
            "Read-only delivery may be verified independently from consequential execution.",
            "Payments, telecom provisioning and dispatch require compliance plus Human Authority approval.",
        ),
    }


def get_coarse_provider_status() -> dict[str, Any]:
    """Return a minimal status suitable for internal health aggregation."""

    fabric = get_private_provider_fabric()
    summary = fabric["summary"]
    return {
        "architecture_passed": bool(fabric["validation"]["passed"]),
        "slots": summary["slots"],
        "wired": summary["wired"],
        "runtime_verified": summary["runtime_verified"],
        "consequential_execution_enabled": any(CONSEQUENTIAL_CONTROLS.values()),
        "human_authority_required": HUMAN_APPROVAL_REQUIRED,
    }
