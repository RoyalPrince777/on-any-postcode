"""Pure fail-closed OAP TV response decision; does not serve or publish media.

Only trusted server-side identity, rights and storage evidence may populate inputs.
Actual HTTP endpoint integration and independent evidence issuers are NOT present.
"""
from __future__ import annotations

from collections.abc import Mapping

from .tv_byte_ranges import UnsatisfiableRange, parse_single_range
from .tv_private_playback_gate import authorize_private_playback


def plan_founder_private_response(
    *,
    founder_authenticated: bool,
    owner_identity_matches: bool,
    rights_decision: object,
    entitlement_proven: bool,
    storage_integrity_proven: bool,
    server_evidence_verified: bool,
    media_size: int,
    range_header: str | None = None,
) -> dict[str, object]:
    """Never produce a media range until every independent proof is allowed."""
    decision = authorize_private_playback(
        founder_authenticated=founder_authenticated,
        owner_identity_matches=owner_identity_matches,
        rights_decision=rights_decision,
        entitlement_proven=entitlement_proven,
        storage_integrity_proven=storage_integrity_proven,
        server_evidence_verified=server_evidence_verified,
    )
    if not decision["allowed"]:
        return {"allowed": False, "blockers": decision["blockers"], "media_bytes_served": False}
    if not isinstance(media_size, int) or isinstance(media_size, bool) or media_size <= 0:
        return {"allowed": False, "blockers": ["invalid_trusted_media_size"], "media_bytes_served": False}
    if range_header is None:
        return {"allowed": True, "status": 200, "start": 0, "end": media_size - 1,
                "length": media_size, "media_bytes_served": False, "public_playback_enabled": False}
    try:
        selection = parse_single_range(range_header, media_size)
    except UnsatisfiableRange:
        return {"allowed": False, "status": 416, "blockers": ["invalid_byte_range"],
                "content_range": f"bytes */{media_size}", "media_bytes_served": False}
    return {"allowed": True, "status": 206, "start": selection.start, "end": selection.end,
            "length": selection.length, "content_range": selection.content_range,
            "media_bytes_served": False, "public_playback_enabled": False}
