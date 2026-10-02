"""Whole-OAP Distribution 700-check governance protocol.

This module unifies existing Distribution Intelligence, Market, Media, Music,
supplier/fulfilment, creator and local/post logistics into one bounded review
contract. It performs no external publishing, payment, dispatch, carrier handoff
or provider execution.

The 700 protocol is 7 distribution lanes x 10 intelligence lenses x 10 evidence
tests = 700 deterministic checks inside one mission, not 700 workflow stages.
"""
from __future__ import annotations

from typing import Any

from . import distribution_intelligence

NAME = "OAP Distribution 700"
SCOPE = "whole_oap_world_distribution"

DISTRIBUTION_LANES: tuple[str, ...] = (
    "music",
    "tv_media",
    "sport",
    "clothing",
    "creator",
    "market_fulfilment",
    "local_post",
)

INTELLIGENCE_LENSES: tuple[str, ...] = (
    "truth",
    "rights",
    "readiness",
    "routing",
    "security",
    "commercial_value",
    "resilience",
    "dependency",
    "recovery",
    "human_authority",
)

EVIDENCE_TESTS: tuple[str, ...] = (
    "owner_or_authority",
    "rights_or_permission",
    "source_reference",
    "timestamp_or_version",
    "functional_test",
    "integration_test",
    "destination_receipt",
    "permission_boundary",
    "rollback_or_recovery",
    "human_approval",
)

TOTAL_PROTOCOL_CHECKS = (
    len(DISTRIBUTION_LANES)
    * len(INTELLIGENCE_LENSES)
    * len(EVIDENCE_TESTS)
)

LANE_POLICIES: dict[str, dict[str, Any]] = {
    "music": {
        "oap_first_party_primary": True,
        "rights_evidence_required": True,
        "distribution_receipt_required": True,
        "external_platform_assumed": False,
    },
    "tv_media": {
        "rights_evidence_required": True,
        "broadcast_or_stream_permission_required": True,
        "oap_owned_or_licensed_content_only": True,
        "external_delivery_assumed": False,
    },
    "sport": {
        "scores_stats_allowed_when_source_backed": True,
        "footage_rights_required": True,
        "competition_data_rights_checked": True,
        "external_broadcast_assumed": False,
    },
    "clothing": {
        "supplier_or_production_evidence_required": True,
        "quality_evidence_required": True,
        "shipping_evidence_required": True,
        "returns_evidence_required": True,
    },
    "creator": {
        "creator_ownership_or_license_required": True,
        "product_provenance_required": True,
        "market_handoff_required": True,
        "external_provider_assumed": False,
    },
    "market_fulfilment": {
        "canonical_order_required": True,
        "supplier_ready_required": True,
        "dispatch_receipt_required_for_dispatch_claim": True,
        "carrier_handoff_receipt_required_for_handoff_claim": True,
    },
    "local_post": {
        "postcode_route_evidence_required": True,
        "parcel_or_booking_identity_required": True,
        "owner_scope_required": True,
        "recovery_readback_required": True,
    },
}


def protocol_cells() -> tuple[tuple[str, str, str], ...]:
    """Return the deterministic 700-cell Distribution matrix."""

    return tuple(
        (lane, lens, evidence_test)
        for lane in DISTRIBUTION_LANES
        for lens in INTELLIGENCE_LENSES
        for evidence_test in EVIDENCE_TESTS
    )


def lane_plan(lane: object) -> dict[str, Any]:
    safe_lane = str(lane or "").strip().lower()
    if safe_lane not in LANE_POLICIES:
        raise ValueError(f"Unsupported distribution lane: {lane}")
    base = distribution_intelligence.status()
    return {
        "name": NAME,
        "scope": SCOPE,
        "lane": safe_lane,
        "policy": dict(LANE_POLICIES[safe_lane]),
        "protocol_check_count": TOTAL_PROTOCOL_CHECKS,
        "existing_distribution_intelligence_reused": True,
        "canonical_world_id": base["canonical_world_id"],
        "rights_proof_required": True,
        "destination_receipt_required": True,
        "guardian_required": True,
        "green_gate_required": True,
        "founder_final_required": True,
        "external_execution_enabled": False,
        "publishing_authority_granted": False,
        "payment_authority_granted": False,
        "dispatch_authority_granted": False,
        "carrier_handoff_authority_granted": False,
        "human_authority_final": True,
        "full_green": False,
    }


def evaluate_lane_evidence(
    lane: object,
    evidence: object,
) -> dict[str, Any]:
    """Evaluate one bounded lane evidence packet without executing Distribution."""

    plan = lane_plan(lane)
    data = evidence if isinstance(evidence, dict) else {}
    results = {
        evidence_test: bool(data.get(evidence_test))
        for evidence_test in EVIDENCE_TESTS
    }
    passed = sum(1 for value in results.values() if value)
    ready = passed == len(EVIDENCE_TESTS)
    return {
        "lane": plan["lane"],
        "checks": results,
        "passed": passed,
        "required": len(EVIDENCE_TESTS),
        "evidence_ready": ready,
        "state": "PROVEN" if ready else "INCOMPLETE",
        "external_execution_enabled": False,
        "public_delivery_claim_allowed": ready
        and bool(data.get("authenticated_destination_adapter"))
        and bool(data.get("destination_delivery_receipt")),
        "human_authority_final": True,
        "founder_final_required": True,
    }


def status() -> dict[str, Any]:
    base = distribution_intelligence.status()
    cells = protocol_cells()
    return {
        "name": NAME,
        "scope": SCOPE,
        "distribution_lane_count": len(DISTRIBUTION_LANES),
        "intelligence_lens_count": len(INTELLIGENCE_LENSES),
        "evidence_test_count": len(EVIDENCE_TESTS),
        "protocol_check_count": len(cells),
        "protocol_is_checks_not_stages": True,
        "unique_protocol_cells": len(set(cells)),
        "lanes": DISTRIBUTION_LANES,
        "lane_policies": {key: dict(value) for key, value in LANE_POLICIES.items()},
        "existing_distribution_intelligence_reused": True,
        "canonical_world_id": base["canonical_world_id"],
        "canonical_world_name": base["canonical_world_name"],
        "external_distribution_state": base["external_distribution_state"],
        "rights_proof_required": True,
        "destination_receipt_required": True,
        "external_execution_enabled": False,
        "publishing_authority_granted": False,
        "payment_authority_granted": False,
        "dispatch_authority_granted": False,
        "carrier_handoff_authority_granted": False,
        "human_authority_final": True,
        "full_green": False,
        "no_fake_green": True,
    }
