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
        "sources": "nih-vitamin-a",
    },
    {
        "id": "brain",
        "name": "Brain",
        "summary": (
            "Green vegetables and peas can provide folate. Folate helps the body "
            "form healthy red blood cells; no single food makes the brain smarter."
        ),
        "sources": "nhs-five-a-day,nhs-folate",
    },
    {
        "id": "heart",
        "name": "Heart",
        "summary": (
            "Fruit and vegetables can provide potassium and fibre. Heart health "
            "depends on the whole eating pattern and other health factors."
        ),
        "sources": "nhs-five-a-day",
    },
    {
        "id": "bones",
        "name": "Bones",
        "summary": (
            "Green leafy vegetables are a source of vitamin K. Vitamin K is used "
            "by proteins involved in blood clotting and bone metabolism."
        ),
        "sources": "nih-vitamin-k",
    },
    {
        "id": "blood",
        "name": "Blood",
        "summary": (
            "Iron is needed to make red blood cells that carry oxygen. Beans and "
            "peas provide plant iron; vitamin C can support absorption of plant iron."
        ),
        "sources": "nhs-iron,nih-iron,nhs-vitamin-c",
    },
    {
        "id": "gut",
        "name": "Gut",
        "summary": (
            "Beans, peas and many vegetables provide fibre. Fibre supports normal "
            "digestion and a healthy gut as part of a varied diet."
        ),
        "sources": "nhs-five-a-day",
    },
)

FOODS: tuple[dict[str, str], ...] = (
    {
        "id": "carrot",
        "name": "Carrot",
        "nutrients": "Beta-carotene · fibre",
        "area": "eyes",
        "colour": "orange",
        "sources": "nih-vitamin-a",
    },
    {
        "id": "sweet-potato",
        "name": "Sweet potato",
        "nutrients": "Beta-carotene · fibre",
        "area": "eyes",
        "colour": "amber",
        "sources": "nih-vitamin-a",
    },
    {
        "id": "spinach",
        "name": "Spinach",
        "nutrients": "Folate · vitamin K · plant iron",
        "area": "bones",
        "colour": "green",
        "sources": "nih-vitamin-k,nhs-iron,nhs-folate",
    },
    {
        "id": "sweet-pepper",
        "name": "Sweet pepper",
        "nutrients": "Vitamin C",
        "area": "blood",
        "colour": "red",
        "sources": "nhs-vitamin-c,nhs-iron",
    },
    {
        "id": "broccoli",
        "name": "Broccoli",
        "nutrients": "Vitamin C · vitamin K · fibre",
        "area": "gut",
        "colour": "emerald",
        "sources": "nhs-five-a-day,nih-vitamin-k,nhs-vitamin-c",
    },
    {
        "id": "peas",
        "name": "Peas",
        "nutrients": "Fibre · folate · plant protein",
        "area": "gut",
        "colour": "lime",
        "sources": "nhs-five-a-day,nhs-folate",
    },
)

FOOD_SOURCES: tuple[dict[str, str], ...] = (
    {
        "id": "nhs-five-a-day",
        "name": "NHS · Why 5 A Day?",
        "url": "https://www.nhs.uk/live-well/eat-well/5-a-day/why-5-a-day/",
    },
    {
        "id": "nhs-iron",
        "name": "NHS · Iron",
        "url": "https://www.nhs.uk/conditions/vitamins-and-minerals/iron/",
    },
    {
        "id": "nih-vitamin-a",
        "name": "NIH · Vitamin A and carotenoids",
        "url": "https://ods.od.nih.gov/factsheets/VitaminA-HealthProfessional/",
    },
    {
        "id": "nih-vitamin-k",
        "name": "NIH · Vitamin K",
        "url": "https://ods.od.nih.gov/factsheets/VitaminK-HealthProfessional/",
    },
    {
        "id": "nih-iron",
        "name": "NIH · Iron",
        "url": "https://ods.od.nih.gov/factsheets/Iron-HealthProfessional/",
    },
    {
        "id": "nhs-folate",
        "name": "NHS · B vitamins and folic acid",
        "url": "https://www.nhs.uk/conditions/vitamins-and-minerals/vitamin-b/",
    },
    {
        "id": "nhs-vitamin-c",
        "name": "NHS · Vitamin C",
        "url": "https://www.nhs.uk/conditions/vitamins-and-minerals/vitamin-c/",
    },
)

