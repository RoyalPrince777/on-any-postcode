"""Private candidate-only OAP Open Music intake; never a rights authority.

Reuse OAP Tune Core and entertainment_catalogue for release records and projection.
This function never downloads, persists, publishes, streams or approves media.
"""
from __future__ import annotations

import hashlib
from collections.abc import Mapping
from uuid import UUID

SOURCE_KINDS = frozenset({
    "direct_artist", "free_music_archive", "ccmixter", "internet_archive",
    "musopen", "other_open_archive",
})
LICENCE_KINDS = frozenset({
    "CC0", "CC_BY", "CC_BY_SA", "PUBLIC_DOMAIN", "DIRECT_PERMISSION",
})
MAX_CANDIDATES = 25


def _uuid(value: object) -> str | None:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError):
        return None


def _safe_text(value: object, limit: int) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = " ".join(value.split())
    return cleaned if 0 < len(cleaned) <= limit else None


def candidate_preview(rows: object) -> dict[str, object]:
    """Sanitise untrusted leads; no assertion becomes verified evidence."""
    source = rows if isinstance(rows, list) else []
    candidates: list[dict[str, object]] = []
    seen: set[str] = set()
    for row in source[:MAX_CANDIDATES]:
        if not isinstance(row, Mapping):
            continue
        uid = _uuid(row.get("candidate_id"))
        title = _safe_text(row.get("title"), 180)
        artist = _safe_text(row.get("artist"), 180)
        source_kind = row.get("source_kind")
        claimed_licence = row.get("claimed_licence")
        if (
            uid is None or uid in seen or title is None or artist is None
            or not isinstance(source_kind, str) or source_kind not in SOURCE_KINDS
            or not isinstance(claimed_licence, str) or claimed_licence not in LICENCE_KINDS
        ):
            continue
        seen.add(uid)
        candidates.append({
            "candidate_id": f"oap:open-music:{uid}",
            "title": title,
            "artist": artist,
            "source_kind": source_kind,
            "claimed_licence": claimed_licence,
            "review_state": "private_candidate",
            "rights_verified": False,
            "source_bytes_verified": False,
            "recording_rights_verified": False,
            "composition_rights_verified": False,
            "territory_verified": False,
            "tune_release_created": False,
            "public_catalogue_enabled": False,
            "playback_enabled": False,
        })
    return {
        "organ": "OAP Music",
        "canonical_catalogue": "OAP Tune Core",
        "candidates": candidates,
        "candidate_count": len(candidates),
        "ingest_performed": False,
        "external_provider_dependency": False,
        "human_authority_final": True,
    }


def evidence_bytes_digest(evidence: object, *, max_bytes: int = 8_388_608) -> dict[str, object]:
    """Compute a digest of bytes actually supplied, never verify their origin."""
    if (\n        type(max_bytes) is not int or not 0 < max_bytes <= 8_388_608\n        or not isinstance(evidence, bytes) or not evidence\n        or len(evidence) > max_bytes\n    ):
        return {
            "accepted": False, "sha256": None, "byte_length": None,
            "independently_verified": False, "rights_verified": False,
        }
    return {
        "accepted": True,
        "sha256": hashlib.sha256(evidence).hexdigest(),
        "byte_length": len(evidence),
        "independently_verified": False,
        "rights_verified": False,
    }


def rights_review(candidate: object, evidence: object = None) -> dict[str, object]:
    """Fail closed even when claimant supplies plausible licence and hash fields."""
    row = candidate if isinstance(candidate, Mapping) else {}
    proof = evidence if isinstance(evidence, Mapping) else {}
    return {
        "candidate_id": row.get("candidate_id") if isinstance(row.get("candidate_id"), str) else None,
        "submitted_evidence_id": _uuid(proof.get("evidence_id")),
        "claimed_licence": row.get("claimed_licence") if isinstance(row.get("claimed_licence"), str) and row.get("claimed_licence") in LICENCE_KINDS else None,
        "rights_verified": False,
        "recording_rights_verified": False,
        "composition_rights_verified": False,
        "territory_verified": False,
        "source_bytes_verified": False,
        "attribution_verified": False,
        "playback_authorised": False,
        "public_catalogue_enabled": False,
        "distribution_authorised": False,
        "blockers": [
            "independent_source_and_licensor_verification_not_connected",
            "source_byte_to_asset_integrity_not_connected",
            "composition_and_recording_rights_not_verified",
            "territory_and_use_permissions_not_verified",
            "attribution_and_revocation_not_connected",
            "owner_scoped_tune_release_and_human_approval_not_connected",
        ],
        "human_authority_final": True,
    }


