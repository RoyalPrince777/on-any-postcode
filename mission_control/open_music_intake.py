"""Private candidate-only OAP Open Music intake; never a rights authority.

Reuse existing first-party OAP Music release records and entertainment_catalogue projection.
This function never downloads, persists, publishes, streams or approves media.
"""
from __future__ import annotations

import hashlib
from collections.abc import Mapping
from urllib.parse import urlsplit
from uuid import UUID

SOURCE_KINDS = frozenset({
    "direct_artist", "free_music_archive", "ccmixter", "internet_archive",
    "musopen", "other_open_archive",
})
LICENCE_KINDS = frozenset({
    "CC0", "CC_BY", "CC_BY_SA", "PUBLIC_DOMAIN", "DIRECT_PERMISSION",
})
MAX_CANDIDATES = 25
MAX_LEADS_SCAN = 250

# Discovery-page references only; not content hosts, rights registries or APIs.
SOURCE_PAGE_HOSTS = {
    "free_music_archive": frozenset({"freemusicarchive.org", "www.freemusicarchive.org"}),
    "ccmixter": frozenset({"ccmixter.org", "www.ccmixter.org", "dig.ccmixter.org"}),
    "internet_archive": frozenset({"archive.org", "www.archive.org"}),
    "musopen": frozenset({"musopen.org", "www.musopen.org"}),
}


def _uuid(value: object) -> str | None:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError):
        return None


def _candidate_uid(value: object) -> str | None:
    """Accept a bare UUID or exactly one canonical OAP Music prefix."""
    if not isinstance(value, str):
        return None
    value = value.removeprefix("oap:open-music:")
    return _uuid(value)


def _safe_text(value: object, limit: int) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = " ".join(value.split())
    return cleaned if 0 < len(cleaned) <= limit else None


def _source_page(source_kind: object, url: object) -> str | None:
    """Allowlist only reviewable HTTPS archive pages; never fetch or resolve."""
    if not isinstance(source_kind, str) or not isinstance(url, str):
        return None
    allowed = SOURCE_PAGE_HOSTS.get(source_kind)
    if allowed is None or not 0 < len(url) <= 2048:
        return None
    if any(char.isspace() or ord(char) < 32 or char == "\\" for char in url):
        return None
    try:
        parsed = urlsplit(url)
        host = parsed.hostname
    except ValueError:
        return None
    if (
        parsed.scheme != "https" or host not in allowed
        or parsed.netloc != host
        or parsed.path in ("", "/") or parsed.path.startswith("//")
        or parsed.query or parsed.fragment
    ):
        return None
    return url


def candidate_preview(rows: object) -> dict[str, object]:
    """Sanitise untrusted leads; no assertion becomes verified evidence."""
    source = rows if isinstance(rows, list) else []
    candidates: list[dict[str, object]] = []
    seen: set[str] = set()
    for row in source[:MAX_LEADS_SCAN]:
        if len(candidates) == MAX_CANDIDATES:
            break
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
            "source_page_url": _source_page(source_kind, row.get("source_page_url")),
            "source_page_independently_checked": False,
            "review_state": "private_candidate",
            "rights_verified": False,
            "source_bytes_verified": False,
            "recording_rights_verified": False,
            "composition_rights_verified": False,
            "territory_verified": False,
            "music_release_created": False,
            "public_catalogue_enabled": False,
            "playback_enabled": False,
        })
    return {
        "organ": "OAP Music",
        "canonical_catalogue": "OAP Music",
        "candidates": candidates,
        "candidate_count": len(candidates),
        "ingest_performed": False,
        "external_provider_dependency": False,
        "human_authority_final": True,
    }


def evidence_bytes_digest(evidence: object, *, max_bytes: int = 8_388_608) -> dict[str, object]:
    """Compute a digest of bytes actually supplied, never verify their origin."""
    if (
        type(max_bytes) is not int or not 0 < max_bytes <= 8_388_608
        or not isinstance(evidence, bytes) or not evidence
        or len(evidence) > max_bytes
    ):
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
    candidate_uid = _candidate_uid(row.get("candidate_id"))
    kind = row.get("source_kind")
    kind = kind if isinstance(kind, str) and kind in SOURCE_KINDS else None
    claim = row.get("claimed_licence")
    claim = claim if isinstance(claim, str) and claim in LICENCE_KINDS else None
    topics = [
        "identify_original_source_and_licensor",
        "verify_recording_rights_separately",
        "verify_composition_rights_separately",
        "verify_territory_and_distribution_uses",
        "verify_attribution_and_revocation",
        "verify_asset_to_evidence_binding",
        "obtain_owner_scoped_music_and_human_approval",
    ]
    if claim in ("CC_BY", "CC_BY_SA"):
        topics.append("verify_credit_and_licence_notice_requirements")
    if claim == "CC_BY_SA":
        topics.append("verify_share_alike_scope_for_planned_uses")
    if claim in ("CC0", "PUBLIC_DOMAIN"):
        topics.append("verify_recording_and_composition_public_domain_separately")
    if claim == "DIRECT_PERMISSION":
        topics.append("verify_direct_grant_signatory_scope_and_expiry")
    return {
        "candidate_id": f"oap:open-music:{candidate_uid}" if candidate_uid else None,
        "submitted_evidence_id": _uuid(proof.get("evidence_id")),
        "source_kind": kind,
        "source_page_url": _source_page(kind, row.get("source_page_url")),
        "source_page_independently_checked": False,
        "claimed_licence": claim,
        "review_topics": topics,
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
            "owner_scoped_music_release_and_human_approval_not_connected",
        ],
        "human_authority_final": True,
    }