FOOD_CHAPTERS: tuple[dict[str, str], ...] = (
    {
        "id": "whole-food",
        "title": "Food supports the whole body",
        "copy": (
            "Vegetables contain combinations of nutrients and fibre. The body uses "
            "those nutrients across connected systems, so this book does not label "
            "one vegetable as a treatment for one organ."
        ),
        "sources": "nhs-five-a-day",
    },
    {
        "id": "nutrient-jobs",
        "title": "Nutrients have different jobs",
        "copy": (
            "Vitamin A contributes to normal vision, vitamin K is used by proteins "
            "involved in blood clotting and bone metabolism, and iron is needed to "
            "make red blood cells that carry oxygen."
        ),
        "sources": "nih-vitamin-a,nih-vitamin-k,nhs-iron",
    },
    {
        "id": "source-trail",
        "title": "Keep the source with the learning",
        "copy": (
            "Every learning card keeps the official reading links used for its fact. "
            "Your own reflection stays visibly separate from the sourced statement."
        ),
        "sources": "nhs-five-a-day,nih-vitamin-a,nih-vitamin-k,nhs-iron",
    },
)

FOOD_CHECKPOINTS: tuple[dict[str, object], ...] = (
    {
        "id": "whole-body",
        "question": "Which statement matches Food Book?",
        "options": (
            ("whole-body", "Food supports the whole body as part of an overall diet."),
            ("single-organ", "One vegetable treats one organ by itself."),
        ),
        "answer": "whole-body",
    },
    {
        "id": "vision",
        "question": "Which nutrient is important for normal vision?",
        "options": (("vitamin-a", "Vitamin A"), ("iron", "Iron")),
        "answer": "vitamin-a",
    },
    {
        "id": "iron",
        "question": "What does iron help the body make?",
        "options": (
            ("red-blood-cells", "Red blood cells that carry oxygen"),
            ("single-organ-cure", "A cure aimed at one organ"),
        ),
        "answer": "red-blood-cells",
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


def _source_ids(value: object) -> tuple[str, ...]:
    return tuple(part.strip() for part in str(value or "").split(",") if part.strip())


def food_learning_card(food_id: object, area_id: object) -> dict[str, object]:
    """Build one immutable, source-bound Food Book fact from catalogue IDs."""

    food_key = _normalise(food_id).replace(" ", "-")
    area_key = _normalise(area_id).replace(" ", "-")
    food = next((item for item in FOODS if item["id"] == food_key), None)
    area = next((item for item in FOOD_AREAS if item["id"] == area_key), None)
    if food is None or area is None or food["area"] != area["id"]:
        raise ValueError("food_area_pair_required")

    source_lookup = {item["id"]: item for item in FOOD_SOURCES}
    source_ids = tuple(
        dict.fromkeys((*_source_ids(food["sources"]), *_source_ids(area["sources"])))
    )
    sources = tuple(dict(source_lookup[source_id]) for source_id in source_ids)
    return {
        "book_id": "food-book",
        "food_id": food["id"],
        "food_name": food["name"],
        "area_id": area["id"],
        "area_name": area["name"],
        "fact": f"{food['name']}: {food['nutrients']}. {area['summary']}",
        "sources": sources,
    }


def validate_catalog() -> dict[str, object]:
    """Fail closed if public catalogue ownership or routes drift."""

    ids = [item.get("id", "") for item in COLLECTIONS]
    routes = [item.get("route", "") for item in COLLECTIONS]
    food_area_ids = {item.get("id", "") for item in FOOD_AREAS}
    source_ids = {item.get("id", "") for item in FOOD_SOURCES}
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
    if len(source_ids) != len(FOOD_SOURCES) or "" in source_ids:
        errors.append("Food source IDs must be present and unique")
    sourced_items = (*FOOD_AREAS, *FOODS, *FOOD_CHAPTERS)
    if any(
        not _source_ids(item.get("sources"))
        or any(source_id not in source_ids for source_id in _source_ids(item.get("sources")))
        for item in sourced_items
    ):
        errors.append("Every Food Book claim must point to a known source")
    if any(
        not checkpoint.get("answer")
        or checkpoint.get("answer")
        not in {option[0] for option in checkpoint.get("options", ())}
        for checkpoint in FOOD_CHECKPOINTS
    ):
        errors.append("Every Food Book checkpoint must have one known answer")

    return {
        "passed": not errors,
        "errors": tuple(errors),
        "collections": len(COLLECTIONS),
        "journey_steps": len(LIBRARY_JOURNEY),
        "founder_assets_exposed": False,
    }
