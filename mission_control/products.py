"""Canonical read-only hierarchy for The Spot, The Link and LinkUp."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any

PRODUCT_HIERARCHY: tuple[dict[str, str], ...] = (
    {
        "id": "the_spot",
        "name": "The Spot",
        "route": "/the-spot",
        "parent_id": "",
        "purpose": "The postcode community place for local people, activity and discovery.",
        "owner": "OAP World",
    },
    {
        "id": "the_link",
        "name": "The Link",
        "route": "/the-link",
        "parent_id": "the_spot",
        "purpose": "The communications gateway inside The Spot.",
        "owner": "Communications",
    },
    {
        "id": "linkup",
        "name": "LinkUp",
        "route": "/linkup",
        "parent_id": "the_link",
        "purpose": "Protected person-to-person and group conversation inside The Link.",
        "owner": "Communications",
    },
)

SPOT_CAPABILITIES: tuple[dict[str, str], ...] = (
    {"id": "pulse", "name": "Pulse", "owner": "OAP World", "purpose": "Local community feed and activity.", "status": "Public surface live", "function": "Displays postcode activity without private data.", "blocked_by": ""},
    {"id": "signal", "name": "OAP Signal", "owner": "OAP Signal", "purpose": "Official alerts, announcements and trusted updates.", "status": "Public posting live", "function": "Uses the existing bounded public Signal feed.", "blocked_by": ""},
    {"id": "postcode-rooms", "name": "Postcode Rooms", "owner": "Communications", "purpose": "Local postcode and community conversations.", "status": "Basic public room live", "function": "Uses the existing bounded room feed.", "blocked_by": "Private rooms require Identity, Permissions and Guardian"},
    {"id": "events", "name": "Events & Experiences", "owner": "Events", "purpose": "Local gatherings, sports, culture and matchday activity.", "status": "Directory live", "function": "Provides an approved discovery surface.", "blocked_by": "Bookings require Identity and audited persistence"},
    {"id": "discovery", "name": "Local Discovery", "owner": "Explorer", "purpose": "Nearby places, services and useful postcode information.", "status": "Directory live", "function": "Provides a postcode discovery entry point.", "blocked_by": "Live providers and geolocation not connected"},
    {"id": "businesses", "name": "Local Businesses", "owner": "Business Registry", "purpose": "Postcode business listings, offers and promotion.", "status": "Directory live", "function": "Separates business discovery from transactions.", "blocked_by": "Verified merchant onboarding not connected"},
    {"id": "creators", "name": "Creators", "owner": "Creator Identity", "purpose": "Local musicians, artists, talent and content creators.", "status": "Directory live", "function": "Provides a creator discovery surface.", "blocked_by": "Verified Creator Identity not connected"},
    {"id": "community-power", "name": "Community Power", "owner": "Community Power", "purpose": "Contribution, participation and community progress.", "status": "Read-only surface live", "function": "Links contribution awareness without copying its ledger.", "blocked_by": "Audited contribution ledger not connected"},
    {"id": "support", "name": "Community Support", "owner": "Humanitarian Support", "purpose": "Local needs, resources and community assistance.", "status": "Read-only surface live", "function": "Shows the protected support entry point.", "blocked_by": "Safeguarding, verification and case privacy required"},
    {"id": "infrastructure", "name": "Maps, Weather & Navigation", "owner": "Infrastructure", "purpose": "Postcode maps, weather, routes and movement awareness.", "status": "Read-only dashboard live", "function": "Links the existing Infrastructure dashboard.", "blocked_by": "External providers not connected"},
    {"id": "market", "name": "Local Market", "owner": "OAP Market", "purpose": "Products and community commerce.", "status": "Read-only surface live", "function": "Separates listings from regulated payments.", "blocked_by": "Merchant verification, payments and SIKA approval required"},
    {"id": "runner", "name": "SIKA Runner", "owner": "Operations", "purpose": "Bookings, delivery, riders, drivers and local movement.", "status": "Read-only surface live", "function": "Shows operational scope without dispatching work.", "blocked_by": "Identity, payments, location safety and Builder handlers required"},
    {"id": "safety", "name": "Safety & Trust", "owner": "Trust", "purpose": "Reporting, Guardian protection and community standards.", "status": "Protection surface live", "function": "Explains fail-closed safety boundaries.", "blocked_by": "Authenticated reporting workflow not connected"},
    {"id": "identity", "name": "Postcode Identity", "owner": "My World", "purpose": "One OAP identity across every Spot.", "status": "Basic profile form live", "function": "Uses the existing bounded My World profile surface.", "blocked_by": "Production authentication and verification not connected"},
    {"id": "tv-media", "name": "OAP TV & Media", "owner": "OAP TV", "purpose": "Local video, live coverage, music, sport and culture.", "status": "Public surface live", "function": "Links the existing OAP TV front door.", "blocked_by": "Creator publishing workflow not connected"},
    {"id": "membership", "name": "Founder & Membership", "owner": "Membership", "purpose": "Free postcode access and approved membership tiers.", "status": "Read-only surface live", "function": "Displays the membership boundary without charging.", "blocked_by": "Identity, entitlement and regulated payment flow required"},
)
LOCKED_SPOT_CAPABILITY_IDS = tuple(item["id"] for item in SPOT_CAPABILITIES)


def _normalise(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def validate_product_hierarchy(
    products: Iterable[Mapping[str, Any]] = PRODUCT_HIERARCHY,
) -> dict[str, Any]:
    """Reject duplicate products, routes, cycles and missing parents."""

    items = tuple(products)
    ids = [str(item.get("id", "")) for item in items]
    names = [_normalise(str(item.get("name", ""))) for item in items]
    routes = [str(item.get("route", "")) for item in items]
    errors: list[str] = []

    for label, values in (("IDs", ids), ("names", names), ("routes", routes)):
        if len(values) != len(set(values)):
            errors.append(f"Duplicate product {label}")

    known_ids = set(ids)
    for item in items:
        parent = str(item.get("parent_id", ""))
        if parent and parent not in known_ids:
            errors.append(f"Unknown parent for {item.get('id')}")
        if parent == item.get("id"):
            errors.append(f"Product cannot parent itself: {item.get('id')}")

    expected = (
        ("the_spot", ""),
        ("the_link", "the_spot"),
        ("linkup", "the_link"),
    )
    actual = tuple((item.get("id"), item.get("parent_id")) for item in items)
    if actual != expected:
        errors.append("The locked hierarchy must remain The Spot → The Link → LinkUp")

    return {
        "passed": not errors,
        "errors": errors,
        "checks": {
            "products": len(items),
            "duplicate_ids": len(ids) - len(set(ids)),
            "duplicate_names": len(names) - len(set(names)),
            "duplicate_routes": len(routes) - len(set(routes)),
        },
    }


def validate_spot_capabilities(
    capabilities: Iterable[Mapping[str, Any]] = SPOT_CAPABILITIES,
) -> dict[str, Any]:
    """Reject duplicate capability identities, names and ownership gaps."""

    items = tuple(capabilities)
    ids = [str(item.get("id", "")) for item in items]
    names = [_normalise(str(item.get("name", ""))) for item in items]
    errors: list[str] = []
    if len(ids) != len(set(ids)):
        errors.append("Duplicate Spot capability IDs")
    if len(names) != len(set(names)):
        errors.append("Duplicate Spot capability names")
    if any(not item.get("owner") for item in items):
        errors.append("Every Spot capability requires one owning system")
    return {
        "passed": not errors,
        "errors": errors,
        "checks": {
            "capabilities": len(items),
            "duplicate_ids": len(ids) - len(set(ids)),
            "duplicate_names": len(names) - len(set(names)),
        },
    }


def get_public_spot_capability(capability_id: str) -> dict[str, str] | None:
    """Resolve an allowlisted Spot capability without side effects."""

    return next(
        (dict(item) for item in SPOT_CAPABILITIES if item["id"] == capability_id),
        None,
    )


def get_public_product_hierarchy() -> dict[str, Any]:
    """Return the public product map without identities or conversations."""

    return {
        "products": tuple(dict(item) for item in PRODUCT_HIERARCHY),
        "capabilities": tuple(dict(item) for item in SPOT_CAPABILITIES),
        "capability_validation": validate_spot_capabilities(),
        "validation": validate_product_hierarchy(),
        "law": "One World → One Front Door → Many Systems Inside",
        "human_authority": "Human Authority remains final",
        "execution_enabled": False,
    }
