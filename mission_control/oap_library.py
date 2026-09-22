"""First-party catalogue for the public OAP Library.

The public Library only points at OAP-owned routes that already exist in this
application.  Private Founder assets remain in ``smi_founder_assets`` and are
never projected into this catalogue.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

LIBRARY_JOURNEY = (
    "Read",
    "Understand",
    "Learn",
    "Create",
    "Preserve",
    "Share",
)

COLLECTIONS: tuple[dict[str, str], ...] = (
    {
        "id": "food-book",
        "name": "Food Book",
        "collection": "Food & Nature",
        "description": (
            "Explore vegetables, nutrients and normal body functions through "
            "an interactive body map."
        ),
        "route": "/library/food-book",
        "access": "member",
        "action": "Enter My World to read",
        "symbol": "🥬",
        "keywords": "food vegetables vitamins nutrition body anatomy health nature",
    },
    {
        "id": "world-languages",
        "name": "World Languages",
        "collection": "People & Language",
        "description": (
            "Learn through continent, country or territory, region, language "
            "and dialect or variant."
        ),
        "route": "/languages",
        "access": "public",
        "action": "Open collection",
        "symbol": "文",
        "keywords": "people language dialect culture countries learning",
    },
    {
        "id": "carnival-intelligence",
        "name": "Carnival Intelligence",
        "collection": "Culture & Chronicle",
        "description": (
            "Read reviewed culture, event, travel and safety knowledge without "
            "opening private Founder systems."
        ),
        "route": "/carnival",
        "access": "public",
        "action": "Open collection",
        "symbol": "◈",
        "keywords": "culture chronicle carnival events history travel safety",
    },
    {
        "id": "our-planet",
        "name": "Our Planet",
        "collection": "Nature",
        "description": (
            "Explore weather, environment, wildlife, green spaces, "
            "sustainability and wellbeing."
        ),
        "route": "/the-spot/nature",
        "access": "public",
        "action": "Open collection",
        "symbol": "◎",
        "keywords": "earth planet nature environment wildlife weather sustainability",
    },
    {
        "id": "places",
        "name": "Places",
        "collection": "Local to Global",
        "description": (
            "Move from postcode to borough, region, country, continent and the "
            "wider world."
        ),
        "route": "/on-any-place",
        "access": "public",
        "action": "Explore places",
        "symbol": "⌾",
        "keywords": "places postcode borough region country continent world map",
    },
)

FOOD_AREAS: tuple[dict[str, str], ...] = (
    {
        "id": "eyes",
        "name": "Eyes",
        "summary": (
            "Carrots and sweet potatoes contain beta-carotene, which the body "
            "can convert into vitamin A. Vitamin A is important for normal vision."
        ),
    },
    {
        "id": "brain",
        "name": "Brain",
        "summary": (
            "Green vegetables and peas can provide folate. Folate supports normal "
            "cell division and blood formation across the body; no single food "
            "makes the brain smarter."
        ),
    },
    {
        "id": "heart",
        "name": "Heart",
        "summary": (
            "Fruit and vegetables can provide potassium and fibre. Heart health "
            "depends on the whole eating pattern and other health factors."
        ),
    },
    {
        "id": "bones",
        "name": "Bones",
        "summary": (
            "Green leafy vegetables are a source of vitamin K. Vitamin K is used "
            "by proteins involved in blood clotting and bone metabolism."
        ),
    },
    {
        "id": "blood",
        "name": "Blood",
        "summary": (
            "Iron is needed to make red blood cells that carry oxygen. Beans and "
            "peas provide plant iron; vitamin C can support absorption of plant iron."
        ),
    },
    {
        "id": "gut",
        "name": "Gut",
        "summary": (
            "Beans, peas and many vegetables provide fibre. Fibre supports normal "
            "digestion and a healthy gut as part of a varied diet."
        ),
    },
)

FOODS: tuple[dict[str, str], ...] = (
    {
        "id": "carrot",
        "name": "Carrot",
        "nutrients": "Beta-carotene · fibre",
        "area": "eyes",
        "colour": "orange",
    },
    {
        "id": "sweet-potato",
        "name": "Sweet potato",
        "nutrients": "Beta-carotene · fibre",
        "area": "eyes",
        "colour": "amber",
    },
    {
        "id": "spinach",
        "name": "Spinach",
        "nutrients": "Folate · vitamin K · plant iron",
        "area": "bones",
        "colour": "green",
    },
    {
        "id": "sweet-pepper",
        "name": "Sweet pepper",
        "nutrients": "Vitamin C",
        "area": "blood",
        "colour": "red",
    },
    {
        "id": "broccoli",
        "name": "Broccoli",
        "nutrients": "Vitamin C · vitamin K · fibre",
        "area": "gut",
        "colour": "emerald",
    },
    {
        "id": "peas",
        "name": "Peas",
        "nutrients": "Fibre · folate · plant protein",
        "area": "gut",
        "colour": "lime",
    },
)

FOOD_SOURCES: tuple[dict[str, str], ...] = (
    {
        "name": "NHS · Why 5 A Day?",
        "url": "https://www.nhs.uk/live-well/eat-well/5-a-day/why-5-a-day/",
    },
    {
        "name": "NHS · Iron",
        "url": "https://www.nhs.uk/conditions/vitamins-and-minerals/iron/",
    },
    {
        "name": "NIH · Vitamin A and carotenoids",
        "url": "https://ods.od.nih.gov/factsheets/VitaminA-HealthProfessional/",
    },
    {
        "name": "NIH · Vitamin K",
        "url": "https://ods.od.nih.gov/factsheets/VitaminK-HealthProfessional/",
    },
    {
        "name": "NIH · Iron",
        "url": "https://ods.od.nih.gov/factsheets/Iron-HealthProfessional/",
    },
)

_ALLOWED_ACCESS = frozenset({"public", "member"})
_SEARCH_CLEANER = re.compile(r"[^a-z0-9]+")


def _normalise(value: object) -> str:
    return _SEARCH_CLEANER.sub(" ", str(value or "").casefold()).strip()


def _search_text(item: Mapping[str, Any]) -> str:
    return " ".join(
        _normalise(item.get(key, ""))
        for key in ("name", "collection", "description", "keywords")
    )


def filter_collections(query: str = "") -> tuple[dict[str, str], ...]:
    """Return bounded public catalogue entries matching every query term."""

    terms = tuple(part for part in _normalise(query)[:80].split() if part)
    if not terms:
        return tuple(dict(item) for item in COLLECTIONS)
    return tuple(
        dict(item)
        for item in COLLECTIONS
        if all(term in _search_text(item) for term in terms)
    )


def validate_catalog() -> dict[str, object]:
    """Fail closed if public catalogue ownership or routes drift."""

    ids = [item.get("id", "") for item in COLLECTIONS]
    routes = [item.get("route", "") for item in COLLECTIONS]
    food_area_ids = {item.get("id", "") for item in FOOD_AREAS}
    errors: list[str] = []

    if LIBRARY_JOURNEY != (
        "Read",
        "Understand",
        "Learn",
        "Create",
        "Preserve",
        "Share",
    ):
        errors.append("Library journey changed")
    if len(ids) != len(set(ids)) or any(not item_id for item_id in ids):
        errors.append("Collection IDs must be present and unique")
    if len(routes) != len(set(routes)) or any(
        not route.startswith("/") or route.startswith("//") for route in routes
    ):
        errors.append("Collection routes must be unique first-party paths")
    if any(item.get("access") not in _ALLOWED_ACCESS for item in COLLECTIONS):
        errors.append("Collection access boundary is invalid")
    if not COLLECTIONS or COLLECTIONS[0].get("id") != "food-book":
        errors.append("Food Book must remain the first Food & Nature collection")
    if any(item.get("area") not in food_area_ids for item in FOODS):
        errors.append("Every food must point to a known body area")

    return {
        "passed": not errors,
        "errors": tuple(errors),
        "collections": len(COLLECTIONS),
        "journey_steps": len(LIBRARY_JOURNEY),
        "founder_assets_exposed": False,
    }
