"""Canonical governed hierarchy for The Spot, The Link and LinkUp."""

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
        "purpose": "The public community front door from world scale down to local postcode life.",
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
        "name": "Link Up",
        "route": "/linkup",
        "parent_id": "the_link",
        "purpose": "Protected person-to-person and crew conversation inside The Link.",
        "owner": "Communications",
    },
)

WORLD_ROOM_LEVELS: tuple[dict[str, str], ...] = (
    {"id": "global", "name": "Global", "parent_id": "", "purpose": "Worldwide public community layer."},
    {"id": "continent", "name": "Continent", "parent_id": "global", "purpose": "Continental community layer."},
    {"id": "country", "name": "Country", "parent_id": "continent", "purpose": "Country community layer."},
    {"id": "county-region", "name": "County / Region", "parent_id": "country", "purpose": "County, state, province or regional layer."},
    {"id": "borough-district", "name": "Borough / District", "parent_id": "county-region", "purpose": "Borough, district or equivalent local authority layer."},
    {"id": "postcode", "name": "Postcode", "parent_id": "borough-district", "purpose": "Postcode or equivalent local code layer."},
    {"id": "local", "name": "Local Room", "parent_id": "postcode", "purpose": "Most local public community room."},
)

SPOT_CAPABILITIES: tuple[dict[str, str], ...] = (
    {"id": "pulse", "name": "Pulse", "owner": "OAP World", "purpose": "Community posts and activity.", "status": "Public surface live", "function": "Displays bounded public activity without exposing private data.", "blocked_by": ""},
    {"id": "signal", "name": "Signal", "owner": "OAP Signal", "purpose": "The OAP feed for trusted updates, alerts and announcements.", "status": "Public posting live", "function": "Uses the bounded public Signal feed.", "blocked_by": ""},
    {"id": "postcode-rooms", "name": "World Rooms", "owner": "Communications", "purpose": "Public community rooms organised Global → Continent → Country → County/Region → Borough/District → Postcode → Local.", "status": "Geographic hierarchy defined; postcode posting remains compatibility path", "function": "Keeps the existing bounded room feed while replacing Postcode Rooms as the product identity.", "blocked_by": "Broader geographic posting and protected participation need verified geography; private person-to-person messages stay inside authenticated Link Up"},
    {"id": "events", "name": "Activity / Adventure", "owner": "Events", "purpose": "Local gatherings, sports, culture and activities.", "status": "Directory live", "function": "Provides an approved discovery surface.", "blocked_by": "Bookings require Identity and audited persistence"},
    {"id": "carnival-intelligence", "name": "Carnival Intelligence", "owner": "Events", "purpose": "Official Carnival schedules, maps, travel and safety guidance.", "status": "Read-only scheduled-data surface implemented", "function": "Shows reviewed official information without location collection or live-tracking claims.", "blocked_by": "Live crowds, incidents and moving assets require authorised feeds and separate Human Authority approval"},
    {"id": "discovery", "name": "Explorer", "owner": "Explorer", "purpose": "Places, services and useful geographic information.", "status": "Location lookup live", "function": "Resolves place and postcode hierarchy with bounded provider calls.", "blocked_by": "First-party turn-by-turn routing remains separate"},
    {"id": "businesses", "name": "Local Businesses", "owner": "Business Registry", "purpose": "Business listings, offers and promotion.", "status": "Directory live", "function": "Separates discovery from transactions.", "blocked_by": "Verified merchant onboarding not connected"},
    {"id": "creators", "name": "Creators", "owner": "Creator Identity", "purpose": "Musicians, artists, talent and content creators.", "status": "Directory live", "function": "Provides creator discovery.", "blocked_by": "Verified Creator Identity and publishing workflow not connected"},
    {"id": "community-power", "name": "Community Power", "owner": "Community Power", "purpose": "Contribution, participation and community progress.", "status": "Read-only surface live", "function": "Links contribution awareness without copying its ledger.", "blocked_by": "Audited contribution ledger not connected"},
    {"id": "support", "name": "Community Support", "owner": "Humanitarian Support", "purpose": "Local needs, resources and community assistance.", "status": "Read-only surface live", "function": "Shows the protected support entry point.", "blocked_by": "Safeguarding, verification and case privacy required"},
    {"id": "infrastructure", "name": "Maps, Weather & Travel", "owner": "Infrastructure", "purpose": "Maps, weather, routes and movement awareness.", "status": "Live location and weather lookup", "function": "Resolves hierarchy and current forecast without external browser scripts.", "blocked_by": "First-party turn-by-turn navigation remains separate"},
    {"id": "market", "name": "Market", "owner": "OAP Market", "purpose": "Products and community commerce.", "status": "Live owner-scoped listings", "function": "Authenticated sellers can publish listings; payments remain separate.", "blocked_by": "Checkout requires merchant verification and regulated payments"},
    {"id": "sika", "name": "SIKA", "owner": "SIKA Core", "purpose": "Contribution, trust and internal value records.", "status": "Owner-scoped ledger live", "function": "Shows contribution credits and review requests without representing SIKA as money.", "blocked_by": "Credit awards require audited Human Authority-approved rules"},
    {"id": "runner", "name": "Movement & Delivery", "owner": "Operations", "purpose": "Bookings, delivery, riders, drivers and local movement.", "status": "Read-only surface live", "function": "Shows operational scope without dispatching work.", "blocked_by": "Identity, payments, location safety and Builder handlers required"},
    {"id": "safety", "name": "Safety & Trust", "owner": "Trust", "purpose": "Reporting, Guardian protection and community standards.", "status": "Protection surface live", "function": "Explains fail-closed safety boundaries.", "blocked_by": "Authenticated reporting and escalation workflow not connected"},
    {"id": "identity", "name": "My World", "owner": "My World", "purpose": "One OAP identity and private personal space.", "status": "Managed identity and geographic profile live", "function": "Uses verified owner-scoped identity and location fields.", "blocked_by": "Optional higher-assurance verification remains separate"},
    {"id": "tv-media", "name": "OAP TV & Media", "owner": "OAP TV", "purpose": "Video, live coverage, music, sport and culture.", "status": "Public surface live", "function": "Links the existing OAP TV front door.", "blocked_by": "Creator publishing workflow not connected"},
    {"id": "membership", "name": "Membership", "owner": "Membership", "purpose": "Free public access and optional approved membership/business services.", "status": "Read-only surface live", "function": "Keeps public browsing free and separates future commercial services.", "blocked_by": "Verified business identity, entitlement and regulated payment flow required"},
    {"id": "languages", "name": "World Languages", "owner": "OAP World", "purpose": "Language learning aligned to real continents, countries, regions, languages and variants.", "status": "Starter public surface live; global expansion in progress", "function": "Uses Continent → Country/Territory → Region → Language → Dialect/Variant → Lessons as the canonical learning hierarchy.", "blocked_by": "Full country/language catalogue, progress, speech and Link Up multilingual tools require implementation plus privacy, youth-safety and accuracy gates"},
)
LOCKED_SPOT_CAPABILITY_IDS = tuple(item["id"] for item in SPOT_CAPABILITIES)

