"""Fail-closed first-party application catalogue for The Spot.

Only server-owned explicit route entries may be exposed. This module does not
grant access: destination routes retain their own authentication and permissions.
"""
from __future__ import annotations

from typing import Final

# Static allowlist: no arbitrary URL, dynamic imports or third-party launch.
APP_ENTRIES: Final[tuple[dict[str, str], ...]] = (
    {"id": "pulse", "name": "Pulse", "category": "Social", "route": "/pulse"},
    {"id": "arena", "name": "OAP Arena", "category": "Games", "route": "/arena"},
    {"id": "market", "name": "OAP Market", "category": "Shopping", "route": "/market"},
    {"id": "the-link", "name": "The Link", "category": "Social", "route": "/the-link"},
)


def public_catalogue(*, registered_routes: set[str], query: str = "") -> list[dict[str, str]]:
    """Return only explicit entries whose routes exist in the current Flask app.

    Caller must supply the real route registry; missing routes are omitted.
    Search is bounded and case-insensitive, without personalised tracking.
    """
    needle = str(query or "").strip().casefold()[:100]
    return [
        dict(item)
        for item in APP_ENTRIES
        if item["route"] in registered_routes
        and (not needle or needle in (item["name"] + " " + item["category"]).casefold())
    ]
