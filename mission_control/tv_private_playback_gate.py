"""Fail-closed OAP TV private playback authorization boundary.

This is a pure decision layer, not an HTTP endpoint or evidence issuer.
All proofs must be established independently by trusted server-side code.
"""
from __future__ import annotations

from collections.abc import Mapping


def authorize_private_playback(
    *,
    founder_authenticated: bool,
    owner_identity_matches: bool,
    rights_decision: object,
    entitlement_proven: bool,
    storage_integrity_proven: bool,
) -> dict[str, object]:
    """Deny unless all independent playback prerequisites are proven."""
    from . import rights_core

    proof = rights_core.decision_proof(
        rights_decision if isinstance(rights_decision, Mapping) else {}
    )
    blockers = []
    if founder_authenticated is not True:
        blockers.append("founder_authentication_required")
    if owner_identity_matches is not True:
        blockers.append("asset_owner_mismatch")
    if not proof["canonical_allow"]:
        blockers.append("canonical_rights_allow_not_proven")
    if entitlement_proven is not True:
        blockers.append("entitlement_not_proven")
    if storage_integrity_proven is not True:
        blockers.append("storage_integrity_not_proven")
    return {
        "allowed": not blockers,
        "blockers": blockers,
        "public_playback_enabled": False,
        "media_bytes_served": False,
    }