def private_source_review_receipt(candidate: object) -> dict[str, object]:
    """In-memory, non-authoritative review receipt for one named source lead.

    Never stores evidence, grants rights, downloads music or creates an OAP Music release.
    A source-page claim cannot prove recording or composition ownership.
    """
    row = candidate if isinstance(candidate, Mapping) else {}
    handoff = music_handoff_preview(row)
    rights = rights_review(row)
    candidate_id = handoff["candidate_id"]
    page = rights["source_page_url"] if candidate_id else None
    attribution_name = _safe_text(row.get("artist"), 180) if candidate_id else None
    attribution_title = _safe_text(row.get("title"), 180) if candidate_id else None
    return {
        "candidate_id": candidate_id,
        "source_kind": rights["source_kind"] if candidate_id else None,
        "source_page_url": page,
        "title": attribution_title,
        "artist": attribution_name,
        "claimed_licence": rights["claimed_licence"] if candidate_id else None,
        "claimed_licence_reference_url": {
            "CC_BY": "https://creativecommons.org/licenses/by/4.0/",
            "CC_BY_SA": "https://creativecommons.org/licenses/by-sa/4.0/",
            "CC0": "https://creativecommons.org/publicdomain/zero/1.0/",
        }.get(rights["claimed_licence"]) if candidate_id else None,
        "attribution_source_url": page,
        "attribution_changes_disclosure_review_required": (
            rights["claimed_licence"] in ("CC_BY", "CC_BY_SA")
            if candidate_id else False
        ),
        "attribution_draft": (
            f"{attribution_title} — {attribution_name}"
            if attribution_title and attribution_name else None
        ),
        "source_page_independently_checked": False,
        "recording_rights_verified": False,
        "composition_rights_verified": False,
        "licensor_authority_verified": False,
        "territory_and_use_verified": False,
        "attribution_verified": False,
        "source_asset_integrity_verified": False,
        "review_state": "private_unverified_lead",
        "receipt_persisted": False,
        "evidence_bytes_retained": False,
        "music_release_created": False,
        "playback_enabled": False,
        "public_catalogue_enabled": False,
        "blockers": rights["blockers"],
        "human_authority_final": True,
    }



def private_music_release_review_plan(
    candidate: object, owner_identity_id: object = None,
    release_id: object = None,
) -> dict[str, object]:
    """Private planning only: an owner UUID is not an authenticated session.

    Reuses existing OAP Music release functions; never persists, approves,
    downloads, changes rights, or creates a second catalogue.
    """
    receipt = private_source_review_receipt(candidate)
    handoff = music_handoff_preview(candidate)
    owner = _uuid(owner_identity_id) if isinstance(owner_identity_id, str) else None
    submitted_release = _uuid(release_id) if isinstance(release_id, str) else None
    candidate_id = receipt["candidate_id"]
    requirements = (
        "independently_verify_original_source_and_licensor",
        "bind_independently_obtained_source_bytes_to_exact_asset",
        "verify_recording_rights_and_contributors",
        "verify_composition_rights_and_samples",
        "verify_territory_duration_and_intended_uses",
        "verify_attribution_licence_notice_changes_and_revocation",
        "authenticate_owner_and_bind_existing_music_release",
        "obtain_auditable_human_release_approval",
    )
    return {
        "candidate_id": candidate_id,
        "submitted_owner_identity_id": owner if candidate_id else None,
        "submitted_release_id": submitted_release if candidate_id else None,
        "owner_authenticated": False,
        "owner_bound_to_music_release": False,
        "target_organ": "OAP Music",
        "target_release_type": handoff["target_release_type"],
        "source_page_url": receipt["source_page_url"],
        "claimed_licence": receipt["claimed_licence"],
        "attribution_draft": receipt["attribution_draft"],
        "review_requirements": [
            {"requirement": name, "independently_proven": False}
            for name in requirements
        ],
        "ready_for_authenticated_handoff": False,
        "independent_rights_verified": False,
        "asset_provenance_verified": False,
        "human_release_approved": False,
        "private_plan_only": True,
        "receipt_persisted": False,
        "release_created": False,
        "media_retrieval_performed": False,
        "public_catalogue_enabled": False,
        "playback_enabled": False,
        "payments_enabled": False,
        "human_authority_final": True,
    }


def asset_integrity_review(
    candidate_id: object, asset_bytes: object, expected_sha256: object,
) -> dict[str, object]:
    """Compare supplied asset bytes to a submitted digest without trusting its origin.

    This is not an independent provenance check or a licence verification. A
    matching attacker-supplied digest must never make content publishable.
    """
    uid = _candidate_uid(candidate_id)
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
        "canonical_catalogue": "OAP Music",
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


def music_handoff_preview(candidate: object) -> dict[str, object]:
    """Inert OAP Music handoff: preserve one release store and authority."""
    row = candidate if isinstance(candidate, Mapping) else {}
    uid = _candidate_uid(row.get("candidate_id"))
    title = _safe_text(row.get("title"), 180)
    artist = _safe_text(row.get("artist"), 180)
    kind = row.get("source_kind")
    licence = row.get("claimed_licence")
    valid = bool(uid and title and artist
                 and isinstance(kind, str) and kind in SOURCE_KINDS
                 and isinstance(licence, str) and licence in LICENCE_KINDS)
    return {
        "candidate_id": f"oap:open-music:{uid}" if valid else None,
        "target_organ": "OAP Music",
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
            "authenticated_owner_scoped_music_write_not_authorised",
            "human_release_approval_required",
        ],
        "human_authority_final": True,
    }
