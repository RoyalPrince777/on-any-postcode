"""Bounded cross-world coordination inside the single SMI brain.

The AGI Core is a routing and synthesis capability. It is not a second brain,
it does not claim that OAP has achieved artificial general intelligence, and it
has no independent approval or execution authority.

Canonical architecture:
- exactly seven Intelligence Worlds;
- specialist families/capabilities are routed inside those Worlds;
- legacy ``domain_ids`` remain for compatibility, but ``world_ids`` is the
  authoritative top-level routing projection.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

_CANONICAL_WORLD_IDS: tuple[str, ...] = (
    "earth",
    "language",
    "life",
    "movement",
    "civic",
    "civilisation",
    "matrix",
)

_WORLD_RULES: tuple[dict[str, object], ...] = (
    {
        "id": "earth",
        "name": "Earth Intelligence",
        "kind": "intelligence_world",
        "keywords": (
            "earth",
            "global",
            "continent",
            "country",
            "region",
            "county",
            "borough",
            "postcode",
            "local",
            "place",
            "geography",
            "nature",
            "climate",
            "weather",
            "ecosystem",
            "agriculture",
        ),
    },
    {
        "id": "language",
        "name": "Language Intelligence",
        "kind": "intelligence_world",
        "keywords": (
            "language",
            "translate",
            "translation",
            "speak",
            "pronunciation",
            "dialect",
            "twi",
            "akan",
            "english",
            "spanish",
            "french",
            "portuguese",
            "creole",
            "sign language",
            "esol",
        ),
    },
    {
        "id": "life",
        "name": "Life Intelligence",
        "kind": "intelligence_world",
        "keywords": (
            "life",
            "education",
            "learn",
            "learning",
            "adult",
            "youth",
            "trade",
            "trades",
            "apprentice",
            "career",
            "job",
            "work",
            "money",
            "budget",
            "business",
            "law",
            "home",
            "parenting",
            "skill",
            "school",
            "profession",
            "animal",
            "wildlife",
            "species",
            "fauna",
        ),
    },
    {
        "id": "movement",
        "name": "Movement Intelligence",
        "kind": "intelligence_world",
        "keywords": (
            "move",
            "movement",
            "route",
            "routing",
            "travel",
            "traffic",
            "drive",
            "walking",
            "walk",
            "cycle",
            "cycling",
            "train",
            "bus",
            "delivery",
            "logistics",
            "navigation",
            "road",
            "journey",
            "map",
            "parking",
            "transport",
        ),
    },
    {
        "id": "civic",
        "name": "Civic Intelligence",
        "kind": "intelligence_world",
        "keywords": (
            "community",
            "community power",
            "president",
            "vice president",
            "leadership",
            "public service",
            "local service",
            "vote",
            "civic",
            "postcode service",
        ),
    },
    {
        "id": "civilisation",
        "name": "Civilisation Intelligence",
        "kind": "intelligence_world",
        "keywords": (
            "civilisation",
            "civilization",
            "history",
            "institution",
            "culture",
            "society",
            "heritage",
            "human progress",
            "akan",
            "akyem",
            "adinkra",
            "ghana",
            "begoro",
            "koradaso",
        ),
    },
    {
        "id": "matrix",
        "name": "Matrix Intelligence",
        "kind": "intelligence_world",
        "keywords": (
            "code",
            "technical",
            "architecture",
            "system",
            "database",
            "api",
            "deploy",
            "software",
            "strategy",
            "simulation",
            "problem solving",
            "spatial",
            "geometry",
            "scene graph",
            "world state",
        ),
    },
)

# Specialist intelligence never expands the seven-World count. ``world_ids``
# below is the authoritative placement for each specialist context.
_SPECIALIST_RULES: tuple[dict[str, object], ...] = (
    {
        "id": "technology",
        "name": "Technology Intelligence",
        "kind": "cross_system_capability",
        "world_ids": ("matrix",),
        "keywords": (
            "technology",
            "connectivity",
            "6g",
            "5g",
            "esim",
            "edge ai",
            "edge compute",
            "mesh network",
            "satellite connectivity",
            "network",
            "telecom",
            "device-to-device",
            "device to device",
            "radio access",
            "humanitarian",
            "emergency communications",
            "emergency telecom",
            "emergency roaming",
            "sos",
            "family reunification",
            "public warning",
            "disaster connectivity",
            "spatial presence",
            "face up spatial",
            "hologram",
            "holographic",
            "volumetric",
            "volumetric telepresence",
            "telepresence",
            "point cloud",
            "light field",
            "light-field",
            "xr",
            "smart glasses",
            "headset",
            "semantic compression",
            "spatial capture",
            "digital twin",
            "photonic wireless",
            "photonic radio",
            "7-21 ghz",
            "7–21 ghz",
            "d-band",
            "d band",
            "sub-thz",
            "sub thz",
            "terahertz",
        ),
    },
    {
        "id": "international_humanitarian",
        "name": "International Humanitarian Intelligence",
        "kind": "cross_system_capability",
        "world_ids": ("earth", "life", "civic"),
        "keywords": (
            "international humanitarian",
            "humanitarian law",
            "ihl",
            "geneva convention",
            "geneva conventions",
            "civilian protection",
            "human rights law",
            "refugee law",
            "asylum",
            "displacement",
            "stateless",
            "disaster law",
            "idrl",
            "law of the land",
            "customary international law",
            "humanitarian principles",
            "medical protection",
            "humanitarian exemption",
            "humanitarian sanctions",
            "cultural property",
            "world crisis",
            "global crisis",
            "world emergency",
            "emergency world crisis",
            "crisis monitoring",
            "humanitarian emergency",
            "natural disaster",
            "earthquake",
            "cyclone",
            "flood",
            "wildfire",
            "volcano",
            "drought",
            "outbreak",
            "epidemic",
            "pandemic",
            "refugee emergency",
            "famine",
            "food crisis",
            "water crisis",
            "critical infrastructure crisis",
        ),
    },
    {
        "id": "multimodal",
        "name": "Multimodal Intelligence",
        "kind": "cross_system_capability",
        "world_ids": ("matrix", "language"),
        "keywords": (
            "image",
            "picture",
            "photo",
            "document",
            "pdf",
            "audio",
            "voice",
            "video",
            "media",
            "multimodal",
        ),
    },
    {
        "id": "akan",
        "name": "Akan Intelligence",
        "kind": "specialist_family_context",
        "world_ids": ("civilisation", "language", "earth"),
        "keywords": ("akan", "akyem", "adinkra", "ghana", "begoro", "koradaso", "twi"),
    },
    {
        "id": "animal",
        "name": "Animal Intelligence",
        "kind": "specialist_family_context",
        "world_ids": ("life",),
        "keywords": ("animal", "wildlife", "species", "fauna"),
    },
    {
        "id": "jungle_book",
        "name": "Jungle Book Intelligence",
        "kind": "specialist_family_context",
        "world_ids": ("life",),
        "keywords": (
            "akela",
            "mowgli",
            "baloo",
            "bagheera",
            "hathi",
            "bandar log",
            "king louie",
            "shere khan",
            "wolf pack",
        ),
    },
)

_TASK_DEFAULTS: dict[str, tuple[str, ...]] = {
    "TECHNICAL": ("matrix",),
    "COMMUNITY": ("civic", "life", "earth"),
    "AKAN": ("civilisation", "language", "earth"),
    "CULTURE": ("civilisation", "language", "life"),
    "MONITORING": ("matrix", "earth", "movement"),
    "STRATEGY": ("matrix", "civic"),
    "GENERAL": ("matrix",),
}

_WORLD_DEPENDENCIES: dict[str, tuple[str, ...]] = {
    "movement": ("earth",),
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

        selected_worlds: list[str] = list(
            _TASK_DEFAULTS.get(task, _TASK_DEFAULTS["GENERAL"])
        )
        legacy_domains: list[str] = list(selected_worlds)
        selected_specialists: list[str] = []
        matches: dict[str, tuple[str, ...]] = {}

        for world in _WORLD_RULES:
            world_id = str(world["id"])
            keywords = tuple(str(item) for item in world["keywords"])
            hit = tuple(keyword for keyword in keywords if keyword in text)
            if hit:
                selected_worlds.append(world_id)
                legacy_domains.append(world_id)
                matches[world_id] = hit[:5]

        for specialist in _SPECIALIST_RULES:
            specialist_id = str(specialist["id"])
            keywords = tuple(str(item) for item in specialist["keywords"])
            hit = tuple(keyword for keyword in keywords if keyword in text)
            if not hit:
                continue
            selected_specialists.append(specialist_id)
            legacy_domains.append(specialist_id)
            matches[specialist_id] = hit[:5]
            for world_id in tuple(str(item) for item in specialist["world_ids"]):
                selected_worlds.append(world_id)
                legacy_domains.append(world_id)

        canonical_worlds = list(_dedupe(selected_worlds))
        for world_id in tuple(canonical_worlds):
            canonical_worlds.extend(_WORLD_DEPENDENCIES.get(world_id, ()))
        world_ids = _dedupe(canonical_worlds)

        # Keep legacy domain IDs until every caller has moved to ``world_ids``.
        for world_id in world_ids:
            legacy_domains.append(world_id)
        domain_ids = _dedupe(legacy_domains)
        specialist_ids = _dedupe(selected_specialists)

        world_by_id = {str(item["id"]): item for item in _WORLD_RULES}
        specialist_by_id = {str(item["id"]): item for item in _SPECIALIST_RULES}
        name_by_id = {
            **{key: str(value["name"]) for key, value in world_by_id.items()},
            **{key: str(value["name"]) for key, value in specialist_by_id.items()},
        }

        return {
            "component": self.component,
            "task_type": task,
            "world_ids": world_ids,
            "worlds": tuple(str(world_by_id[item]["name"]) for item in world_ids),
            "specialist_ids": specialist_ids,
            "specialists": tuple(
                str(specialist_by_id[item]["name"]) for item in specialist_ids
            ),
            "domain_ids": domain_ids,
            "domains": tuple(name_by_id[item] for item in domain_ids),
            "matches": matches,
            "canonical_world_model": True,
            "world_count_limit": 7,
            "cross_domain": len(world_ids) > 1,
            "synthesis_required": len(world_ids) > 1 or bool(specialist_ids),
            "decision_authority": False,
            "execution_authority": False,
            "human_authority_final": True,
        }

    def status(self) -> dict[str, object]:
        cross_system = tuple(
            str(item["id"])
            for item in _SPECIALIST_RULES
            if item["kind"] == "cross_system_capability"
        )
        family_contexts = tuple(
            str(item["id"])
            for item in _SPECIALIST_RULES
            if item["kind"] == "specialist_family_context"
        )
        combined = (*_WORLD_RULES, *_SPECIALIST_RULES)
        return {
            "component": self.component,
            "ready": True,
            "kind": "capability_layer",
            "brain_count": 0,
            "world_count": len(_WORLD_RULES),
            "world_ids": _CANONICAL_WORLD_IDS,
            "worlds": tuple(str(item["name"]) for item in _WORLD_RULES),
            "specialist_context_count": len(_SPECIALIST_RULES),
            "cross_system_capability_ids": cross_system,
            "family_context_ids": family_contexts,
            "domain_count": len(combined),
            "domains": tuple(str(item["name"]) for item in combined),
            "canonical_world_model": tuple(
                str(item["id"]) for item in _WORLD_RULES
            )
            == _CANONICAL_WORLD_IDS,
            "general_intelligence_certified": False,
            "agi_achieved": False,
            "mode": "bounded_cross_world_coordination",
            "independent_execute": False,
            "independent_approval": False,
            "human_authority_final": True,
            "truth_boundary": (
                "AGI Core names OAP's general-purpose coordination target and routing layer; "
                "it does not claim that artificial general intelligence has been achieved."
            ),
        }
