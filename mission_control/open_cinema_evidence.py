"""Private first-party evidence-to-country-rights review contract.

An applicant-supplied document ID, digest, reviewer flag, or licence claim never
constitutes independent chain-of-title verification. This module makes a bounded
review envelope only; it never fetches documents, stores evidence or grants rights.
"""
from __future__ import annotations

from collections.abc import Mapping
from uuid import UUID

from . import open_cinema_worldwide as world

ALLOWED_KINDS = frozenset({
    "signed_distribution_agreement", "public_domain_analysis",
    "creative_commons_source", "creator_direct_permission",
})
MAX_EVIDENCE = 10


def _uid(value: object) -> str | None:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError):
        return None


def review_envelope(candidate_id: object, territory: object, evidence: object) -> dict[str, object]:
    """Summarise *submitted* evidence; never attest its truth or existence."""
    uid = _uid(candidate_id)
    country = world.country_claim(territory)
    source_rows = evidence if isinstance(evidence, list) else []
    refs: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in source_rows[:MAX_EVIDENCE]:
        if not isinstance(row, Mapping):
            continue
        ref = _uid(row.get("evidence_id"))
        kind = row.get("kind")
        digest = row.get("sha256")
        if (
            ref is None or ref in seen
            or not isinstance(kind, str) or kind not in ALLOWED_KINDS
            or not isinstance(digest, str) or len(digest) != 64
            or any(ch not in "0123456789abcdef" for ch in digest)
        ):
            continue
        seen.add(ref)
        refs.append({"evidence_id": ref, "kind": kind, "submitted_sha256": digest})
    blockers = [
        "evidence_bytes_not_retrieved_or_integrity_verified",
        "independent_licensor_and_chain_of_title_not_verified",
        "asset_entitlement_and_human_release_not_connected",
    ]
    if uid is None:
        blockers.insert(0, "invalid_candidate_id")
    if country is None:
        blockers.insert(0, "invalid_country_or_window")
    if not refs:
        blockers.insert(0, "no_valid_evidence_submissions")
    return {
        "candidate_id": f"oap:open-cinema:{uid}" if uid else None,
        "country": country["country"] if country else None,
        "models": country["claimed_models"] if country else [],
        "starts_on": country["claimed_start"] if country else None,
        "ends_on": country["claimed_end"] if country else None,
        "submitted_evidence": refs,
        "evidence_count": len(refs),
        "review_state": "awaiting_independent_review",
        "submitted_digests_verified": False,
        "country_rights_verified": False,
        "licence_acquired": False,
        "content_published": False,
        "playback_enabled": False,
        "blockers": blockers,
        "human_authority_final": True,
    }
