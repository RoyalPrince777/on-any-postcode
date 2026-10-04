"""OAP Planetary Intelligence seven-domain registry and bounded status model.

The seven operational domains are physical/infrastructure operating environments.
Cyber is deliberately cross-cutting rather than an eighth domain. SMI remains the
single fusion brain above the domain model.

This module performs no collection, network calls, control actions or autonomous
execution. It describes governed capability boundaries for Founder surfaces.
"""
from __future__ import annotations

from typing import Any

DOMAIN_ORDER = (
    "underground",
    "water",
    "land",
    "air",
    "space",
    "spectrum",
    "energy",
)

DOMAINS: dict[str, dict[str, Any]] = {
    "underground": {
        "name": "Underground Intelligence",
        "icon": "🕳️",
        "purpose": "Subsurface geology, groundwater, tunnels, buried infrastructure, seismic and ground-risk context.",
        "signals": ("geology", "groundwater", "tunnels", "utilities", "seismic", "ground hazards"),
    },
    "water": {
        "name": "Water Intelligence",
        "icon": "🌊",
        "purpose": "Oceans, rivers, lakes, reservoirs, flood, coastal, port and subsea infrastructure context.",
        "signals": ("rivers", "oceans", "flooding", "tides", "water quality", "subsea infrastructure"),
    },
    "land": {
        "name": "Land Intelligence",
        "icon": "🌍",
        "purpose": "Terrain, postcode geography, roads, buildings, agriculture, environment and surface infrastructure.",
        "signals": ("terrain", "postcodes", "roads", "buildings", "agriculture", "land use"),
    },
    "air": {
        "name": "Air Intelligence",
        "icon": "🌬️",
        "purpose": "Atmosphere, weather, aviation, drones, air quality and airborne sensing context.",
        "signals": ("weather", "aviation", "drones", "air quality", "wind", "atmospheric hazards"),
    },
    "space": {
        "name": "Space Intelligence",
        "icon": "🛰️",
        "purpose": "Satellites, Earth observation, navigation, orbital systems, space weather and debris context.",
        "signals": ("satellites", "earth observation", "GNSS", "orbits", "space weather", "debris"),
    },
    "spectrum": {
        "name": "Spectrum Intelligence",
        "icon": "📡",
        "purpose": "RF, radar, cellular, 5G/6G, ISAC, GNSS signal and electromagnetic context across domains.",
        "signals": ("RF", "radar", "cellular", "5G/6G", "ISAC", "interference"),
    },
    "energy": {
        "name": "Energy Intelligence",
        "icon": "⚡",
        "purpose": "Generation, grids, storage, fuel, renewables, charging and energy-resilience context.",
        "signals": ("generation", "grid", "storage", "fuel", "renewables", "charging"),
    },
}


DOMAIN_COMMANDS: dict[str, dict[str, tuple[str, ...]]] = {
    "underground": {
        "observe": ("geology", "groundwater", "seismic activity"),
        "assets": ("tunnels", "buried utilities", "foundations"),
        "risks": ("subsidence", "sinkholes", "contamination"),
        "forecasts": ("ground movement", "water-table change", "infrastructure stress"),
        "dependencies": ("land", "water", "energy", "cyber"),
    },
    "water": {
        "observe": ("rivers", "oceans", "reservoirs"),
        "assets": ("ports", "dams", "subsea cables"),
        "risks": ("flooding", "erosion", "water quality"),
        "forecasts": ("tides", "flood risk", "coastal change"),
        "dependencies": ("land", "air", "energy", "cyber"),
    },
    "land": {
        "observe": ("terrain", "postcodes", "land use"),
        "assets": ("roads", "buildings", "agriculture"),
        "risks": ("surface disruption", "wildfire", "infrastructure damage"),
        "forecasts": ("mobility pressure", "land-use change", "environmental stress"),
        "dependencies": ("underground", "water", "air", "energy", "cyber"),
    },
    "air": {
        "observe": ("weather", "air quality", "aviation"),
        "assets": ("airspace", "airports", "airborne sensors"),
        "risks": ("storms", "poor visibility", "pollution"),
        "forecasts": ("wind", "storm path", "atmospheric conditions"),
        "dependencies": ("land", "water", "space", "spectrum", "cyber"),
    },
    "space": {
        "observe": ("satellites", "orbits", "space weather"),
        "assets": ("earth observation", "GNSS", "communications"),
        "risks": ("debris", "signal loss", "space-weather disruption"),
        "forecasts": ("orbital conjunction", "coverage windows", "space weather"),
        "dependencies": ("air", "spectrum", "energy", "cyber"),
    },
    "spectrum": {
        "observe": ("RF", "radar", "cellular"),
        "assets": ("5G/6G", "ISAC", "GNSS signals"),
        "risks": ("interference", "coverage loss", "signal congestion"),
        "forecasts": ("propagation", "capacity pressure", "interference risk"),
        "dependencies": ("air", "space", "energy", "cyber"),
    },
    "energy": {
        "observe": ("generation", "grid", "storage"),
        "assets": ("renewables", "fuel", "charging"),
        "risks": ("outage", "capacity shortfall", "supply disruption"),
        "forecasts": ("demand", "resilience", "generation balance"),
        "dependencies": ("land", "water", "spectrum", "cyber"),
    },
}

