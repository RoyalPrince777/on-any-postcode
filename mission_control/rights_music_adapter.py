"""OAP Music evidence adapter for the canonical Rights Core."""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any
from uuid import UUID, uuid5

from . import music_evidence, rights_core

NAMESPACE = UUID("c6dd8df0-6120-4f72-9c7f-8a8ef2b2ed41")


def _stable_grant_id(asset_id: str, scope: dict[str, Any]) -> str:
    payload = json.dumps({"asset_id": asset_id, **scope}, sort_keys=True, default=str)
    return str(uuid5(NAMESPACE, payload))


def project_music_release(
    *,
    asset: object,
    receipts: object,
    permitted_uses: object,
    territories: object,
    permitted_channels: object = ("OAP Music",),
    right_type: object = "stream",
    grantor_reference: object = "oap:music:evidence",
    valid_from: object = None,
    valid_until: object = None,
    derivatives_allowed: bool = False,
    commercial_use_allowed: bool = False,
    attribution_required: bool = True,
    authority_verified: bool = False,
    authority_receipt_hash: object = None,
    human_approved: bool = False,
    human_approval_receipt_hash: object = None,
) -> dict[str, Any]:
    canonical_asset = rights_core.canonical_asset(asset)
    rows = receipts if isinstance(receipts, list) else []
    chain = music_evidence.verify_receipt_chain(rows)
    gate = music_evidence.private_distribution_gate(
        rows,
        recovery_readback_proven=any(
            isinstance(row, Mapping) and row.get("evidence_kind") == "recovery_readback"
            for row in rows
        ),
    )
    if not chain["chain_verified"]:
        raise ValueError("music_evidence_chain_invalid")
    if gate["missing_evidence_kinds"]:
        raise ValueError("music_evidence_incomplete")

    evidence_hashes = sorted({
        str(row["evidence_sha256"])
        for row in rows
        if isinstance(row, Mapping) and row.get("evidence_sha256")
    })
    if not evidence_hashes:
        raise ValueError("music_evidence_hashes_missing")

    territory_values = list(territories) if isinstance(territories, (list, tuple, set, frozenset)) else []
    use_values = list(permitted_uses) if isinstance(permitted_uses, (list, tuple, set, frozenset)) else []
    channel_values = list(permitted_channels) if isinstance(permitted_channels, (list, tuple, set, frozenset)) else []
    scope = {
        "right_type": right_type,
        "permitted_uses": sorted(map(str, use_values)),
        "territories": sorted(map(str, territory_values)),
        "permitted_channels": sorted(map(str, channel_values)),
        "valid_from": valid_from,
        "valid_until": valid_until,
    }
    grant = rights_core.canonical_grant({
        "grant_id": _stable_grant_id(canonical_asset["asset_id"], scope),
        "asset_id": canonical_asset["asset_id"],
        "owner_identity_id": canonical_asset["owner_identity_id"],
        "grantor_reference": grantor_reference,
        "right_type": right_type,
        "permitted_uses": use_values,
        "territories": territory_values,
        "permitted_channels": channel_values,
        "valid_from": valid_from,
        "valid_until": valid_until,
        "derivatives_allowed": derivatives_allowed,
        "commercial_use_allowed": commercial_use_allowed,
        "attribution_required": attribution_required,
        "evidence_hashes": evidence_hashes,
        "authority_verified": bool(authority_verified),
        "authority_receipt_hash": authority_receipt_hash,
        "human_approved": bool(human_approved),
        "human_approval_receipt_hash": human_approval_receipt_hash,
        "revoked": False,
    })
    return {
        "asset": canonical_asset,
        "grant": grant,
        "chain_head_hash": chain["head_hash"],
        "evidence_receipt_count": chain["receipt_count"],
        "private_music_handoff_ready": bool(gate["private_handoff_ready"]),
        "rights_verified_by_software": False,
        "authority_inferred": False,
        "human_approval_inferred": False,
        "public_distribution_enabled": False,
    }


def evaluate_music_use(*, asset: object, receipts: object, request: object,
                       permitted_uses: object, territories: object,
                       authority_verified: bool = False,
                       authority_receipt_hash: object = None,
                       human_approved: bool = False,
                       human_approval_receipt_hash: object = None,
                       **grant_scope: Any) -> dict[str, Any]:
    projection = project_music_release(
        asset=asset, receipts=receipts, permitted_uses=permitted_uses,
        territories=territories, authority_verified=authority_verified,
        authority_receipt_hash=authority_receipt_hash,
        human_approved=human_approved,
        human_approval_receipt_hash=human_approval_receipt_hash,
        **grant_scope,
    )
    decision = rights_core.evaluate_use(
        asset=projection["asset"], grants=[projection["grant"]], request=request
    )
    return {
        **decision,
        "music_evidence_chain_head": projection["chain_head_hash"],
        "music_evidence_receipt_count": projection["evidence_receipt_count"],
        "public_distribution_enabled": False,
    }


def status() -> dict[str, Any]:
    return {
        "component": "OAP Music → Rights Core adapter",
        "existing_music_evidence_reused": True,
        "stable_grant_identity": True,
        "owner_scope_bound": True,
        "channel_scope_bound": True,
        "rights_core_decision_reused": True,
        "authority_inferred": False,
        "human_approval_inferred": False,
        "public_distribution_enabled": False,
    }
