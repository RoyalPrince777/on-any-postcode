"""Fail-closed first-party application catalogue for The Spot.

Only server-owned explicit route entries may be exposed. This module does not
grant access: destination routes retain their own authentication and permissions.
"""
from __future__ import annotations

from typing import Final

# Static allowlist: no arbitrary URL, dynamic imports or third-party launch.
APP_ENTRIES: Final[tuple[dict[str, str], ...]] = (
    {"id": "pulse", "name": "Pulse", "category": "Social", "route": "/the-spot/pulse"},
    {"id": "arena", "name": "OAP Arena", "category": "Games", "route": "/arena"},
    {"id": "market", "name": "OAP Market", "category": "Shopping", "route": "/the-spot/market"},
    {"id": "the-link", "name": "The Link", "category": "Social", "route": "/the-link"},
)


def public_catalogue(*, registered_routes: set[str], query: str = "", public_routes: set[str] | None = None) -> list[dict[str, str]]:
    """Return only explicit entries whose routes exist in the current Flask app.

    Caller must supply the real route registry AND independently reviewed public\n    route set. Absence of a public-route review fails closed.
    Search is bounded and case-insensitive, without personalised tracking.
    """
    needle = str(query or "").strip().casefold()[:100]
    return [
        dict(item)
        for item in APP_ENTRIES
        if public_routes is not None\n        and item["route"] in public_routes\n        and item["route"] in registered_routes
        and (not needle or needle in (item["name"] + " " + item["category"]).casefold())
    ]
