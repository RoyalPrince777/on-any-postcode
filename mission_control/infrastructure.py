"""Canonical, read-only OAP Infrastructure scope and public projection.

Infrastructure owns exactly Maps, Weather, eSIM and Connectivity. Related
Navigation, Mobility and shared Mission Control health remain outside that
ownership boundary so this UI cannot become a duplicate routing, transport or
operations engine. Nothing in this module probes a network, activates a
service, persists state or exposes credentials.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any

from oap.contracts import IdentityRecord

from .db import db_status

LOCKED_INFRASTRUCTURE_MODULES: tuple[dict[str, str], ...] = (
    {
        "id": "maps",
        "name": "Maps",
        "purpose": "Postcode places, local landmarks and map context.",
        "status": "Not connected",
        "state": "degraded",
        "readiness": "Read-only shell ready",
        "data": "No map provider configured",
        "boundary": (
            "Provides place context only; it does not create a Navigation or "
            "Mobility engine."
        ),
    },
    {
        "id": "weather",
        "name": "Weather",
        "purpose": "Weather records and local condition awareness.",
        "status": "Not connected",
        "state": "degraded",
        "readiness": "Read-only shell ready",
        "data": "No live weather provider configured",
        "boundary": (
            "Shows approved weather records only; alerts and provider calls "
            "remain unavailable."
        ),
    },
    {
        "id": "esim",
        "name": "eSIM",
        "purpose": "Telecom and eSIM service-readiness records.",
        "status": "Provider required",
        "state": "degraded",
        "readiness": "Activation unavailable",
        "data": "No lawful telecom provider approved",
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
        "data": "No connectivity source configured",
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

PROPOSED_CONNECTIONS: tuple[dict[str, str], ...] = (
    {
        "title": "Connect Maps and Weather providers",
        "description": (
            "Select licensed data sources, privacy rules and postcode-level "
            "display limits before any live provider integration."
        ),
        "status": "Requires human approval",
    },
    {
        "title": "Approve an eSIM service pathway",
        "description": (
            "Confirm a lawful telecom partner, Identity checks, consent, "
            "billing boundaries and Guardian review before activation exists."
        ),
        "status": "Requires human approval",
    },
    {
        "title": "Define Connectivity integrations",
        "description": (
            "Approve each provider-backed network source before adding Wi-Fi, "
            "carrier or satellite status beyond this empty shell."
        ),
        "status": "Requires human approval",
    },
)


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
        errors.append("Locked Infrastructure modules missing: " + ", ".join(sorted(missing)))
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

    return {
        "visibility": "public",
        "modules": [dict(module) for module in LOCKED_INFRASTRUCTURE_MODULES],
        "related_systems": [dict(system) for system in RELATED_SYSTEM_BOUNDARIES],
        "proposed_connections": [dict(item) for item in PROPOSED_CONNECTIONS],
        "validation": validate_infrastructure_scope(),
        "operating_mode": {
            "label": "Read-only awareness",
            "message": "No provider calls, activation or network changes are enabled.",
        },
        "human_authority": {
            "status": "Final approval required",
            "message": (
                "Every provider connection or operational control requires "
                "recorded Human Authority approval."
            ),
        },
    }


def get_private_infrastructure(identity: IdentityRecord) -> dict[str, Any]:
    """Return private readiness only to authorized level-zero Human Authority."""

    if (
        identity.status != "ACTIVE"
        or identity.identity_type != "human_authority"
        or identity.authority_level != 0
        or "VIEW_SOVEREIGN_INFRASTRUCTURE" not in identity.permissions
    ):
        raise PermissionError(
            "Private Infrastructure requires authorized Human Authority"
        )

    database = db_status()
    public = get_public_infrastructure()
    return {
        "visibility": "private",
        "identity": {
            "identity_id": identity.identity_id,
            "authority_level": identity.authority_level,
        },
        "modules": public["modules"],
        "boundaries": public["related_systems"],
        "runtime": {
            "database_backend": database["backend"],
            "database_initialized": bool(database["initialized"]),
            "maps_provider": "unassigned",
            "weather_provider": "unassigned",
            "esim_provider": "unassigned",
            "connectivity_provider": "unassigned",
            "provider_calls_enabled": False,
            "network_mutations_enabled": False,
            "credentials_exposed": False,
        },
        "activation_gates": public["proposed_connections"],
        "human_authority": public["human_authority"],
    }
