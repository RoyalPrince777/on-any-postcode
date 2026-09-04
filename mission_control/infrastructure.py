"""Canonical, read-only OAP Infrastructure scope and public projection.

Infrastructure owns exactly Maps, Weather, eSIM and Connectivity. Related
Navigation, Mobility and shared Mission Control health remain outside that
ownership boundary so this UI cannot become a duplicate routing, transport or
operations engine. Public status is evidence-driven. The OAP Live Signal
language and Infrastructure Intelligence are first-party OAP capabilities;
outside sources may contribute replaceable evidence only and never OAP identity,
authority or execution rights.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any

from . import infrastructure_intelligence, live_signals, location_intelligence

LOCKED_INFRASTRUCTURE_MODULES: tuple[dict[str, str], ...] = (
    {
        "id": "maps",
        "name": "Maps",
        "purpose": "Postcode places, local landmarks and map context.",
        "status": "Configured; runtime proof pending",
        "state": "degraded",
        "readiness": "Bounded location lookup configured",
        "data": "No successful bounded location evidence observed in this process",
        "boundary": (
            "Provides place context only; it does not create a Navigation or "
            "Mobility engine."
        ),
    },
    {
        "id": "weather",
        "name": "Weather",
        "purpose": "Weather records and local condition awareness.",
        "status": "Configured; runtime proof pending",
        "state": "degraded",
        "readiness": "Bounded weather lookup configured",
        "data": "No successful bounded weather evidence observed in this process",
        "boundary": (
            "Shows bounded weather results only; consequential alerts or external "
            "operations remain unavailable."
        ),
    },
    {
        "id": "esim",
        "name": "eSIM",
        "purpose": "Telecom and eSIM service-readiness records.",
        "status": "OAP carrier capability required",
        "state": "degraded",
        "readiness": "Activation unavailable",
        "data": "No lawful first-party carrier capability proven",
        "boundary": (
            "Readiness records only; purchase, provisioning and activation "
            "controls are not registered."
        ),
    },
    {
        "id": "connectivity",
        "name": "Connectivity",
        "purpose": "Coarse connection availability and reachability awareness.",
        "status": "Not connected",
        "state": "degraded",
        "readiness": "Status-only shell ready",
        "data": "No first-party connectivity evidence source configured",
        "boundary": (
            "No network control, credentials, Wi-Fi or satellite service is "
            "asserted by this interface."
        ),
    },
)

LOCKED_MODULE_IDS = tuple(module["id"] for module in LOCKED_INFRASTRUCTURE_MODULES)
LOCKED_MODULE_NAMES = tuple(
    module["name"] for module in LOCKED_INFRASTRUCTURE_MODULES
)

RELATED_SYSTEM_BOUNDARIES: tuple[dict[str, str], ...] = (
    {
        "id": "navigation",
        "name": "Navigation",
        "owner": "Related hub",
        "relationship": (
            "May consume approved Maps context; routing remains outside this "
            "Infrastructure registry."
        ),
    },
    {
        "id": "mobility",
        "name": "Mobility",
        "owner": "Separate OAP layer",
        "relationship": (
            "Owns Deliveries, Transport and Travel. Infrastructure does not "
            "duplicate those services."
        ),
    },
    {
        "id": "system_health",
        "name": "System health",
        "owner": "Shared Mission Control widget",
        "relationship": (
            "Infrastructure may display the coarse shared projection but does "
            "not own or replace health monitoring."
        ),
    },
    {
        "id": "operations",
        "name": "Operations",
        "owner": "Separate OAP system",
        "relationship": (
            "Execution and operational controls stay outside this read-only "
            "dashboard."
        ),
    },
)

FIRST_PARTY_BUILD_GATES: tuple[dict[str, str], ...] = (
    {
        "title": "Build OAP-owned Maps and Weather evidence path",
        "description": (
            "Keep OAP ownership of the map, weather, classification, state and UI layers. "
            "Any outside data used for evidence must remain replaceable data only and may "
            "not become OAP identity or authority."
        ),
        "status": "Requires human approval",
    },
    {
        "title": "Build OAP eSIM carrier readiness path",
        "description": (
            "Do not expose activation until OAP can prove a lawful carrier capability, "
            "identity checks, consent, billing boundaries and Guardian review."
        ),
        "status": "Requires human approval",
    },
    {
        "title": "Build OAP Connectivity evidence path",
        "description": (
            "Create first-party connection-state, reachability and continuity evidence. "
            "Outside network data may be validation input only and cannot control OAP."
        ),
        "status": "Requires human approval",
    },
)

# Compatibility name retained for existing callers; the contents are now explicitly
# first-party build gates rather than provider-control proposals.
PROPOSED_CONNECTIONS = FIRST_PARTY_BUILD_GATES

FIRST_PARTY_POLICY = {
    "owner": "ON ANY POSTCODE",
    "oap_owns_system": True,
    "oap_owns_intelligence": True,
    "oap_owns_signal_language": True,
    "oap_owns_health_model": True,
    "external_identity_allowed": False,
    "external_authority_allowed": False,
    "external_source_role": "replaceable_data_only_when_needed",
    "human_authority_final": True,
}


def _normalise(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def _duplicates(values: Iterable[str]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return duplicates


def _runtime_modules() -> tuple[list[dict[str, Any]], dict[str, object]]:
    """Overlay runtime delivery evidence without performing network I/O."""

    evidence = location_intelligence.status()
    maps_verified = bool(
        evidence.get("postcode_provider_verified")
        or evidence.get("global_provider_verified")
    )
    weather_verified = bool(evidence.get("weather_provider_verified"))
    modules: list[dict[str, Any]] = [dict(module) for module in LOCKED_INFRASTRUCTURE_MODULES]

    for module in modules:
        if module["id"] == "maps" and maps_verified:
            module.update(
                status="Runtime verified",
                state="healthy",
                readiness="Location lookup ready",
                data="Successful bounded location evidence observed",
            )
        elif module["id"] == "weather" and weather_verified:
            module.update(
                status="Runtime verified",
                state="healthy",
                readiness="Weather lookup ready",
                data="Successful bounded weather evidence observed",
            )
        module["signal"] = live_signals.resolve_runtime_signal(
            module.get("state"), status=module.get("status")
        )

    public_evidence: dict[str, object] = {
        "maps_runtime_verified": maps_verified,
        "weather_runtime_verified": weather_verified,
        "spatial_contract": str(evidence.get("spatial_contract") or ""),
        "network_probe_on_get": False,
        "evidence_mode": "observed_delivery",
        "outside_source_is_authority": False,
    }
    return modules, public_evidence


def validate_infrastructure_scope(
    modules: Iterable[Mapping[str, Any]] = LOCKED_INFRASTRUCTURE_MODULES,
    related_systems: Iterable[Mapping[str, Any]] = RELATED_SYSTEM_BOUNDARIES,
) -> dict[str, Any]:
    """Detect duplicate, overlapping or renamed Infrastructure ownership."""

    module_list = tuple(modules)
    related_list = tuple(related_systems)
    ids = [str(module.get("id", "")).strip().casefold() for module in module_list]
    names = [_normalise(str(module.get("name", ""))) for module in module_list]
    related_ids = {
        str(system.get("id", "")).strip().casefold() for system in related_list
    }
    related_names = {
        _normalise(str(system.get("name", ""))) for system in related_list
    }

    duplicate_ids = _duplicates(ids)
    duplicate_names = _duplicates(names)
    overlaps = (set(ids) & related_ids) | (set(names) & related_names)
    expected_ids = set(LOCKED_MODULE_IDS)
    missing = expected_ids - set(ids)
    unexpected = set(ids) - expected_ids
    mutation_controls = sum(
        bool(module.get("mutation_enabled")) for module in module_list
    )

    errors: list[str] = []
    if duplicate_ids:
        errors.append(
            "Duplicate Infrastructure module IDs: " + ", ".join(sorted(duplicate_ids))
        )
    if duplicate_names:
        errors.append(
            "Duplicate Infrastructure module names: "
            + ", ".join(sorted(duplicate_names))
        )
    if overlaps:
        errors.append(
            "Infrastructure ownership overlaps a separate system: "
            + ", ".join(sorted(overlaps))
        )
    if missing:
        errors.append(
            "Locked Infrastructure modules missing: " + ", ".join(sorted(missing))
        )
    if unexpected:
        errors.append(
            "Unapproved Infrastructure modules present: "
            + ", ".join(sorted(unexpected))
        )
    if mutation_controls:
        errors.append("Infrastructure mutation controls must remain disabled")

    return {
        "passed": not errors,
        "errors": errors,
        "checks": {
            "canonical_modules": len(module_list),
            "duplicate_ids": len(duplicate_ids),
            "naming_conflicts": len(duplicate_names),
            "ownership_overlaps": len(overlaps),
            "mutation_controls": mutation_controls,
        },
    }


def get_public_infrastructure() -> dict[str, Any]:
    """Return an allowlisted, non-operational Infrastructure projection."""

    modules, runtime_evidence = _runtime_modules()
    projection: dict[str, Any] = {
        "modules": modules,
        "runtime_evidence": runtime_evidence,
        "related_systems": [dict(system) for system in RELATED_SYSTEM_BOUNDARIES],
        "proposed_connections": [dict(item) for item in FIRST_PARTY_BUILD_GATES],
        "first_party_build_gates": [dict(item) for item in FIRST_PARTY_BUILD_GATES],
        "first_party_policy": dict(FIRST_PARTY_POLICY),
        "signal_legend": live_signals.public_legend(),
        "validation": validate_infrastructure_scope(),
        "operating_mode": {
            "label": "Read-only awareness",
            "message": "No activation, infrastructure mutation or network changes are enabled.",
        },
        "human_authority": {
            "status": "Final approval required",
            "message": (
                "Every connection, activation or operational control requires "
                "recorded Human Authority approval."
            ),
        },
    }
    projection["intelligence"] = infrastructure_intelligence.review(projection)
    return projection