PUBLIC_SPOT_CAPABILITIES: tuple[dict[str, str], ...] = (
    {"source_id": "pulse", "slug": "pulse", "name": "Pulse", "purpose": "See community posts and activity."},
    {"source_id": "signal", "slug": "signal", "name": "Signal", "purpose": "Follow the OAP feed, trusted updates, alerts and announcements."},
    {"source_id": "postcode-rooms", "slug": "postcode-rooms", "name": "World Rooms", "purpose": "Move from Global to Continent, Country, County/Region, Borough/District, Postcode and Local rooms."},
    {"source_id": "events", "slug": "events", "name": "Activity / Adventure", "purpose": "Find gatherings, sport, culture and things to do."},
    {"source_id": "carnival-intelligence", "slug": "carnival", "name": "Carnival Intelligence", "purpose": "Use reviewed Carnival schedules, maps, travel and safety guidance."},
    {"source_id": "discovery", "slug": "discovery", "name": "Explorer", "purpose": "Explore useful places and services."},
    {"source_id": "businesses", "slug": "businesses", "name": "Local Businesses", "purpose": "Discover businesses, offers and services."},
    {"source_id": "creators", "slug": "creators", "name": "Creators", "purpose": "Find musicians, artists and talent."},
    {"source_id": "community-power", "slug": "community-progress", "name": "Community Power", "purpose": "See participation and positive community action."},
    {"source_id": "support", "slug": "support", "name": "Community Support", "purpose": "Find help, resources and support."},
    {"source_id": "infrastructure", "slug": "maps-weather-travel", "name": "Maps, Weather & Travel", "purpose": "Plan routes and stay aware of local conditions."},
    {"source_id": "market", "slug": "market", "name": "Market", "purpose": "Explore products and community commerce."},
    {"source_id": "sika", "slug": "sika", "name": "SIKA", "purpose": "View contribution and trust-value records."},
    {"source_id": "runner", "slug": "movement-delivery", "name": "Movement & Delivery", "purpose": "Explore bookings, delivery and travel."},
    {"source_id": "safety", "slug": "safety", "name": "Safety & Trust", "purpose": "Find community standards and reporting support."},
    {"source_id": "identity", "slug": "my-world", "name": "My World", "purpose": "Your private OAP identity and personal space."},
    {"source_id": "tv-media", "slug": "tv-media", "name": "OAP TV & Media", "purpose": "Watch video, music, sport and culture."},
    {"source_id": "membership", "slug": "membership", "name": "Membership", "purpose": "Explore free public access and optional approved services."},
    {"source_id": "languages", "slug": "languages", "name": "World Languages", "purpose": "Learn through Continent → Country/Territory → Region → Language → Dialect/Variant → Lessons."},
)