def asset_integrity_review(
    candidate_id: object, asset_bytes: object, expected_sha256: object,
) -> dict[str, object]:
    """Compare supplied asset bytes to a submitted digest without trusting its origin.

    This is not an independent provenance check or a licence verification. A
    matching attacker-supplied digest must never make content publishable.
    """
    uid = _uuid(candidate_id)
    actual = evidence_bytes_digest(asset_bytes)
    expected_valid = (
        isinstance(expected_sha256, str)
        and len(expected_sha256) == 64
        and all(char in "0123456789abcdef" for char in expected_sha256)
    )
    matches = bool(
        uid and actual["accepted"] and expected_valid
        and actual["sha256"] == expected_sha256
    )
    return {
        "candidate_id": f"oap:open-music:{uid}" if uid else None,
        "digest_matches_submission": matches,
        "asset_bytes_accepted": actual["accepted"],
        "actual_sha256": actual["sha256"] if uid else None,
        "independent_source_provenance_verified": False,
        "rights_verified": False,
        "public_catalogue_enabled": False,
        "playback_enabled": False,
        "human_authority_final": True,
    }


# Discovery references only. None is a connected source, licensor, or provider.
OPEN_SOURCE_DIRECTORY = (
    ("direct_artist", "Direct OAP artist submission", None),
    ("free_music_archive", "Free Music Archive", "https://freemusicarchive.org/"),
    ("ccmixter", "ccMixter", "https://dig.ccmixter.org/"),
    ("internet_archive", "Internet Archive Netlabels", "https://archive.org/details/netlabels"),
    ("musopen", "Musopen", "https://musopen.org/music/"),
    ("other_open_archive", "Individually reviewed open archive", None),
)


def source_directory() -> dict[str, object]:
    """Static discovery leads; deliberately no scrape, API or licence claim."""
    return {
        "canonical_catalogue": "OAP Tune Core",
        "entries": [
            {"source_kind": kind, "label": label, "discovery_url": url,
             "connected": False, "licence_verified": False,
             "bulk_import_allowed": False}
            for kind, label, url in OPEN_SOURCE_DIRECTORY
        ],
        "source_fetch_performed": False,
        "catalogue_write_performed": False,
        "human_authority_final": True,
    }


def tune_handoff_preview(candidate: object) -> dict[str, object]:
    """Inert Tune Core handoff: avoid a second release store and authority."""
    row = candidate if isinstance(candidate, Mapping) else {}
    uid = _uuid(row.get("candidate_id"))
    title = _safe_text(row.get("title"), 180)
    artist = _safe_text(row.get("artist"), 180)
    kind = row.get("source_kind")
    licence = row.get("claimed_licence")
    valid = bool(uid and title and artist
                 and isinstance(kind, str) and kind in SOURCE_KINDS
                 and isinstance(licence, str) and licence in LICENCE_KINDS)
    return {
        "candidate_id": f"oap:open-music:{uid}" if valid else None,
        "target_organ": "OAP Tune Core",
        "target_release_type": "single" if valid else None,
        "title": title if valid else None,
        "artist": artist if valid else None,
        "claimed_licence": licence if valid else None,
        "handoff_ready": False,
        "rights_verified": False,
        "release_created": False,
        "playback_enabled": False,
        "public_catalogue_enabled": False,
        "blockers": [
            "independent_rights_verification_required",
            "authenticated_owner_scoped_tune_write_not_authorised",
            "human_release_approval_required",
        ],
        "human_authority_final": True,
    }
