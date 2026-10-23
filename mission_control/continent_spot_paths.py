"""Read-only continent-to-Spot breadcrumbs over existing OAP product hierarchy.

No public routes, geocoding, personal tracking, live claims, or writes.
This module does not change legacy continent grouping used elsewhere.
"""
from __future__ import annotations

from collections.abc import Mapping
from mission_control.products import WORLD_ROOM_LEVELS
from mission_control.languages import CONTINENTS

CONTINENT_IDS = tuple(item["id"] for item in CONTINENTS)
LEVEL_IDS = tuple(item["id"] for item in WORLD_ROOM_LEVELS)


def validate_path(path: Mapping[str, str]) -> tuple[str, ...]:
    errors = []
    continent = str(path.get("continent", "")).strip().lower()
    if continent not in CONTINENT_IDS:
        errors.append("unknown_continent")
    if continent == "antarctica" and path.get("country"):
        errors.append("antarctica_has_no_country_layer")
    if continent != "antarctica" and not str(path.get("country", "")).strip():
        errors.append("country_required")
    for key in ("region", "district", "postcode"):
        if not isinstance(path.get(key, ""), str):
            errors.append("invalid_" + key)
    return tuple(errors)


def breadcrumbs(path: Mapping[str, str]) -> tuple[dict[str, str], ...]:
    errors = validate_path(path)
    if errors:
        raise ValueError(", ".join(errors))
    nodes = [{"level": "earth", "label": "Earth"},
             {"level": "continent", "label": str(path["continent"]).strip().lower()}]
    for level, key in (("country", "country"), ("county-region", "region"),
                       ("borough-district", "district"), ("postcode", "postcode")):
        value = str(path.get(key, "")).strip()
        if value:
            nodes.append({"level": level, "label": value})
    nodes.append({"level": "the-spot", "label": "The Spot"})
    return tuple(nodes)


def existing_product_routes() -> dict[str, str]:
    from mission_control.products import PRODUCT_HIERARCHY
    return {entry["id"]: entry["route"] for entry in PRODUCT_HIERARCHY}


# Compatibility adapter: legacy Caribbean remains its own reporting bucket,
# but belongs under North America in the seven-continent navigation.
_LEGACY_TO_WORLD = {
    "Africa": "africa", "Europe": "europe", "Asia": "asia",
    "North America": "north-america", "South America": "south-america",
    "Caribbean": "north-america", "Oceania": "oceania",
}


def world_continent_for_country(country: str) -> str | None:
    """Resolve a known country without changing legacy reporting categories."""
    from mission_control.world_geography import continent_for_country

    legacy = continent_for_country(country)
    result = _LEGACY_TO_WORLD.get(legacy)
    return result if result in CONTINENT_IDS else None


def country_breadcrumbs(country: str, *, region: str = "",
                        district: str = "", postcode: str = "") -> tuple[dict[str, str], ...]:
    """Fail closed on unknown countries; never infer personal location."""
    continent = world_continent_for_country(country)
    if continent is None:
        raise ValueError("unknown_country")
    return breadcrumbs({"continent": continent, "country": country,
                        "region": region, "district": district, "postcode": postcode})
