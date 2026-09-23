"""OAP Open Cinema: first-party, private candidate intake; NOT a film licence.

External catalogues are optional discovery references, never playback providers or
rights authorities. No HTTP, scraping, importing media or persistence here.
"""
from __future__ import annotations

from collections.abc import Mapping
from urllib.parse import urlsplit
from uuid import UUID

from . import open_cinema_worldwide

SOURCES = {
    "wikimedia_commons": "commons.wikimedia.org",
    "library_of_congress": "loc.gov",
    "internet_archive": "archive.org",
    "direct_creator": None,
}
LICENCE_CLAIMS = frozenset({"PUBLIC_DOMAIN", "CC0", "CC_BY", "CC_BY_SA", "DIRECT_PERMISSION"})
MAX_ITEMS = 50


def _reference_url(url: object, source: str) -> str | None:
    """Allowlisted citation reference only, NOT an asset or playback location."""
    if not isinstance(url, str) or len(url) > 2048:
        return None
    parsed = urlsplit(url)
    host = parsed.hostname
    try:
        forbidden_authority = parsed.username or parsed.password or parsed.port
    except ValueError:
        return None
    if parsed.scheme != "https" or forbidden_authority:
        return None
    if host is None or host != SOURCES[source] or not parsed.path:
        return None
    if parsed.fragment or parsed.query:
        return None
    return url


def candidate(row: object) -> dict[str, object] | None:
    """Sanitise an owner-supplied lead without trusting its rights assertion."""
    if not isinstance(row, Mapping):
        return None
    try:
        uid = str(UUID(str(row.get("candidate_id"))))
    except (TypeError, ValueError, AttributeError):
        return None
    source = row.get("source")
    title = row.get("title")
    licence = row.get("licence_claim")
    if (
        not isinstance(source, str) or source not in SOURCES
        or not isinstance(title, str) or not 1 <= len(title.strip()) <= 180
        or not isinstance(licence, str) or licence not in LICENCE_CLAIMS
    ):
        return None
    reference = (
        _reference_url(row.get("reference_url"), source)
        if SOURCES[source] else None
    )
    if SOURCES[source] and reference is None:
        return None
    return {
        "candidate_id": f"oap:open-cinema:{uid}",
        "title": title.strip(),
        "source": source,
        "source_reference": reference,
        "licence_claim": licence,
        "rights_evidence_checked": False,
        "uk_cleared": False,
        "ghana_cleared": False,
        "asset_integrity_checked": False,
        "publication_approved": False,
        "discovery_only": True,
        "playback_enabled": False,
        "stream_url": None,
        "download_url": None,
        "worldwide_rights": open_cinema_worldwide.matrix(row.get("territories")),
    }


def private_collection_intake() -> dict[str, object]:
    """Private editorial intake, not owned assets or OAP distribution rights.

    Named works are user-reported purchases, not corroborated transactions.
    Discovery sources are already present in SOURCES; no duplicate catalogue,
    public route, file retrieval, new provider dependency or playback contract.
    """
    purchased = (
        ("The Wire", "television_series", "HBO"),
        ("Friday", "feature_film_1995", "New Line Cinema"),
    )
    titles = [{
        "title": title,
        "kind": kind,
        "production_reference": reference,
        "purchase_reported_by": "founder",
        "purchase_receipt_checked": False,
        "oap_distribution_licence_verified": False,
        "territories_licensed": [],
        "public_catalogue_enabled": False,
        "playback_enabled": False,
        "stream_url": None,
        "download_url": None,
        "stage": "private_rights_review",
    } for title, kind, reference in purchased]
    return {
        "collection": "OAP Open Cinema",
        "scope": "founder_only_private_editorial_intake",
        "existing_catalogue_preserved": True,
        "reported_purchases": titles,
        "other_old_film_titles_received": False,
        "other_old_films": [],
        "free_catalogue_discovery": [{
            "source": source,
            "title_clearance_state": "per_title_evidence_required",
            "films_imported": 0,
            "licences_acquired": False,
            "public_catalogue_enabled": False,
            "playback_enabled": False,
        } for source in SOURCES],
        "rights_registry_connected": False,
        "public_catalogue_enabled": False,
        "playback_enabled": False,
        "payments_enabled": False,
        "media_import_performed": False,
        "human_authority_final": True,
    }


def preview(rows: object) -> dict[str, object]:
    """Stateless owner-side import preview; not a rights registry or DB."""
    source_rows = rows if isinstance(rows, list) else []
    items = []
    seen = set()
    for row in source_rows[:MAX_ITEMS]:
        item = candidate(row)
        if item is None or item["candidate_id"] in seen:
            continue
        seen.add(item["candidate_id"])
        items.append(item)
    return {
        "connector": "OAP Open Cinema",
        "mode": "private_candidate_preview",
        "sources": tuple(SOURCES),
        "items": items,
        "item_count": len(items),
        "rights_registry_connected": False,
        "licences_acquired": False,
        "worldwide_rights_enabled": False,
        "public_catalogue_enabled": False,
        "playback_enabled": False,
        "publication_performed": False,
        "media_import_performed": False,
        "network_requests_performed": False,
        "persistence_performed": False,
        "human_authority_final": True,
    }