CROSS_DOMAIN_RELATIONSHIPS = (
    {
        "id": "storm-flood-grid",
        "name": "Storm → Flood → Grid",
        "domains": ("air", "water", "land", "energy"),
        "purpose": "Correlate atmospheric hazards with flooding, surface disruption and energy resilience.",
    },
    {
        "id": "space-spectrum-navigation",
        "name": "Space → Spectrum → Navigation",
        "domains": ("space", "spectrum", "land", "air"),
        "purpose": "Correlate satellite, RF and navigation dependencies across surface and aviation systems.",
    },
    {
        "id": "groundwater-infrastructure",
        "name": "Groundwater → Underground → Land",
        "domains": ("water", "underground", "land"),
        "purpose": "Correlate groundwater change with subsurface and surface infrastructure risk.",
    },
    {
        "id": "energy-cyber-dependency",
        "name": "Energy ↔ Cyber Dependency",
        "domains": ("energy", "spectrum", "land"),
        "purpose": "Represent the physical dependencies behind digitally controlled energy systems.",
    },
)

CYBER_FABRIC = {
    "name": "Cyber Fabric",
    "icon": "💻",
    "role": "Digital nervous system across all seven domains",
    "covers": (
        "networks",
        "software",
        "devices",
        "identities",
        "APIs",
        "databases",
        "control systems",
        "digital twins",
        "cybersecurity",
    ),
}

SMI_FUSION = {
    "name": "SMI Fusion",
    "icon": "🧠",
    "role": "Single governed fusion brain above the seven domains and Cyber Fabric",
    "cycle": (
        "observe",
        "detect",
        "identify",
        "correlate",
        "understand",
        "forecast",
        "recommend",
    ),
    "truth_states": ("observed", "correlated", "inferred", "forecast", "unknown"),
}


def domain_status(domain_id: str) -> dict[str, Any]:
    """Return a bounded truth-safe status for one operational domain."""
    if domain_id not in DOMAINS:
        raise KeyError(domain_id)
    domain = DOMAINS[domain_id]
    command = DOMAIN_COMMANDS[domain_id]
    return {
        "id": domain_id,
        **domain,
        "command": command,
        "command_sections": tuple(command),
        "architecture_ready": True,
        "architecture_light": "🟢",
        "dashboard_ready": True,
        "dashboard_light": "🟢",
        "live_external_sources_proven": False,
        "live_external_light": "🟣",
        "control_execution_granted": False,
        "network_calls_made": False,
        "human_authority_final": True,
        "truth_boundary": (
            "Dashboard and domain model are implemented. Live external sensing, "
            "hardware control and universal coverage require separate source-specific proof."
        ),
    }


def status() -> dict[str, Any]:
    """Return the complete seven-domain + Cyber + SMI architecture."""
    domains = tuple(domain_status(domain_id) for domain_id in DOMAIN_ORDER)
    return {
        "component": "OAP Planetary Intelligence",
        "operational_domain_count": len(domains),
        "operational_domains": domains,
        "cross_domain_relationship_count": len(CROSS_DOMAIN_RELATIONSHIPS),
        "cross_domain_relationships": CROSS_DOMAIN_RELATIONSHIPS,
        "cyber_fabric": {
            **CYBER_FABRIC,
            "cross_cutting": True,
            "domain_ids": DOMAIN_ORDER,
            "architecture_ready": True,
            "architecture_light": "🟢",
            "live_control_proven": False,
            "live_control_light": "🟣",
            "execution_granted": False,
        },
        "smi_fusion": {
            **SMI_FUSION,
            "single_brain": True,
            "architecture_ready": True,
            "architecture_light": "🟢",
            "external_live_fusion_proven": False,
            "external_live_light": "🟣",
            "execution_granted": False,
            "approval_granted": False,
        },
        "governance_path": (
            "7 Domains",
            "Cyber Fabric",
            "SMI Fusion",
            "Guardian / Oversight",
            "Green Gate",
            "Human Final Authority",
        ),
        "architecture_ready": True,
        "architecture_light": "🟢",
        "universal_live_runtime_ready": False,
        "universal_live_runtime_light": "🟣",
        "network_calls_made": False,
        "execution_granted": False,
        "approval_granted": False,
        "human_authority_final": True,
    }


def public_safe_status() -> dict[str, Any]:
    """Founder-safe read-only projection."""
    return status()
