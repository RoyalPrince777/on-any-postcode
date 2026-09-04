"""Civilian humanitarian Map Intelligence for OAP emergency response.

This module binds International Humanitarian Connectivity Intelligence to the
existing first-party Movement / Map Intelligence architecture. It prepares
privacy-preserving map views and readiness information for civilian life safety,
medical access, essential aid, family reunification and connectivity resilience.
It does not publish precise civilian locations, expose military overlays, perform
surveillance, or claim production navigation before the owned map store, route
engine and live observations are proven.
"""

from __future__ import annotations

from typing import Any

from .movement_intelligence import movement_intelligence_status

CANONICAL_SPATIAL_HIERARCHY: tuple[str, ...] = (
    "Spot",
    "Postcode / Local Equivalent",
    "Borough / District",
    "Region / County",
    "Country",
    "Continent",
    "Global",
)

HUMANITARIAN_MAP_LAYERS: tuple[dict[str, str], ...] = (
    {
        "id": "administrative_boundaries",
        "name": "Administrative Boundaries",
        "purpose": "Resolve EARTH OUR TURF local-to-global humanitarian operating context.",
    },
    {
        "id": "medical",
        "name": "Medical Access",
        "purpose": "Represent verified civilian hospitals, clinics and emergency medical access points.",
    },
    {
        "id": "shelter",
        "name": "Shelter",
        "purpose": "Represent verified public civilian shelter and temporary accommodation information.",
    },
    {
        "id": "water_food",
        "name": "Water & Food",
        "purpose": "Represent verified civilian water, food and essential-aid access points.",
    },
    {
        "id": "connectivity",
        "name": "Connectivity",
        "purpose": "Show bounded connectivity availability, outages and cold-spot evidence.",
    },
    {
        "id": "hazards",
        "name": "Hazards",
        "purpose": "Represent verified hazards and areas requiring civilian caution or avoidance.",
    },
    {
        "id": "disruptions",
        "name": "Route Disruptions",
        "purpose": "Represent verified road, bridge, transit and access disruptions without military overlays.",
    },
    {
        "id": "accessibility",
        "name": "Accessible Movement",
        "purpose": "Prefer accessible civilian routes and places where evidence supports them.",
    },
    {
        "id": "family_reunification",
        "name": "Family Reunification",
        "purpose": "Support privacy-minimised reunification areas without publishing individual locations.",
    },
    {
        "id": "safe_route",
        "name": "Civilian Safe-Route Readiness",
        "purpose": "Prepare bounded route requirements while refusing false claims of verified-safe navigation.",
    },
)

EVIDENCE_GATED_LAYERS = frozenset(
    {
        "medical",
        "shelter",
        "water_food",
        "connectivity",
        "hazards",
        "disruptions",
        "accessibility",
        "family_reunification",
        "safe_route",
    }
)


def _supported_layer_ids() -> tuple[str, ...]:
    return tuple(layer["id"] for layer in HUMANITARIAN_MAP_LAYERS)


def prepare_humanitarian_map_view(
    *,
    area: str,
    layers: tuple[str, ...] | list[str] = (),
    source_verified: bool = False,
    precise_location_requested: bool = False,
    public_share: bool = False,
) -> dict[str, Any]:
    """Prepare a civilian map view without claiming route or data readiness."""

    clean_area = " ".join(str(area or "").split()).strip()
    if not clean_area:
        return {
            "accepted": False,
            "reason": "area_required",
            "public_share": False,
            "precise_location_stored": False,
            "human_authority_final": True,
        }

    supported = _supported_layer_ids()
    requested = tuple(dict.fromkeys(str(item).strip().casefold() for item in layers if str(item).strip()))
    if not requested:
        requested = (
            "administrative_boundaries",
            "medical",
            "shelter",
            "water_food",
            "connectivity",
            "hazards",
            "disruptions",
            "accessibility",
            "safe_route",
        )
    unsupported = tuple(item for item in requested if item not in supported)
    if unsupported:
        return {
            "accepted": False,
            "reason": "unsupported_map_layer",
            "unsupported_layers": unsupported,
            "public_share": False,
            "precise_location_stored": False,
            "human_authority_final": True,
        }

    if public_share and precise_location_requested:
        return {
            "accepted": False,
            "reason": "precise_civilian_location_publication_blocked",
            "public_share": False,
            "precise_location_stored": False,
            "human_authority_final": True,
        }

    movement = movement_intelligence_status()
    gated = tuple(item for item in requested if item in EVIDENCE_GATED_LAYERS)
    evidence_ready = bool(source_verified) or not gated
    return {
        "accepted": evidence_ready,
        "reason": "prepared" if evidence_ready else "verified_source_required",
        "area": clean_area,
        "requested_layers": requested,
        "source_verified": bool(source_verified),
        "map_architecture_ready": bool(movement["architecture_passed"]),
        "production_navigation_ready": bool(movement["production_navigation_ready"]),
        "navigation_claimed_safe": False,
        "route_recommendation_only": True,
        "public_share": bool(public_share and not precise_location_requested),
        "precise_location_requested": bool(precise_location_requested),
        "precise_location_stored": False,
        "precise_civilian_location_public": False,
        "individual_tracking": False,
        "crowd_tracking": False,
        "military_overlays": False,
        "targeting": False,
        "surveillance": False,
        "proprietary_map_api_required": False,
        "autonomous_navigation": False,
        "human_authority_final": True,
    }


def humanitarian_map_intelligence_status() -> dict[str, Any]:
    """Return production architecture status for humanitarian Map Intelligence."""

    movement = movement_intelligence_status()
    first_party = movement["first_party_policy"]
    layer_ids = _supported_layer_ids()
    architecture_ready = (
        bool(movement["architecture_passed"])
        and len(layer_ids) == len(set(layer_ids))
        and first_party["production_proprietary_map_api_allowed"] is False
        and first_party["production_proprietary_routing_api_allowed"] is False
        and first_party["oap_controlled_map_store_required"] is True
        and first_party["oap_controlled_route_engine_required"] is True
        and first_party["offline_navigation_target"] is True
    )
    return {
        "id": "humanitarian_map_intelligence",
        "name": "Humanitarian Map Intelligence",
        "mode": "civilian_emergency_map_production",
        "demo_mode": False,
        "architecture_ready": architecture_ready,
        "map_intelligence_bound": True,
        "movement_intelligence": movement,
        "canonical_spatial_binding": movement["canonical_spatial_binding"],
        "spatial_hierarchy": CANONICAL_SPATIAL_HIERARCHY,
        "layers": HUMANITARIAN_MAP_LAYERS,
        "layer_count": len(HUMANITARIAN_MAP_LAYERS),
        "first_party_policy": dict(first_party),
        "production_navigation_ready": bool(movement["production_navigation_ready"]),
        "live_humanitarian_data_feeds_claim": False,
        "verified_sources_required": True,
        "offline_navigation_target": True,
        "precise_civilian_location_public": False,
        "individual_tracking": False,
        "crowd_tracking": False,
        "military_overlays": False,
        "targeting": False,
        "surveillance": False,
        "autonomous_navigation": False,
        "civilian_only": True,
        "human_authority_final": True,
        "truth_boundary": (
            "Humanitarian Map Intelligence is production architecture bound to OAP Movement "
            "Intelligence. It does not claim live humanitarian map feeds or production-safe "
            "navigation until the OAP-controlled map store, route engine, verified observations "
            "and runtime navigation gates pass."
        ),
    }
