"""OAP Studio artifact adapter for the canonical Rights Core.

Studio may prove that an artifact was generated and indexed, but generation is
not ownership or publication permission. This adapter maps a durable Founder
asset record into the shared rights contract and requires explicit evidence,
authority verification, and human approval before an ALLOW decision.
"""
from __future__ import annotations

from typing import Any
from uuid import uuid4

from . import rights_core


def canonical_studio_asset(record: object) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise TypeError("invalid_studio_asset")
    if str(record.get("source") or "") != "studio_generation":
        raise ValueError("studio_asset_source_required")
    return rights_core.canonical_asset({
        "asset_id": record.get("asset_id"),
        "owner_identity_id": record.get("identity_id"),
        "kind": record.get("asset_kind") or "studio_asset",
        "content_sha256": record.get("content_sha256") or record.get("sha256"),
        "source_reference": (
            f"oap:studio:{record.get('request_id')}"
            if record.get("request_id")
            else "oap:studio:generation"
        ),
        "parent_asset_id": record.get("parent_asset_id"),
    })


def evaluate_studio_publish(
    *,
    record: object,
    request: object,
    evidence_hashes: object,
    territories: object,
    permitted_uses: object = ("publish",),
    grantor_reference: object = "oap:studio:owner",
    authority_verified: bool = False,
    human_approved: bool = False,
    derivatives_allowed: bool = False,
    commercial_use_allowed: bool = False,
    attribution_required: bool = False,
    valid_from: object = None,
    valid_until: object = None,
    lineage_assets: object = (),
) -> dict[str, Any]:
    asset = canonical_studio_asset(record)
    grant = rights_core.canonical_grant({
        "grant_id": str(uuid4()),
        "asset_id": asset["asset_id"],
        "grantor_reference": grantor_reference,
        "right_type": "distribution",
        "permitted_uses": permitted_uses,
        "territories": territories,
        "valid_from": valid_from,
        "valid_until": valid_until,
        "derivatives_allowed": derivatives_allowed,
        "commercial_use_allowed": commercial_use_allowed,
        "attribution_required": attribution_required,
        "evidence_hashes": evidence_hashes,
        "authority_verified": authority_verified,
        "human_approved": human_approved,
        "revoked": False,
    })
    decision = rights_core.evaluate_use(
        asset=asset,
        grants=[grant],
        request=request,
        lineage_assets=lineage_assets,
    )
    return {
        **decision,
        "studio_artifact_indexed": True,
        "generation_proof_is_not_rights_proof": True,
        "public_publish_enabled": False,
    }


def status() -> dict[str, Any]:
    return {
        "component": "OAP Studio → Rights Core adapter",
        "founder_asset_contract_reused": True,
        "generation_proof_is_not_rights_proof": True,
        "rights_core_decision_reused": True,
        "public_publish_enabled": False,
    }
