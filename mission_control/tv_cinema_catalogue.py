"""OAP TV Cinema and Channels: private, fail-closed catalogue projections.

Metadata from owner-submitted drafts never issues licences, generates playback
URLs, uploads files or publishes programmes. No network/database side effects.
"""
from __future__ import annotations

from collections.abc import Mapping
from uuid import UUID

KINDS = frozenset({"film", "documentary", "series", "episode", "creator_video", "live"})
MAX_ITEMS = 100
MAX_TITLE = 180


def catalogue_item(row: object) -> dict[str, object] | None:
    """Accept bounded draft metadata only; never trust its access flags."""
    if not isinstance(row, Mapping):
        return None
    try:
        item_id = str(UUID(str(row.get("item_id"))))
    except (ValueError, TypeError, AttributeError):
        return None
    kind = row.get("kind")
    title = row.get("title")
    if (
        not isinstance(kind, str) or kind not in KINDS
        or not isinstance(title, str) or not 1 <= len(title.strip()) <= MAX_TITLE
    ):
        return None
    record: dict[str, object] = {
        "item_id": f"oap:tv:{item_id}",
        "kind": kind,
        "title": title.strip(),
        "draft_only": True,
        "rights_verified": False,
        "asset_verified": False,
        "published": False,
        "playback_enabled": False,
        "playback_url": None,
    }
    if kind in {"series", "episode"}:
        series_id = row.get("series_id")
        if kind == "episode":
            try:
                record["series_id"] = f"oap:tv:{UUID(str(series_id))}"
            except (ValueError, TypeError, AttributeError):
                return None
            season = row.get("season")
            episode = row.get("episode")
            if any(type(value) is not int or not 1 <= value <= 999 for value in (season, episode)):
                return None
            record["season"] = season
            record["episode"] = episode
    return record


def private_catalogue(rows: object) -> dict[str, object]:
    """Build a deduplicated internal draft catalogue; no public availability."""
    accepted: list[dict[str, object]] = []
    seen: set[str] = set()
    for raw in (rows if isinstance(rows, list) else [])[:MAX_ITEMS]:
        item = catalogue_item(raw)
        if item is None or str(item["item_id"]) in seen:
            continue
        seen.add(str(item["item_id"]))
        accepted.append(item)
    return {
        "items": accepted,
        "item_count": len(accepted),
        "mode": "private_draft_only",
        "public_catalogue_enabled": False,
        "publishing_performed": False,
        "playback_enabled": False,
        "asset_import_performed": False,
    }
