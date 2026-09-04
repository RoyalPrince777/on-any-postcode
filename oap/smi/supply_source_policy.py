"""OAP-owned travel source independence policy.

OAP Direct is the persisted first-party supply path. External travel services may
be queried as optional reference data, but they do not become OAP partners,
persisted inventory or booking execution dependencies.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

SUPPLY_SOURCE_POLICY_REVISION = "2026-09-04-v2"
DIRECT_SOURCE_ID = "oap_direct"
EXTERNAL_SOURCE_CLASS = "external_lookup_only"


def source_priority(*, source_id: str, source_kind: str) -> int:
    """Return a stable preference class without inventing commercial quality."""

    normalized_id = str(source_id or "").strip().casefold()
    normalized_kind = str(source_kind or "").strip().casefold()
    if normalized_id == DIRECT_SOURCE_ID or normalized_kind == "oap_direct":
        return 0
    if normalized_kind in {"external", EXTERNAL_SOURCE_CLASS, "external_lookup"}:
        return 100
    return 200


def rank_comparable_sources(
    offers: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], ...]:
    """Rank already-comparable reference results by OAP source preference."""

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
    """Return the locked War Room source-independence policy."""

    return {
        "component": "OAP Supply Source Policy",
        "revision": SUPPLY_SOURCE_POLICY_REVISION,
        "policy_ready": True,
        "oap_direct_preferred_when_comparable": True,
        "external_suppliers_allowed": False,
        "external_suppliers_optional": True,
        "external_lookup_allowed": True,
        "external_lookup_persisted": False,
        "single_external_provider_dependency_allowed": False,
        "booking_com_required": False,
        "booking_com_partner": False,
        "preferred_source_order": (DIRECT_SOURCE_ID,),
        "provider_brand_controls_oap_experience": False,
        "external_provider_authority": False,
        "creates_intelligence_worlds": False,
        "creates_agents": False,
        "creates_brain": False,
        "guardian_gate_required": True,
        "human_authority_final": True,
        "truth_boundary": (
            "OAP Direct is the only persisted travel supply lane. External travel sites "
            "may be queried on demand for reference, but their results are not imported "
            "as OAP inventory and they never receive OAP booking or platform authority."
        ),
    }
