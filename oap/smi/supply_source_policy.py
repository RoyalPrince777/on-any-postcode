"""OAP-owned supply-source independence policy.

OAP Direct is the preferred first-party supply path. External travel suppliers
may accelerate inventory, but no single provider may become required for OAP
Travel to exist, reason, discover direct supply, or preserve its booking journey.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

SUPPLY_SOURCE_POLICY_REVISION = "2026-09-04-v1"
DIRECT_SOURCE_ID = "oap_direct"
EXTERNAL_SOURCE_CLASS = "replaceable_external_supply"


def source_priority(*, source_id: str, source_kind: str) -> int:
    """Return a stable preference class without inventing commercial quality.

    Direct supply wins only the source-independence tie-break. Price, suitability,
    availability and user requirements must still be compared by the caller.
    """

    normalized_id = str(source_id or "").strip().casefold()
    normalized_kind = str(source_kind or "").strip().casefold()
    if normalized_id == DIRECT_SOURCE_ID or normalized_kind == "oap_direct":
        return 0
    if normalized_kind in {"external", EXTERNAL_SOURCE_CLASS}:
        return 100
    return 200


def rank_comparable_sources(offers: Sequence[Mapping[str, Any]]) -> tuple[dict[str, Any], ...]:
    """Rank already-comparable offers by OAP source preference.

    This function must only receive offers that the caller has already determined
    are comparable for the user's requested category, dates and requirements. It
    never claims that a higher-priced direct offer is automatically better.
    """

    normalized: list[dict[str, Any]] = []
    for index, offer in enumerate(offers):
        item = dict(offer)
        item["source_priority"] = source_priority(
            source_id=str(item.get("source_id") or item.get("provider_id") or ""),
            source_kind=str(item.get("source_kind") or ""),
        )
        item["original_order"] = index
        normalized.append(item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (int(item["source_priority"]), int(item["original_order"])),
        )
    )


def status() -> dict[str, Any]:
    """Return the locked War Room supply-independence policy."""

    return {
        "component": "OAP Supply Source Policy",
        "revision": SUPPLY_SOURCE_POLICY_REVISION,
        "policy_ready": True,
        "oap_direct_preferred_when_comparable": True,
        "external_suppliers_allowed": True,
        "external_suppliers_optional": True,
        "single_external_provider_dependency_allowed": False,
        "booking_com_required": False,
        "preferred_source_order": (DIRECT_SOURCE_ID, EXTERNAL_SOURCE_CLASS),
        "provider_brand_controls_oap_experience": False,
        "external_provider_authority": False,
        "creates_intelligence_worlds": False,
        "creates_agents": False,
        "creates_brain": False,
        "guardian_gate_required": True,
        "human_authority_final": True,
        "truth_boundary": (
            "OAP Direct is preferred when offers are otherwise comparable. External "
            "suppliers can expand inventory but remain replaceable. No provider is "
            "required for OAP identity, intelligence, governance or first-party supply."
        ),
    }
