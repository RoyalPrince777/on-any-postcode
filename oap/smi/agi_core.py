"""Bounded AGI coordination capability inside the single SMI brain.

The AGI Core is a routing and cross-domain synthesis capability. It is not a
second brain, it does not claim that OAP has achieved artificial general
intelligence, and it has no independent approval or execution authority.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

_DOMAIN_RULES: tuple[dict[str, object], ...] = (
    {
        "id": "earth",
        "name": "Earth Intelligence",
        "kind": "intelligence_world",
        "keywords": (
            "earth", "global", "continent", "country", "region", "county",
            "borough", "postcode", "local", "place", "geography", "nature",
            "climate", "weather", "ecosystem", "agriculture",
        ),
    },
    {
        "id": "language",
        "name": "Language Intelligence",
        "kind": "cross_system_capability",
        "keywords": (
            "language", "translate", "translation", "speak", "pronunciation",
            "dialect", "twi", "akan", "english", "spanish", "french",
            "portuguese", "creole", "sign language", "esol",
        ),
    },
    {
        "id": "life",
        "name": "Life Intelligence",
        "kind": "cross_system_capability",
        "keywords": (
            "life", "education", "learn", "learning", "adult", "youth", "trade",
            "trades", "apprentice", "career", "job", "work", "money", "budget",
            "business", "law", "home", "parenting", "skill", "school", "profession",
        ),
    },
    {
        "id": "movement",
        "name": "Movement Intelligence",
        "kind": "cross_system_capability",
        "keywords": (
            "move", "movement", "route", "routing", "travel", "traffic", "drive",
            "walking", "walk", "cycle", "cycling", "train", "bus", "delivery",
            "logistics", "navigation", "road", "journey", "map", "parking", "transport",
        ),
    },
    {
        "id": "technology",
        "name": "Technology Intelligence",
        "kind": "cross_system_capability",
        "keywords": (
            "technology", "connectivity", "6g", "5g", "esim", "edge ai", "edge compute",
            "mesh network", "satellite connectivity", "network", "telecom",
            "device-to-device", "device to device", "radio access", "humanitarian",
            "emergency communications", "emergency telecom", "emergency roaming", "sos",
            "family reunification", "public warning", "disaster connectivity",
            "spatial presence", "face up spatial", "hologram", "holographic",
            "volumetric", "volumetric telepresence", "telepresence", "point cloud",
            "light field", "light-field", "xr", "smart glasses", "headset",
            "semantic compression", "spatial capture", "digital twin",
            "photonic wireless", "photonic radio", "7-21 ghz", "7–21 ghz",
            "d-band", "d band", "sub-thz", "sub thz", "terahertz",
        ),
    },
    {
        "id": "international_humanitarian",
        "name": "International Humanitarian Intelligence",
        "kind": "cross_system_capability",
        "keywords": (
            "international humanitarian", "humanitarian law", "ihl", "geneva convention",
            "geneva conventions", "civilian protection", "human rights law", "refugee law",
            "asylum", "displacement", "stateless", "disaster law", "idrl", "law of the land",
            "customary international law", "humanitarian principles", "medical protection",
            "humanitarian exemption", "humanitarian sanctions", "cultural property",
            "world crisis", "global crisis", "world emergency", "emergency world crisis",
            "crisis monitoring", "humanitarian emergency", "natural disaster", "earthquake",
            "cyclone", "flood", "wildfire", "volcano", "drought", "outbreak", "epidemic",
            "pandemic", "refugee emergency", "famine", "food crisis", "water crisis",
            "critical infrastructure crisis",
        ),
    },
    {
        "id": "civic",
        "name": "Civic Intelligence",
        "kind": "intelligence_world",
        "keywords": (
            "community", "community power", "president", "vice president", "leadership",
            "public service", "local service", "vote", "civic",
        ),
    },
    {
        "id": "civilisation",
        "name": "Civilisation Intelligence",
        "kind": "intelligence_world",
        "keywords": (
            "civilisation", "civilization", "history", "institution", "culture", "society",
            "heritage", "human progress",
        ),
    },
    {
        "id": "matrix",
        "name": "Matrix Intelligence",
        "kind": "intelligence_world",
        "keywords": (
            "code", "technical", "architecture", "system", "database", "api", "deploy",
            "software", "strategy", "simulation", "problem solving", "spatial", "geometry",
            "scene graph", "world state",
        ),
    },
    {
        "id": "akan",
        "name": "Akan Intelligence",
        "kind": "intelligence_world",
        "keywords": ("akan", "akyem", "adinkra", "ghana", "begoro", "koradaso"),
    },
    {
        "id": "animal",
        "name": "Animal Intelligence",
        "kind": "intelligence_world",
        "keywords": ("animal", "wildlife", "species", "fauna"),
    },
    {
        "id": "jungle_book",
        "name": "Jungle Book Intelligence",
        "kind": "intelligence_world",
        "keywords": (
            "akela", "mowgli", "baloo", "bagheera", "hathi", "bandar log",
            "king louie", "shere khan", "wolf pack",
        ),
    },
)

_TASK_DEFAULTS: dict[str, tuple[str, ...]] = {
    "TECHNICAL": ("matrix",),
    "COMMUNITY": ("civic", "life", "earth"),
    "AKAN": ("akan", "earth", "language", "civilisation"),
    "CULTURE": ("civilisation", "language", "life"),
    "MONITORING": ("matrix", "earth", "movement"),
    "STRATEGY": ("matrix", "civic"),
    "GENERAL": ("matrix",),
}

_DOMAIN_DEPENDENCIES: dict[str, tuple[str, ...]] = {
    "movement": ("earth",),
    "technology": ("matrix",),
    "international_humanitarian": ("earth", "life"),
}


def _dedupe(values: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return tuple(ordered)


class AGICore:
    """Select specialist intelligence for SMI without gaining authority."""

    component = "AGI Core"

    def route(self, content: object, task_type: object = "GENERAL") -> dict[str, Any]:
        text = str(content or "").casefold()
        task = str(task_type or "GENERAL").strip().upper() or "GENERAL"
        selected: list[str] = list(_TASK_DEFAULTS.get(task, _TASK_DEFAULTS["GENERAL"]))
        matches: dict[str, tuple[str, ...]] = {}
        for domain in _DOMAIN_RULES:
            domain_id = str(domain["id"])
            keywords = tuple(str(item) for item in domain["keywords"])
            hit = tuple(keyword for keyword in keywords if keyword in text)
            if hit:
                selected.append(domain_id)
                matches[domain_id] = hit[:5]
        selected_ids = _dedupe(selected)
        for domain_id in selected_ids:
            selected.extend(_DOMAIN_DEPENDENCIES.get(domain_id, ()))
        domain_ids = _dedupe(selected)
        by_id = {str(item["id"]): item for item in _DOMAIN_RULES}
        return {
            "component": self.component,
            "task_type": task,
            "domain_ids": domain_ids,
            "domains": tuple(str(by_id[item]["name"]) for item in domain_ids),
            "matches": matches,
            "cross_domain": len(domain_ids) > 1,
            "synthesis_required": len(domain_ids) > 1,
            "decision_authority": False,
            "execution_authority": False,
            "human_authority_final": True,
        }

    def status(self) -> dict[str, object]:
        return {
            "component": self.component,
            "ready": True,
            "kind": "capability_layer",
            "brain_count": 0,
            "domain_count": len(_DOMAIN_RULES),
            "domains": tuple(str(item["name"]) for item in _DOMAIN_RULES),
            "general_intelligence_certified": False,
            "agi_achieved": False,
            "mode": "bounded_cross_domain_coordination",
            "independent_execute": False,
            "independent_approval": False,
            "human_authority_final": True,
            "truth_boundary": (
                "AGI Core names OAP's general-purpose coordination target and routing layer; "
                "it does not claim that artificial general intelligence has been achieved."
            ),
        }