def _normalise(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def validate_product_hierarchy(products: Iterable[Mapping[str, Any]] = PRODUCT_HIERARCHY) -> dict[str, Any]:
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
    expected = (("the_spot", ""), ("the_link", "the_spot"), ("linkup", "the_link"))
    actual = tuple((item.get("id"), item.get("parent_id")) for item in items)
    if actual != expected:
        errors.append("The locked hierarchy must remain The Spot → The Link → Link Up")
    return {"passed": not errors, "errors": errors, "checks": {"products": len(items), "duplicate_ids": len(ids)-len(set(ids)), "duplicate_names": len(names)-len(set(names)), "duplicate_routes": len(routes)-len(set(routes))}}


def validate_world_room_levels(levels: Iterable[Mapping[str, Any]] = WORLD_ROOM_LEVELS) -> dict[str, Any]:
    items = tuple(levels)
    ids = [str(item.get("id", "")) for item in items]
    errors: list[str] = []
    if len(ids) != len(set(ids)):
        errors.append("Duplicate World Room levels")
    expected = ("global", "continent", "country", "county-region", "borough-district", "postcode", "local")
    if tuple(ids) != expected:
        errors.append("World Rooms hierarchy changed")
    return {"passed": not errors, "errors": errors, "checks": {"levels": len(items)}}


def validate_spot_capabilities(capabilities: Iterable[Mapping[str, Any]] = SPOT_CAPABILITIES) -> dict[str, Any]:
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
    return {"passed": not errors, "errors": errors, "checks": {"capabilities": len(items), "duplicate_ids": len(ids)-len(set(ids)), "duplicate_names": len(names)-len(set(names))}}


def _public_spot_copy(item: Mapping[str, str]) -> dict[str, str]:
    return {"slug": str(item["slug"]), "name": str(item["name"]), "purpose": str(item["purpose"])}


def get_public_spot_slug(capability_id: str) -> str | None:
    return next((str(item["slug"]) for item in PUBLIC_SPOT_CAPABILITIES if item["source_id"] == capability_id), None)


def get_public_spot_capability(capability_slug: str) -> dict[str, str] | None:
    return next((_public_spot_copy(item) for item in PUBLIC_SPOT_CAPABILITIES if item["slug"] == capability_slug), None)


def get_public_product_hierarchy() -> dict[str, Any]:
    return {
        "products": tuple({"id": item["id"], "name": item["name"], "purpose": item["purpose"]} for item in PRODUCT_HIERARCHY),
        "capabilities": tuple(_public_spot_copy(item) for item in PUBLIC_SPOT_CAPABILITIES),
        "world_rooms": tuple(dict(item) for item in WORLD_ROOM_LEVELS),
        "world_rooms_validation": validate_world_room_levels(),
        "law": "One World. One Front Door. Many Systems Inside.",
    }
