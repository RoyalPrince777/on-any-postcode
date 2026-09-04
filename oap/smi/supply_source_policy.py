"""OAP-owned supply-source independence policy.

The public OAP Travel catalogue is OAP Direct only. External marketplace data may
be fetched as research context, but it does not become a supplier relationship,
Partner Supply, OAP inventory or booking authority.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

SUPPLY_SOURCE_POLICY_REVISION = "2026-09-04-v2"
DIRECT_SOURCE_ID = "oap_direct"
EXTERNAL_RESEARCH_CLASS = "external_research"


def source_priority(*, source_id: str, source_kind: str) -> int:
    normalized_id = str(source_id or "").strip().casefold()
    normalized_kind = str(source_kind or "").strip().casefold()
    if normalized_id == DIRECT_SOURCE_ID or normalized_kind == "oap_direct":
        return 0
    if normalized_kind in {"external", EXTERNAL_RESEARCH_CLASS}:
        return 100
    return 200


def rank_comparable_sources(offers: Sequence[Mapping[str, Any]]) -> tuple[dict[str, Any], ...]:
    """Rank already-comparable observations without promoting research to inventory."""

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
    return {
        "component": "OAP Supply Source Policy",
        "revision": SUPPLY_SOURCE_POLICY_REVISION,
        "policy_ready": True,
        "oap_direct_preferred_when_comparable": True,
        "external_supplier_catalogue_allowed": False,
        "external_data_fetch_allowed": True,
        "external_data_is_research_only": True,
        "single_external_provider_dependency_allowed": False,
        "preferred_source_order": (DIRECT_SOURCE_ID,),
        "provider_brand_controls_oap_experience": False,
        "external_provider_authority": False,
        "creates_intelligence_worlds": False,
        "creates_agents": False,
        "creates_brain": False,
        "guardian_gate_required": True,
        "human_authority_final": True,
        "truth_boundary": (
            "Only directly onboarded Certified OAP Suppliers enter OAP Travel. External "
            "marketplace information may be fetched for research/comparison but stays "
            "outside the OAP catalogue, reservation ledger and payment path."
        ),
    }
