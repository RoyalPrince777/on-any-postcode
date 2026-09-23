"""Isolated OAP Open Cinema evidence-byte integrity primitive.

A matching digest proves only that supplied bytes match a supplied digest. It
does NOT verify an agreement, licensor, public-domain status, chain of title,
country permission or film-streaming rights. No filesystem, fetch, persistence,
HTTP route or trusted authority is created here.
"""
from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
from hmac import compare_digest
from uuid import UUID

MAX_BYTES = 2_000_000


def check_bytes(evidence: object, document: object) -> dict[str, object]:
    """Bounded local byte check; always refuse to convert it to rights proof."""
    row = evidence if isinstance(evidence, Mapping) else {}
    try:
        evidence_id = str(UUID(str(row.get("evidence_id"))))
    except (TypeError, ValueError, AttributeError):
        evidence_id = None
    expected = row.get("sha256")
    valid_digest = (
        isinstance(expected, str)
        and len(expected) == 64
        and all(char in "0123456789abcdef" for char in expected)
    )
    valid_bytes = type(document) is bytes and 0 < len(document) <= MAX_BYTES
    matching = bool(
        evidence_id and valid_digest and valid_bytes
        and compare_digest(sha256(document).hexdigest(), expected)
    )
    return {
        "evidence_id": evidence_id,
        "bytes_checked": bool(valid_bytes),
        "digest_match": matching,
        "source_authenticity_verified": False,
        "licensor_authority_verified": False,
        "chain_of_title_verified": False,
        "country_rights_verified": False,
        "playback_enabled": False,
        "publication_enabled": False,
        "document_retained": False,
        "blockers": [
            "independent_evidence_source_not_attested",
            "licensor_chain_of_title_and_territory_not_verified",
            "media_asset_entitlement_and_human_release_not_connected",
        ],
    }
