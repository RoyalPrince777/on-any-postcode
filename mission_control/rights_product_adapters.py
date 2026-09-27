"""Thin first-party product adapters for the canonical Rights Core.

These adapters only decide internal eligibility. They never publish, broadcast,
distribute, monetise, or claim legal validity.
"""
from __future__ import annotations

import json
from typing import Any
from uuid import UUID, uuid5

from . import rights_core

NAMESPACE = UUID("4ae0cf62-8c53-4dbf-9ce6-5bb0d4ca650f")


def _grant_id(product: str, asset_id: str, scope: dict[str, Any]) -> str:
    payload = json.dumps(
        {"product": product, "asset_id": asset_id, **scope},
        sort_keys=True,
        default=str,
    )
    return str(uuid5(NAMESPACE, payload))


def _evaluate(
    *,
    product: str,
    asset: object,
    request: object,
    right_type: str,
    permitted_uses: object,
    territories: object,
    permitted_channels: object,
    evidence_hashes: object,
    grantor_reference: str,
    authority_verified: bool = False,
    authority_receipt_hash: object = None,
    human_approved: bool = False,
    human_approval_receipt_hash: object = None,
    valid_from: object = None,
    valid_until: object = None,
    derivatives_allowed: bool = False,
    commercial_use_allowed: bool = False,
    attribution_required: bool = False,
    revoked: bool = False,
    revocation_receipt_hash: object = None,
    lineage_assets: object = (),
) -> dict[str, Any]:
    canonical = rights_core.canonical_asset(asset)
    scope = {
        "right_type": right_type,
        "uses": sorted(map(str, permitted_uses)),
        "territories": sorted(map(str, territories)),
        "channels": sorted(map(str, permitted_channels)),
        "valid_from": valid_from,
        "valid_until": valid_until,
    }
    grant = rights_core.canonical_grant({
        "grant_id": _grant_id(product, canonical["asset_id"], scope),
        "asset_id": canonical["asset_id"],
        "owner_identity_id": canonical["owner_identity_id"],
        "grantor_reference": grantor_reference,
        "right_type": right_type,
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
        "revoked": revoked,
        "revocation_receipt_hash": revocation_receipt_hash,
    })
    decision = rights_core.evaluate_use(
        asset=canonical,
        grants=[grant],
        request=request,
        lineage_assets=lineage_assets,
    )
    return {
        **decision,
        "product": product,
        "internal_eligibility_only": True,
        "legal_validity_verified": False,
        "public_action_enabled": False,
    }


def evaluate_records_archive(**kwargs: Any) -> dict[str, Any]:
    return _evaluate(
        product="OAP Records",
        right_type="recording",
        permitted_uses=("archive",),
        permitted_channels=("OAP Records",),
        grantor_reference="oap:records:archive",
        **kwargs,
    )


def evaluate_media_publish(**kwargs: Any) -> dict[str, Any]:
    return _evaluate(
        product="OAP Media",
        right_type="distribution",
        permitted_uses=("publish",),
        permitted_channels=("OAP Media",),
        grantor_reference="oap:media:publish",
        **kwargs,
    )


def evaluate_tv_broadcast(**kwargs: Any) -> dict[str, Any]:
    return _evaluate(
        product="OAP TV",
        right_type="broadcast",
        permitted_uses=("broadcast",),
        permitted_channels=("OAP TV",),
        grantor_reference="oap:tv:broadcast",
        **kwargs,
    )


def evaluate_distribution_handoff(**kwargs: Any) -> dict[str, Any]:
    return _evaluate(
        product="OAP Distribution",
        right_type="distribution",
        permitted_uses=("distribution",),
        permitted_channels=("OAP Distribution",),
        grantor_reference="oap:distribution:handoff",
        **kwargs,
    )


def status() -> dict[str, Any]:
    return {
        "component": "OAP Rights product adapters",
        "records_internal_gate": True,
        "media_internal_gate": True,
        "tv_internal_gate": True,
        "distribution_internal_gate": True,
        "public_action_enabled": False,
        "legal_validity_verified": False,
    }
