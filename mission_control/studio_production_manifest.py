"""Private, pure OAP Studio production-manifest validation.

This module never reads assets, writes records, generates media, publishes,
grants permissions, or changes the existing Studio execution boundary.
"""
from __future__ import annotations

import re
from typing import Any
from uuid import UUID

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_LANGUAGES = frozenset({"en", "tw"})
_KINDS = frozenset({"script", "image", "video", "audio", "subtitle", "master"})


def _uuid(value: object, name: str) -> str:
    try:
        return str(UUID(str(value)))
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError(f"{name}_invalid") from exc


def validate_manifest(record: object, *, owner_id: object) -> dict[str, Any]:
    """Validate a private episode manifest without authorising execution."""
    if not isinstance(record, dict):
        raise ValueError("studio_manifest_invalid")
    owner = _uuid(owner_id, "owner_id")
    if _uuid(record.get("owner_id"), "manifest_owner_id") != owner:
        raise ValueError("studio_manifest_owner_mismatch")
    project = _uuid(record.get("project_id"), "project_id")
    episode = _uuid(record.get("episode_id"), "episode_id")
    duration = record.get("duration_seconds")
    if type(duration) is not int or not 1 <= duration <= 7200:
        raise ValueError("studio_duration_invalid")
    languages = record.get("languages")
    if not isinstance(languages, list) or not languages or any(
        not isinstance(lang, str) or lang not in _LANGUAGES for lang in languages
    ) or len(set(languages)) != len(languages):
        raise ValueError("studio_languages_invalid")
    assets = record.get("assets")
    if not isinstance(assets, list) or len(assets) > 1000:
        raise ValueError("studio_assets_invalid")
    checked = []
    seen = set()
    for asset in assets:
        if not isinstance(asset, dict):
            raise ValueError("studio_asset_invalid")
        aid = _uuid(asset.get("asset_id"), "asset_id")
        if aid in seen:
            raise ValueError("studio_asset_duplicate")
        seen.add(aid)
        if _uuid(asset.get("owner_id"), "asset_owner_id") != owner:
            raise ValueError("studio_asset_owner_mismatch")
        kind = asset.get("kind")
        digest = asset.get("sha256")
        if kind not in _KINDS or not isinstance(digest, str) or not _SHA256.fullmatch(digest):
            raise ValueError("studio_asset_evidence_invalid")
        checked.append({"asset_id": aid, "owner_id": owner, "kind": kind, "sha256": digest})
    return {
        "owner_id": owner,
        "project_id": project,
        "episode_id": episode,
        "duration_seconds": duration,
        "languages": list(languages),
        "assets": checked,
        "execution_authorised": False,
        "publish_authorised": False,
        "payment_authorised": False,
        "release_state": "blocked",
    }
