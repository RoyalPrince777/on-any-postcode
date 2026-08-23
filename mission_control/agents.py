"""Canonical OAP-owned agent families and read-only public projections.

External AI services are providers, never OAP agents or authority holders.
Every registered agent belongs to one family and carries only the agent-level
Soul-Mind-Body anatomy.  This module contains no execution or persistence path.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any

INTELLIGENCE_FAMILIES: tuple[dict[str, Any], ...] = (
    {
        "id": "civic",
        "name": "Civic Intelligence",
        "world_id": "civic",
        "purpose": "Community coordination, public service and postcode awareness.",
        "roster_status": "Roster requires human approval",
    },
    {
        "id": "jungle_book",
        "name": "Jungle Book Intelligence",
        "world_id": "jungle_book",
        "purpose": "Situational wisdom, coordination, mentoring and protection.",
        "roster_status": "Confirmed roster preserved",
    },
    {
        "id": "animal",
        "name": "Animal Intelligence",
        "world_id": "animal",
        "purpose": "Specialist signals expressed through approved animal archetypes.",
        "roster_status": "Confirmed core roster preserved",
    },
    {
        "id": "matrix",
        "name": "Matrix Intelligence",
        "world_id": "matrix",
        "purpose": "Systems reasoning, simulation, strategy and problem solving.",
        "roster_status": "Confirmed roster preserved",
    },
    {
        "id": "civilisation",
        "name": "Civilisation Intelligence",
        "world_id": "civilisation",
        "purpose": "Long-range culture, institutions, learning and human progress.",
        "roster_status": "Roster requires human approval",
    },
    {
        "id": "akan_core",
        "name": "Akan Core Intelligence",
        "world_id": "akan",
        "purpose": "Akan-Akyem identity, values, heritage and constitutional wisdom.",
        "roster_status": "Roster requires human approval",
    },
    {
        "id": "akan_animal",
        "name": "Akan Animal Intelligence",
        "world_id": "akan",
        "purpose": "Akan animal wisdom kept inside its own cultural family.",
        "roster_status": "Confirmed roster is incomplete",
    },
)

LOCKED_FAMILY_IDS = tuple(family["id"] for family in INTELLIGENCE_FAMILIES)
INTELLIGENCE_WORLDS: tuple[dict[str, str], ...] = (
    {"id": "civic", "name": "Civic Intelligence"},
    {"id": "jungle_book", "name": "Jungle Book Intelligence"},
    {"id": "animal", "name": "Animal Intelligence"},
    {"id": "akan", "name": "Akan Intelligence"},
    {"id": "matrix", "name": "Matrix Intelligence"},
    {"id": "civilisation", "name": "Civilisation Intelligence"},
)
LOCKED_WORLD_IDS = tuple(world["id"] for world in INTELLIGENCE_WORLDS)
INTELLIGENCE_WORLD_NAMES = tuple(world["name"] for world in INTELLIGENCE_WORLDS)
INTELLIGENCE_FAMILY_NAMES = tuple(family["name"] for family in INTELLIGENCE_FAMILIES)

# The approved registry target is preserved independently of implementation
# progress. Missing passports are never fabricated or treated as approved.
LOCKED_AGENT_COUNT = 78

INTELLIGENCE_PROVIDERS: tuple[dict[str, str], ...] = (
    {"id": "gpt", "name": "GPT", "type": "Cloud provider"},
    {"id": "claude", "name": "Claude", "type": "Cloud provider"},
    {"id": "gemini", "name": "Gemini", "type": "Cloud provider"},
    {"id": "kimi", "name": "Kimi", "type": "Cloud provider"},
    {"id": "grok", "name": "Grok", "type": "Cloud provider"},
    {"id": "edge_copilot", "name": "Edge/Copilot", "type": "Cloud provider"},
    {"id": "ollama", "name": "Ollama Local", "type": "Local provider"},
)

AGENT_ANATOMY = (
    {
        "name": "Soul",
        "purpose": "Purpose, values, ethics and constitutional alignment.",
    },
    {
        "name": "Mind",
        "purpose": "Reasoning, contextual understanding and permitted memory access.",
    },
    {
        "name": "Body",
        "purpose": "Approved tools, interfaces and bounded action capability.",
    },
)

ADVISORY_AGENT_NAMES = ("Neo", "Akela", "Bagheera", "Gyata", "Shere Khan")

_DEFAULT_RESTRICTIONS = (
    "Cannot override Human Authority",
    "Cannot approve its own recommendation",
    "Cannot change its own permissions",
    "Cannot execute real-world actions from this interface",
)

_CREATED_BY = {
    "organisation": "ON ANY POSTCODE",
    "short_name": "OAP",
    "system": "OAP Intelligence",
    "authority": "Human Authority",
}


def _preserved_agent(
    agent_id: str,
    name: str,
    family_id: str,
    *,
    aliases: tuple[str, ...] = (),
    entity_type: str = "AI Agent",
) -> dict[str, Any]:
    return {
        "agent_id": agent_id,
        "created_by": dict(_CREATED_BY),
        "created_at": None,
        "version": "1.0",
        "name": name,
        "aliases": aliases,
        "family_id": family_id,
        "organ": None,
        "powered_by": "ON ANY POSTCODE",
        "entity_type": entity_type,
        "identity": {
            "type": entity_type,
            "classification": "Intelligence Cell",
            "purpose": "Support human-led decisions",
        },
        "role": None,
        "role_status": "Requires human approval",
        "brain_region": None,
        "brain_region_status": "Requires human approval",
        "registry_status": "PRESERVED",
        "runtime_status": "Not connected",
        "soul": {
            "purpose": "Preserve this approved OAP agent identity.",
            "values": ("Human benefit", "Protection", "Truth"),
            "alignment": "OAP Constitution",
        },
        "mind": {
            "capabilities": ("Analyse", "Advise", "Recommend"),
            "memory_access": "Not connected",
            "provider_assignment": "Not assigned",
        },
        "body": {
            "tools": (),
            "actions": (),
            "execution": "Disabled",
        },
        "permissions": ("READ", "ANALYSE", "RECOMMEND"),
        "restrictions": _DEFAULT_RESTRICTIONS,
        "guardian": "OAP Guardian",
        "supervisor": "Living Kernel",
        "memory_system": "HRM Core",
        "audit_required": True,
        "authority": {
            "level": None,
            "supervisor": "Living Kernel",
            "guardian": "OAP Guardian",
        },
        "memory": {"system": "HRM Core", "audit": True},
        "status": "PRESERVED",
        "provider_ids": (),
    }


def _proposed_agent(agent_id: str, name: str, family_id: str) -> dict[str, Any]:
    """Create a non-operational draft passport pending named human approval."""

    passport = _preserved_agent(agent_id, name, family_id)
    passport.update(
        {
            "registry_status": "PROPOSED",
            "runtime_status": "Disabled — requires human approval",
            "status": "PROPOSED",
        }
    )
    passport["soul"] = {
        **passport["soul"],
        "purpose": "Proposed OAP identity; purpose requires human approval.",
    }
    return passport


NEO = {
    "agent_id": "NEO-001",
    "created_by": dict(_CREATED_BY),
    "created_at": None,
    "version": "1.0",
    "name": "Neo",
    "aliases": (),
    "family_id": "matrix",
    "organ": "Brain",
    "powered_by": "ON ANY POSTCODE",
    "entity_type": "AI Agent",
    "identity": {
        "type": "AI Agent",
        "classification": "Intelligence Cell",
        "purpose": "Support human-led decisions",
    },
    "role": "Kernel Sentinel",
    "role_status": "Approved",
    "brain_region": "SMI Brain",
    "brain_region_status": "Approved connection; not another brain component",
    "registry_status": "ACTIVE",
    "runtime_status": "Not connected",
    "soul": {
        "purpose": "Solve complex problems",
        "values": ("Truth", "Protection", "Human benefit"),
        "alignment": "OAP Constitution",
    },
    "mind": {
        "capabilities": ("Reasoning", "Learning", "Strategy"),
        "reasoning": True,
        "learning": True,
        "strategy": True,
        "memory_access": "HRM Approved",
        "provider_assignment": "Not assigned",
    },
    "body": {
        "tools": ("analysis", "communication"),
        "actions": ("solve", "assist"),
        "execution": "Human approval required",
    },
    "permissions": ("READ", "ANALYSE", "RECOMMEND"),
    "restrictions": _DEFAULT_RESTRICTIONS,
    "guardian": "OAP Guardian",
    "supervisor": "Living Kernel",
    "memory_system": "HRM Core",
    "audit_required": True,
    "authority": {
        "level": 4,
        "supervisor": "Living Kernel",
        "guardian": "OAP Guardian",
    },
    "memory": {"system": "HRM Core", "audit": True},
    "status": "ACTIVE",
    "provider_ids": (),
}


PRESERVED_AGENT_REGISTRY: tuple[dict[str, Any], ...] = (
    NEO,
    _preserved_agent("MATRIX-MORPHEUS-001", "Morpheus", "matrix"),
    _preserved_agent("MATRIX-TRINITY-001", "Trinity", "matrix"),
    _preserved_agent("MATRIX-ORACLE-001", "Oracle", "matrix"),
    _preserved_agent("MATRIX-ARCHITECT-001", "Architect", "matrix"),
    _preserved_agent("MATRIX-KEYMAKER-001", "Keymaker", "matrix"),
    _preserved_agent("MATRIX-SERAPH-001", "Seraph", "matrix"),
    _preserved_agent("JUNGLE-AKELA-001", "Akela", "jungle_book"),
    _preserved_agent("JUNGLE-MOWGLI-001", "Mowgli", "jungle_book"),
    _preserved_agent(
        "JUNGLE-WOLF-PACK-001",
        "Wolf Pack",
        "jungle_book",
        entity_type="Collective Intelligence",
    ),
    _preserved_agent("JUNGLE-BALOO-001", "Baloo", "jungle_book"),
    _preserved_agent("JUNGLE-BAGHEERA-001", "Bagheera", "jungle_book"),
    _preserved_agent(
        "JUNGLE-HATHI-001",
        "Colonel Hathi",
        "jungle_book",
        aliases=("Hathi",),
    ),
    _preserved_agent("JUNGLE-HATHI-JR-001", "Hathi Jr", "jungle_book"),
    _preserved_agent(
        "JUNGLE-BANDAR-LOG-001",
        "Bandar Log",
        "jungle_book",
        entity_type="Collective Intelligence",
    ),
    _preserved_agent("JUNGLE-KING-LOUIE-001", "King Louie", "jungle_book"),
    _preserved_agent("JUNGLE-SHERE-KHAN-001", "Shere Khan", "jungle_book"),
    _preserved_agent("ANIMAL-BEE-001", "Bee", "animal"),
    _preserved_agent("ANIMAL-OWL-001", "Owl", "animal"),
    _preserved_agent("ANIMAL-ELEPHANT-001", "Elephant", "animal"),
    _preserved_agent("ANIMAL-PANTHER-001", "Panther", "animal"),
    _preserved_agent("ANIMAL-EAGLE-001", "Eagle", "animal"),
    _preserved_agent("ANIMAL-FALCON-001", "Falcon", "animal"),
    _preserved_agent("ANIMAL-GORILLA-001", "Gorilla", "animal"),
    _preserved_agent(
        "AKAN-GYATA-001",
        "Gyata",
        "akan_animal",
        aliases=("Akan Lion",),
    ),
)

# These names complete the 78-passport implementation target as a reviewable
# draft. They carry no role, provider, tool, execution permission or runtime
# activation. Human Authority must approve each identity before PROPOSED can be
# changed to PRESERVED or ACTIVE.
PROPOSED_AGENT_SPECS: tuple[tuple[str, str, str], ...] = (
    ("CIVIC-POSTCODE-BEACON-001", "Postcode Beacon", "civic"),
    ("CIVIC-BOROUGH-BRIDGE-001", "Borough Bridge", "civic"),
    ("CIVIC-COUNTY-COMPASS-001", "County Compass", "civic"),
    ("CIVIC-COUNTRY-LINK-001", "Country Link", "civic"),
    ("CIVIC-CONTINENT-RELAY-001", "Continent Relay", "civic"),
    ("CIVIC-COMMUNITY-LISTENER-001", "Community Listener", "civic"),
    ("CIVIC-SIGNAL-KEEPER-001", "Signal Keeper", "civic"),
    ("CIVIC-LOCAL-GUIDE-001", "Local Guide", "civic"),
    ("CIVIC-NEIGHBOURHOOD-VOICE-001", "Neighbourhood Voice", "civic"),
    ("CIVIC-PUBLIC-SERVICE-001", "Public Service", "civic"),
    ("CIVIC-BUSINESS-CONNECTOR-001", "Business Connector", "civic"),
    ("CIVIC-CREATOR-LINK-001", "Creator Link", "civic"),
    ("CIVIC-YOUTH-VOICE-001", "Youth Voice", "civic"),
    ("CIVIC-ELDER-VOICE-001", "Elder Voice", "civic"),
    ("CIVIC-FAMILY-LINK-001", "Family Link", "civic"),
    ("CIVIC-SAFETY-LIAISON-001", "Safety Liaison", "civic"),
    ("CIVIC-EVENT-COORDINATOR-001", "Event Coordinator", "civic"),
    ("CIVIC-TRANSPORT-SCOUT-001", "Transport Scout", "civic"),
    ("CIVIC-OPPORTUNITY-FINDER-001", "Opportunity Finder", "civic"),
    ("ANIMAL-BEAR-001", "Bear", "animal"),
    ("ANIMAL-WOLF-001", "Wolf", "animal"),
    ("ANIMAL-FOX-001", "Fox", "animal"),
    ("ANIMAL-SHARK-001", "Shark", "animal"),
    ("ANIMAL-WHALE-001", "Whale", "animal"),
    ("ANIMAL-CHEETAH-001", "Cheetah", "animal"),
    ("ANIMAL-SPIDER-001", "Spider", "animal"),
    ("ANIMAL-DOLPHIN-001", "Dolphin", "animal"),
    ("ANIMAL-SNAKE-001", "Snake", "animal"),
    ("ANIMAL-TIGER-001", "Tiger", "animal"),
    ("ANIMAL-HORSE-001", "Horse", "animal"),
    ("ANIMAL-STAG-001", "Stag", "animal"),
    ("ANIMAL-OCTOPUS-001", "Octopus", "animal"),
    ("ANIMAL-TURTLE-001", "Turtle", "animal"),
    ("CIVILISATION-HISTORIAN-001", "Civilisation Historian", "civilisation"),
    ("CIVILISATION-EDUCATOR-001", "Civilisation Educator", "civilisation"),
    ("CIVILISATION-INNOVATOR-001", "Civilisation Innovator", "civilisation"),
    ("CIVILISATION-DIPLOMAT-001", "Civilisation Diplomat", "civilisation"),
    ("CIVILISATION-STEWARD-001", "Civilisation Steward", "civilisation"),
    ("CIVILISATION-ARTISAN-001", "Civilisation Artisan", "civilisation"),
    ("CIVILISATION-FUTURIST-001", "Civilisation Futurist", "civilisation"),
    ("AKAN-CORE-NANA-001", "Nana", "akan_core"),
    ("AKAN-ANANSE-001", "Akan Spider", "akan_animal"),
    ("AKAN-ELEPHANT-001", "Akan Elephant", "akan_animal"),
    ("AKAN-EAGLE-001", "Akan Eagle", "akan_animal"),
    ("AKAN-FALCON-001", "Akan Falcon", "akan_animal"),
    ("AKAN-OWL-001", "Akan Owl", "akan_animal"),
    ("AKAN-BEE-001", "Akan Bee", "akan_animal"),
    ("AKAN-PANTHER-001", "Akan Panther", "akan_animal"),
    ("AKAN-CROCODILE-001", "Akan Crocodile", "akan_animal"),
    ("AKAN-TORTOISE-001", "Akan Tortoise", "akan_animal"),
    ("AKAN-ANTELOPE-001", "Akan Antelope", "akan_animal"),
    ("AKAN-BUFFALO-001", "Akan Buffalo", "akan_animal"),
    ("AKAN-HORNBILL-001", "Akan Hornbill", "akan_animal"),
)

PROPOSED_AGENT_REGISTRY = tuple(
    _proposed_agent(agent_id, name, family_id)
    for agent_id, name, family_id in PROPOSED_AGENT_SPECS
)
AGENT_REGISTRY = PRESERVED_AGENT_REGISTRY + PROPOSED_AGENT_REGISTRY


def _normalise(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def _duplicates(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        normalised = _normalise(value)
        if normalised in seen:
            duplicates.add(value)
        else:
            seen.add(normalised)
    return sorted(duplicates)


def validate_agent_registry(
    families: Iterable[Mapping[str, Any]] = INTELLIGENCE_FAMILIES,
    agents: Iterable[Mapping[str, Any]] = AGENT_REGISTRY,
    providers: Iterable[Mapping[str, str]] = INTELLIGENCE_PROVIDERS,
) -> dict[str, Any]:
    """Detect registry conflicts and report canonical roster completeness."""

    family_items = tuple(families)
    agent_items = tuple(agents)
    provider_items = tuple(providers)
    errors: list[str] = []

    duplicate_family_ids = _duplicates(item["id"] for item in family_items)
    duplicate_family_names = _duplicates(item["name"] for item in family_items)
    if len(family_items) != 7:
        errors.append("Exactly seven OAP Intelligence families are required.")
    if tuple(item["id"] for item in family_items) != LOCKED_FAMILY_IDS:
        errors.append("The locked OAP Intelligence family set or order has changed.")
    if duplicate_family_ids or duplicate_family_names:
        errors.append("OAP Intelligence family identifiers and names must be unique.")

    unknown_worlds = sorted(
        {
            item.get("world_id", "")
            for item in family_items
            if item.get("world_id") not in LOCKED_WORLD_IDS
        }
    )
    if unknown_worlds:
        errors.append("Unknown Intelligence worlds: " + ", ".join(unknown_worlds))

    family_ids = {item["id"] for item in family_items}
    unknown_families = sorted(
        {
            item["family_id"]
            for item in agent_items
            if item["family_id"] not in family_ids
        }
    )
    if unknown_families:
        errors.append("Unknown agent families: " + ", ".join(unknown_families))

    duplicate_agent_ids = _duplicates(item["agent_id"] for item in agent_items)
    agent_labels: list[str] = []
    for item in agent_items:
        agent_labels.append(item["name"])
        agent_labels.extend(item.get("aliases", ()))
    duplicate_agent_names = _duplicates(agent_labels)
    if duplicate_agent_ids:
        errors.append("Duplicate agent identifiers: " + ", ".join(duplicate_agent_ids))
    if duplicate_agent_names:
        errors.append("Duplicate agent names or aliases: " + ", ".join(duplicate_agent_names))

    approved_roles = [
        item["role"]
        for item in agent_items
        if item.get("role") and item.get("role_status") == "Approved"
    ]
    duplicate_roles = _duplicates(approved_roles)
    if duplicate_roles:
        errors.append("Duplicate approved agent roles: " + ", ".join(duplicate_roles))

    provider_names = [item["name"] for item in provider_items]
    duplicate_provider_ids = _duplicates(item["id"] for item in provider_items)
    duplicate_provider_names = _duplicates(provider_names)
    if duplicate_provider_ids or duplicate_provider_names:
        errors.append("Provider identifiers and names must be unique.")
    family_names = [item["name"] for item in family_items]
    provider_family_conflicts = sorted(
        {_normalise(name) for name in provider_names}
        & {_normalise(name) for name in family_names}
    )
    if provider_family_conflicts:
        errors.append("Providers cannot be registered as OAP Intelligence families.")

    provider_ids = {item["id"] for item in provider_items}
    unknown_providers = sorted(
        {
            provider_id
            for item in agent_items
            for provider_id in item.get("provider_ids", ())
            if provider_id not in provider_ids
        }
    )
    if unknown_providers:
        errors.append("Unknown provider assignments: " + ", ".join(unknown_providers))

    required_layers = {"soul", "mind", "body"}
    malformed_agents = sorted(
        item["agent_id"]
        for item in agent_items
        if not required_layers.issubset(item)
    )
    if malformed_agents:
        errors.append("Agents missing Soul-Mind-Body: " + ", ".join(malformed_agents))

    unsafe_agents = sorted(
        item["agent_id"]
        for item in agent_items
        if "EXECUTE" in item.get("permissions", ())
        or "Cannot override Human Authority" not in item.get("restrictions", ())
    )
    if unsafe_agents:
        errors.append("Unsafe agent authority detected: " + ", ".join(unsafe_agents))

    canonical_names = family_names + agent_labels
    banned_names = [
        name
        for name in canonical_names
        if _normalise(name) == "kaa" or "council" in name.casefold()
    ]
    if banned_names:
        errors.append("Prohibited or legacy names found: " + ", ".join(banned_names))

    roster_complete = len(agent_items) == LOCKED_AGENT_COUNT
    proposed_passports = sum(
        item.get("registry_status") == "PROPOSED" for item in agent_items
    )
    return {
        "passed": not errors,
        "ready_for_activation": not errors and roster_complete and not proposed_passports,
        "errors": errors,
        "checks": {
            "worlds": len(INTELLIGENCE_WORLDS),
            "families": len(family_items),
            "registered_agents": len(agent_items),
            "locked_agent_count": LOCKED_AGENT_COUNT,
            "missing_passports": max(LOCKED_AGENT_COUNT - len(agent_items), 0),
            "roster_complete": roster_complete,
            "proposed_passports": proposed_passports,
            "human_approved_passports": len(agent_items) - proposed_passports,
            "providers": len(provider_items),
            "duplicate_providers": len(duplicate_provider_ids)
            + len(duplicate_provider_names),
            "duplicate_agent_ids": len(duplicate_agent_ids),
            "duplicate_agent_names": len(duplicate_agent_names),
            "duplicate_approved_roles": len(duplicate_roles),
            "unknown_families": len(unknown_families),
            "unsafe_authority": len(unsafe_agents),
        },
    }


def _family_counts(
    agents: Iterable[Mapping[str, Any]],
    *,
    registry_status: str | None = None,
) -> dict[str, int]:
    counts = {family_id: 0 for family_id in LOCKED_FAMILY_IDS}
    for agent in agents:
        if registry_status and agent.get("registry_status") != registry_status:
            continue
        counts[agent["family_id"]] += 1
    return counts


def get_public_family_status() -> list[dict[str, Any]]:
    """Return honest family-level status for the existing gateway cards."""

    counts = _family_counts(AGENT_REGISTRY)
    proposed = _family_counts(AGENT_REGISTRY, registry_status="PROPOSED")
    return [
        {
            "family_id": family["id"],
            "name": family["name"],
            "status": "Not connected",
            "assignment": (
                f"{counts[family['id']]} passport(s), "
                f"{proposed[family['id']]} proposed; no live assignment"
            ),
        }
        for family in INTELLIGENCE_FAMILIES
    ]


def get_public_agent_directory(
    family_id: str | None = None,
    query: str = "",
) -> dict[str, Any]:
    """Return a filtered, side-effect-free directory for server rendering."""

    validation = validate_agent_registry()
    counts = _family_counts(AGENT_REGISTRY)
    proposed = _family_counts(AGENT_REGISTRY, registry_status="PROPOSED")
    search = query.strip().casefold()[:80]
    selected_agents = [
        agent
        for agent in AGENT_REGISTRY
        if (family_id is None or agent["family_id"] == family_id)
        and (
            not search
            or search in agent["name"].casefold()
            or search in agent["agent_id"].casefold()
            or (agent.get("role") and search in agent["role"].casefold())
        )
    ]

    families = [
        {
            **family,
            "registered_agents": counts[family["id"]],
            "proposed_agents": proposed[family["id"]],
            "human_approved_agents": counts[family["id"]] - proposed[family["id"]],
            "selected": family["id"] == family_id,
        }
        for family in INTELLIGENCE_FAMILIES
    ]
    return {
        "families": families,
        "agents": selected_agents,
        "providers": INTELLIGENCE_PROVIDERS,
        "agent_anatomy": AGENT_ANATOMY,
        "validation": validation,
        "filters": {"family_id": family_id, "query": query.strip()[:80]},
        "human_authority": {
            "status": "Final approval required",
            "message": "No agent action or architecture change is enabled here.",
        },
    }
