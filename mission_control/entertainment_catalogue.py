"""Read-only first-party entertainment catalogue and player *contract*.

Project existing owner-scoped OAP Music records. This creates no alternative
content store, raw-media access, rights evidence, playback engine or authority.
Until a server-owned rights/evidence/entitlement chain is connected, playback
MUST remain disabled even for PUBLISHED/VERIFIED catalogue metadata.
"""
from __future__ import annotations

from collections.abc import Mapping
from uuid import UUID

RELEASE_TYPES = frozenset({"single", "ep", "album"})
RELEASE_STATES = frozenset(
    {"DRAFT", "REVIEW_REQUIRED", "APPROVED", "PUBLISHED", "ARCHIVED"}
)
RIGHTS_STATES = frozenset(
    {"SELF_DECLARED", "REVIEW_REQUIRED", "VERIFIED", "REJECTED"}
)
DESTINATIONS = (
    "OAP TV", "OAP Media", "OAP Music", "OAP Live", "OAP Records",
)
PLAYER_OWNER = "OAP Player"
SOURCE_ORGAN = "OAP Music"
MAX_ITEMS = 100


def _release(row: object) -> dict[str, object] | None:
    """Allowlist metadata only; never surface an untrusted media_ref or URL."""
    if not isinstance(row, Mapping):
        return None
    try:
        release_id = str(UUID(str(row.get("release_id"))))
    except (TypeError, ValueError, AttributeError):
        return None
    title = row.get("title")
    kind = row.get("release_type")
    state = row.get("state")
    rights = row.get("rights_status")
    if (
        not isinstance(title, str)
        or not title.strip()
        or len(title) > 180
        or not isinstance(kind, str)
        or kind not in RELEASE_TYPES
        or not isinstance(state, str)
        or state not in RELEASE_STATES
        or not isinstance(rights, str)
        or rights not in RIGHTS_STATES
    ):
        return None
    count = row.get("track_count", 0)
    if type(count) is not int or not 0 <= count <= 100_000:
        return None
    return {
        "content_id": f"oap:tune:{release_id}",
        "source_organ": SOURCE_ORGAN,
        "source_release_id": release_id,
        "title": title.strip(),
        "kind": kind,
        "publication_state": state,
        "rights_review_state": rights,
        "track_count": count,
        "catalogue_visibility": "owner_only",
        "playback_available": False,
        "playback_url": None,
    }


def rights_gate(record: object) -> dict[str, object]:
    """A schema state or caller-supplied boolean is NOT independent rights proof.

    No verified rights-record resolver is connected to this read contract.
    Deliberately fail closed until the existing rights authority can supply
    independently checked, owner/asset/territory-bound evidence and receipts.
    """
    row = record if isinstance(record, Mapping) else {}
    publication_state = row.get("publication_state")
    rights_state = row.get("rights_review_state")
    blockers = []
    if publication_state != "PUBLISHED":
        blockers.append("publication_not_proven")
    if rights_state != "VERIFIED":
        blockers.append("rights_review_not_verified")
    blockers.extend((
        "independent_rights_evidence_not_connected",
        "media_asset_integrity_not_connected",
        "viewer_entitlement_not_connected",
    ))
    return {
        "allowed": False,
        "blockers": blockers,
        "independent_proof_checked": False,
        "content_published": False,
        "playback_authorised": False,
        "founder_final_required": True,
    }


def universal_player_contract(record: object = None) -> dict[str, object]:
    """One future player contract reused by Music, TV, Media, Live and Records."""
    item = record if isinstance(record, Mapping) else {}
    return {
        "owner": PLAYER_OWNER,
        "mode": "contract_only",
        "content_id": item.get("content_id") if isinstance(
            item.get("content_id"), str
        ) else None,
        "destinations": DESTINATIONS,
        "controls_planned": (
            "play_pause", "seek", "captions", "quality", "resume", "stop",
        ),
        "rights": rights_gate(item),
        "playback_enabled": False,
        "stream_url": None,
        "download_url": None,
        "entitlement_token": None,
        "media_delivery_performed": False,
        "external_distribution_performed": False,
        "publishing_authority_granted": False,
        "human_authority_final": True,
    }


def project_catalogue(tune_dashboard: object) -> dict[str, object]:
    """Project already-owner-scoped OAP Music releases without storing a second copy.

    Caller MUST obtain tune_dashboard using the existing authenticated
    product_core_services.tune_dashboard(identity_id), never request JSON.
    No other organ is claimed indexed or playable by this limited projection.
    """
    dashboard = tune_dashboard if isinstance(tune_dashboard, Mapping) else {}
    source = dashboard.get("releases")
    source_rows = source if isinstance(source, (list, tuple)) else ()
    items: list[dict[str, object]] = []
    ids: set[str] = set()
    for row in source_rows[:MAX_ITEMS]:
        item = _release(row)
        if item is None or item["content_id"] in ids:
            continue
        ids.add(item["content_id"])
        items.append(item)
    return {
        "catalogue": "OAP Entertainment",
        "source_organ": SOURCE_ORGAN,
        "scope": "authenticated_owner_tune_releases_only",
        "destinations_reserved": DESTINATIONS,
        "other_destination_adapters_connected": False,
        "items": items,
        "item_count": len(items),
        "player": universal_player_contract(),
        "rights_registry_connected": False,
        "public_catalogue_enabled": False,
        "playback_enabled": False,
        "publication_performed": False,
        "migration_performed": False,
        "human_authority_final": True,
    }
