"""Canonical Map Intelligence manifest.

Presentation contract only. Consequential Movement operations remain in their governed
backend routes and are not enabled by this module.
"""

MAP_INTELLIGENCE_TOOLS: tuple[str, ...] = (
    "Map",
    "Routes",
    "Weather",
    "Travel",
    "Movement",
    "OAP Direct",
    "Booking",
    "Delivery",
)

CANONICAL_PUBLIC_SLUG = "maps-weather-travel"
RETIRED_PUBLIC_SLUGS: tuple[str, ...] = ("movement-delivery",)

TRUTH_LOCKS: tuple[str, ...] = (
    "turn-by-turn routing",
    "confirmed supplier booking",
    "payment",
    "automatic dispatch",
    "live tracking",
)


def map_intelligence_manifest() -> dict[str, object]:
    return {
        "name": "Map Intelligence",
        "slug": CANONICAL_PUBLIC_SLUG,
        "tools": MAP_INTELLIGENCE_TOOLS,
        "retired_public_slugs": RETIRED_PUBLIC_SLUGS,
        "truth_locks": TRUTH_LOCKS,
        "law": "One World. One Front Door. Many Systems Inside.",
    }
