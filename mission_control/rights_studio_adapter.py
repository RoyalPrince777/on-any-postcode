"""OAP Studio artifact adapter for the canonical Rights Core."""
from __future__ import annotations

import json
from typing import Any
from uuid import UUID, uuid5

from . import rights_core

NAMESPACE = UUID("7b5de1f1-a23b-4bd3-8507-7ec95f02cc74")


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
        "source_reference": f"oap:studio:{record.get('request_id')}" if record.get("request_id") else "oap:studio:generation",
        "parent_asset_id": record.get("parent_asset_id"),
    })


def evaluate_studio_publish(
    *, record: object, request: object, evidence_hashes: object, territories: object,
    permitted_uses: object = ("publish",), permitted_channels: object = ("OAP Media",),
    grantor_reference: object = "oap:studio:owner",
    authority_verified: bool = False, authority_receipt_hash: object = None,
    human_approved: bool = False, human_approval_receipt_hash: object = None,
    derivatives_allowed: bool = False, commercial_use_allowed: bool = False,
    attribution_required: bool = False, valid_from: object = None,
    valid_until: object = None, lineage_assets: object = (),
) -> dict[str, Any]:
    asset = canonical_studio_asset(record)
    scope = json.dumps({
        "asset": asset["asset_id"], "uses": sorted(map(str, permitted_uses)),
        "territories": sorted(map(str, territories)),
        "channels": sorted(map(str, permitted_channels)),
        "valid_from": valid_from, "valid_until": valid_until,
    }, sort_keys=True)
    grant = rights_core.canonical_grant({
        "grant_id": str(uuid5(NAMESPACE, scope)),
        "asset_id": asset["asset_id"],
        "owner_identity_id": asset["owner_identity_id"],
        "grantor_reference": grantor_reference,
        "right_type": "distribution",
        "permitted_uses": permitted_uses,
        "territories": territories,
        "permitted_channels": permitted_channels,
        "valid_from": valid_from,
        "valid_until": valid_until,
        "derivatives_allowed": derivatives_allowed,
        "commercial_use_allowed": commercial_use_allowed,
        "attribution_required": attribution_required,
        "evidence_hashes": evidence_hashes,
        "authority_verified": authority_verified,
        "authority_receipt_hash": authority_receipt_hash,
        "human_approved": human_approved,
        "human_approval_receipt_hash": human_approval_receipt_hash,
        "revoked": False,
    })
    decision = rights_core.evaluate_use(
        asset=asset, grants=[grant], request=request, lineage_assets=lineage_assets
    )
    return {
        **decision,
        "studio_artifact_indexed": True,
        "generation_proof_is_not_rights_proof": True,
        "public_publish_enabled": False,
    }


def status() -> dict[str, Any]:
    return {
        "component": "OAP Studio to Rights Core adapter",
        "founder_asset_contract_reused": True,
        "stable_grant_identity": True,
        "owner_scope_bound": True,
        "channel_scope_bound": True,
        "generation_proof_is_not_rights_proof": True,
        "rights_core_decision_reused": True,
        "public_publish_enabled": False,
    }
