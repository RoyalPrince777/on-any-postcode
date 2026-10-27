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


def series_episodes(rows: object, series_id: str) -> dict[str, object]:
    """Derive a private, ordered episode listing without claiming availability."""
    try:
        canonical_id = f"oap:tv:{UUID(series_id)}"
    except (ValueError, TypeError, AttributeError):
        return {
            "series_id": None, "episodes": [], "episode_count": 0,
            "playback_enabled": False, "public_catalogue_enabled": False,
        }
    drafts = private_catalogue(rows)["items"]
    episodes = [
        item for item in drafts
        if item["kind"] == "episode" and item.get("series_id") == canonical_id
    ]
    episodes.sort(key=lambda item: (item["season"], item["episode"], item["item_id"]))
    return {
        "series_id": canonical_id,
        "episodes": episodes,
        "episode_count": len(episodes),
        "playback_enabled": False,
        "public_catalogue_enabled": False,
    }


def private_shelves(rows: object) -> dict[str, object]:
    """Group genuine owner-supplied drafts for Cinema, Series, Channels and Live.

    This remains a private, in-memory projection. It cannot create a public
    catalogue, fetch third-party videos or grant playback rights.
    """
    drafts = private_catalogue(rows)["items"]
    shelves: dict[str, list[dict[str, object]]] = {
        "cinema": [], "series": [], "channels": [], "live": [],
    }
    known_series = {item["item_id"] for item in drafts if item["kind"] == "series"}
    for item in drafts:
        kind = item["kind"]
        if kind == "episode" and item.get("series_id") not in known_series:
            continue  # Orphan episodes cannot appear as a browseable series.
        if kind in {"film", "documentary"}:
            shelves["cinema"].append(item)
        elif kind in {"series", "episode"}:
            shelves["series"].append(item)
        elif kind == "creator_video":
            shelves["channels"].append(item)
        elif kind == "live":
            shelves["live"].append(item)
    return {
        "shelves": shelves,
        "item_count": sum(len(items) for items in shelves.values()),
        "mode": "private_draft_only",
        "public_catalogue_enabled": False,
        "playback_enabled": False,
    }
