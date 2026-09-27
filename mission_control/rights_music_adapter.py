"""OAP Music evidence adapter for the canonical Rights Core.

This module preserves the existing OAP Music evidence chain. It only projects
verified receipt-chain facts into the shared Rights Core contract. It never
upgrades evidence presence into legal verification, licensor authority, or
human approval.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from uuid import uuid4

from . import music_evidence, rights_core


def project_music_release(
    *,
    asset: object,
    receipts: object,
    permitted_uses: object,
    territories: object,
    right_type: object = "stream",
    grantor_reference: object = "oap:music:evidence",
    valid_from: object = None,
    valid_until: object = None,
    derivatives_allowed: bool = False,
    commercial_use_allowed: bool = False,
    attribution_required: bool = True,
    authority_verified: bool = False,
    human_approved: bool = False,
) -> dict[str, Any]:
    """Project one music evidence chain into one scoped Rights Core grant.

    A valid receipt chain and the complete private evidence set are required.
    The adapter intentionally keeps authority and approval explicit; receipt
    presence alone cannot set either flag to true.
    """
    canonical_asset = rights_core.canonical_asset(asset)
    rows = receipts if isinstance(receipts, list) else []
    chain = music_evidence.verify_receipt_chain(rows)
    gate = music_evidence.private_distribution_gate(
        rows,
        recovery_readback_proven=any(
            isinstance(row, Mapping)
            and row.get("evidence_kind") == "recovery_readback"
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

    territory_values = list(territories) if isinstance(
        territories, (list, tuple, set, frozenset)
    ) else []
    use_values = list(permitted_uses) if isinstance(
        permitted_uses, (list, tuple, set, frozenset)
    ) else []

    grant = rights_core.canonical_grant({
        "grant_id": str(uuid4()),
        "asset_id": canonical_asset["asset_id"],
        "grantor_reference": grantor_reference,
        "right_type": right_type,
        "permitted_uses": use_values,
        "territories": territory_values,
        "valid_from": valid_from,
        "valid_until": valid_until,
        "derivatives_allowed": derivatives_allowed,
        "commercial_use_allowed": commercial_use_allowed,
        "attribution_required": attribution_required,
        "evidence_hashes": evidence_hashes,
        "authority_verified": bool(authority_verified),
        "human_approved": bool(human_approved),
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


def evaluate_music_use(
    *,
    asset: object,
    receipts: object,
    request: object,
    permitted_uses: object,
    territories: object,
    authority_verified: bool = False,
    human_approved: bool = False,
    **grant_scope: Any,
) -> dict[str, Any]:
    """Evaluate one music use through the same canonical Rights Core."""
    projection = project_music_release(
        asset=asset,
        receipts=receipts,
        permitted_uses=permitted_uses,
        territories=territories,
        authority_verified=authority_verified,
        human_approved=human_approved,
        **grant_scope,
    )
    decision = rights_core.evaluate_use(
        asset=projection["asset"],
        grants=[projection["grant"]],
        request=request,
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
        "rights_core_decision_reused": True,
        "authority_inferred": False,
        "human_approval_inferred": False,
        "public_distribution_enabled": False,
    }
