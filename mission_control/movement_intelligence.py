"""First-party Movement Intelligence for OAP.

This module defines the owned intelligence boundary for maps, positioning,
routing, traffic, roads, transit, places and journey prediction. Production
navigation must not depend on proprietary third-party map/routing APIs.
Consequential physical-world actions remain governed by Aegis, Living Kernel
and Human Authority.
"""
from __future__ import annotations

from typing import Any

MOVEMENT_INTELLIGENCE_COMPONENTS: tuple[dict[str, str], ...] = (
    {"id": "atlas", "name": "Atlas Intelligence", "purpose": "Canonical OAP-controlled world graph for roads, paths, buildings, places and geographic hierarchy."},
    {"id": "position", "name": "Position Intelligence", "purpose": "Fuse consented GNSS and device sensor observations into bounded map-matched position."},
    {"id": "route", "name": "Route Intelligence", "purpose": "Compute walking, cycling, road, delivery and accessibility routes on OAP-controlled graph data."},
    {"id": "traffic", "name": "Traffic Intelligence", "purpose": "Learn congestion and disruption from consented OAP observations, verified incidents and historical movement outcomes."},
    {"id": "road", "name": "Road Intelligence", "purpose": "Represent lanes, junctions, restrictions, hazards, gradients, surfaces, access and speed rules with provenance."},
    {"id": "transit", "name": "Transit Intelligence", "purpose": "Represent governed public-transport topology, schedules and service observations without outsourcing route decisions."},
    {"id": "place", "name": "Place Intelligence", "purpose": "Resolve OAP places through Postcode, Spot, Borough, County, Country, Continent and Earth hierarchy."},
    {"id": "prediction", "name": "Journey Prediction", "purpose": "Estimate ETA, delay, congestion and route confidence from owned observations and HRM history."},
    {"id": "safety", "name": "Movement Safety", "purpose": "Apply Aegis safety, privacy, certification and physical-world execution boundaries."},
    {"id": "memory", "name": "Movement Memory", "purpose": "Record verified route outcomes and bounded movement learning through HRM rather than a competing memory store."},
    {"id": "agents", "name": "Movement Agents", "purpose": "Coordinate specialised governed movement workers through the existing Agent Registry."},
)

FIRST_PARTY_POLICY: dict[str, Any] = {
    "production_proprietary_map_api_allowed": False,
    "production_proprietary_routing_api_allowed": False,
    "external_provider_required_for_route_decision": False,
    "oap_controlled_map_store_required": True,
    "oap_controlled_route_engine_required": True,
    "offline_navigation_target": True,
    "human_authority_final": True,
}

INTELLIGENCE_LOOP: tuple[str, ...] = (
    "sense", "observe", "map_context", "predict", "route", "judge_risk",
    "recommend", "authorise", "navigate", "observe_result", "hrm_learn",
)

GOVERNANCE: dict[str, str] = {
    "think": "SMI",
    "protect": "Aegis",
    "authorise": "Living Kernel",
    "remember": "HRM",
    "verify": "Registry",
    "review": "War Room",
    "execute": "Agent Registry",
    "final_authority": "Human Authority",
}


def validate_movement_intelligence() -> dict[str, Any]:
    ids = [component["id"] for component in MOVEMENT_INTELLIGENCE_COMPONENTS]
    duplicates = sorted({item for item in ids if ids.count(item) > 1})
    errors: list[str] = []
    if duplicates:
        errors.append("Duplicate Movement Intelligence components: " + ", ".join(duplicates))
    if FIRST_PARTY_POLICY["production_proprietary_map_api_allowed"]:
        errors.append("Proprietary production map APIs must remain disabled")
    if FIRST_PARTY_POLICY["production_proprietary_routing_api_allowed"]:
        errors.append("Proprietary production routing APIs must remain disabled")
    if not FIRST_PARTY_POLICY["oap_controlled_map_store_required"]:
        errors.append("OAP-controlled map storage is required")
    if not FIRST_PARTY_POLICY["oap_controlled_route_engine_required"]:
        errors.append("OAP-controlled routing is required")
    if not FIRST_PARTY_POLICY["human_authority_final"]:
        errors.append("Human Authority must remain final")
    return {"passed": not errors, "errors": errors, "components": len(ids), "policy": dict(FIRST_PARTY_POLICY)}


def movement_intelligence_status() -> dict[str, Any]:
    validation = validate_movement_intelligence()
    return {
        "name": "OAP Movement Intelligence",
        "architecture_passed": validation["passed"],
        "component_count": len(MOVEMENT_INTELLIGENCE_COMPONENTS),
        "components": tuple(dict(item) for item in MOVEMENT_INTELLIGENCE_COMPONENTS),
        "intelligence_loop": INTELLIGENCE_LOOP,
        "governance": dict(GOVERNANCE),
        "first_party_policy": dict(FIRST_PARTY_POLICY),
        "production_navigation_ready": False,
        "readiness_reason": "Owned map store, route engine, live observations and runtime verification must pass before production navigation is enabled.",
    }
