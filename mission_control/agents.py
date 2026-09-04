"""Canonical OAP agent alignment facade.

This module preserves the approved 78-agent registry while enforcing the locked
organism boundary:

- OASIS, OAP CORE, NEXUS, Guardian, Living Kernel and HRM are systems/organs,
  never agents.
- SMI is one brain.
- Earth, Language, Life, Movement, Civic, Civilisation and Matrix are the seven
  Intelligence Worlds.
- Specialist families live inside one canonical world/system.
- Matrix agents live in the Matrix System.
- Nirmata is the Creation Architect inside Civilisation Intelligence.

The previous registry implementation remains available internally as
``agents_legacy`` for compatibility. External providers remain providers and
never become OAP agents or authority holders.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from . import agents_legacy as _legacy

ADVISORY_AGENT_NAMES = _legacy.ADVISORY_AGENT_NAMES
AGENT_ANATOMY = _legacy.AGENT_ANATOMY
INTELLIGENCE_PROVIDERS = _legacy.INTELLIGENCE_PROVIDERS
LOCKED_AGENT_COUNT = _legacy.LOCKED_AGENT_COUNT
NEO = _legacy.NEO

INTELLIGENCE_WORLDS: tuple[dict[str, Any], ...] = (
    {
        "id": "earth",
        "name": "Earth Intelligence",
        "system_id": "earth_system",
        "system_name": "Earth System",
        "kind": "intelligence_world",
        "purpose": "Planet, place, nature, climate, land, water, ecosystems and environmental context.",
    },
    {
        "id": "language",
        "name": "Language Intelligence",
        "system_id": "language_system",
        "system_name": "Language System",
        "kind": "intelligence_world",
        "purpose": "Language, meaning, translation, communication and cultural expression.",
    },
    {
        "id": "life",
        "name": "Life Intelligence",
        "system_id": "life_system",
        "system_name": "Life System",
        "kind": "intelligence_world",
        "purpose": "Human, animal, health, wellbeing, family, living systems and protection context.",
    },
    {
        "id": "movement",
        "name": "Movement Intelligence",
        "system_id": "movement_system",
        "system_name": "Movement System",
        "kind": "intelligence_world",
        "purpose": "Movement, routes, mobility, transport, logistics and spatial coordination.",
    },
    {
        "id": "civic",
        "name": "Civic Intelligence",
        "system_id": "civic_system",
        "system_name": "Civic System",
        "kind": "intelligence_world",
        "purpose": "Community, postcode, public-service and local civic context.",
    },
    {
        "id": "civilisation",
        "name": "Civilisation Intelligence",
        "system_id": "civilisation_system",
        "system_name": "Civilisation System",
        "kind": "intelligence_world",
        "purpose": "Culture, institutions, learning, heritage, creation and long-range human progress.",
    },
    {
        "id": "matrix",
        "name": "Matrix Intelligence",
        "system_id": "matrix_system",
        "system_name": "Matrix System",
        "kind": "intelligence_world",
        "purpose": "Systems reasoning, architecture, technical strategy, simulation and problem solving.",
    },
)

LOCKED_WORLD_IDS = tuple(world["id"] for world in INTELLIGENCE_WORLDS)
INTELLIGENCE_WORLD_NAMES = tuple(world["name"] for world in INTELLIGENCE_WORLDS)

_FAMILY_ALIGNMENT: dict[str, dict[str, Any]] = {
    "civic": {
        "world_id": "civic",
        "home_system": "Civic System",
        "classification": "world_family",
    },
    "jungle_book": {
        "world_id": "life",
        "home_system": "Life System",
        "classification": "specialist_context",
    },
    "animal": {
        "world_id": "life",
        "home_system": "Life System",
        "classification": "specialist_context",
    },
    "matrix": {
        "world_id": "matrix",
        "home_system": "Matrix System",
        "classification": "world_family",
    },
    "civilisation": {
        "world_id": "civilisation",
        "home_system": "Civilisation System",
        "classification": "world_family",
    },
    "akan_core": {
        "world_id": "civilisation",
        "home_system": "Civilisation System",
        "classification": "specialist_context",
    },
    "akan_animal": {
        "world_id": "civilisation",
        "home_system": "Civilisation System",
        "classification": "specialist_context",
        "cross_world_ids": ("life",),
    },
}

INTELLIGENCE_FAMILIES: tuple[dict[str, Any], ...] = tuple(
    {**family, **_FAMILY_ALIGNMENT[family["id"]]}
    for family in _legacy.INTELLIGENCE_FAMILIES
)
LOCKED_FAMILY_IDS = tuple(family["id"] for family in INTELLIGENCE_FAMILIES)
INTELLIGENCE_FAMILY_NAMES = tuple(family["name"] for family in INTELLIGENCE_FAMILIES)

ORGANISM_NON_AGENT_SYSTEMS: tuple[dict[str, str], ...] = (
    {"id": "oasis", "name": "OASIS", "kind": "environment"},
    {"id": "oap_core", "name": "OAP CORE", "kind": "connective_context"},
    {"id": "nexus", "name": "NEXUS", "kind": "nervous_system"},
    {"id": "thalamus", "name": "Thalamus", "kind": "brain_region"},
    {"id": "smi", "name": "SMI", "kind": "brain"},
    {"id": "aegis", "name": "Aegis", "kind": "defensive_shield"},
    {"id": "guardian", "name": "Guardian", "kind": "protective_gate"},
    {"id": "war_room", "name": "War Room", "kind": "strategic_chamber"},
    {"id": "living_kernel", "name": "Living Kernel", "kind": "heart"},
    {"id": "hrm", "name": "HRM Core", "kind": "memory"},
    {"id": "body_systems", "name": "Body Systems", "kind": "execution_body"},
)


def _canonical_nirmata() -> dict[str, Any]:
    source = next(agent for agent in _legacy.AGENT_REGISTRY if agent["name"] == "Nirmata")
    agent = dict(source)
    agent.update(
        {
            "agent_id": "NIRMATA-001",
            "name": "Nirmata",
            "aliases": ("Civilisation Artisan",),
            "family_id": "civilisation",
            "organ": "Brain",
            "role": "Creation Architect",
            "role_status": "Approved",
            "brain_region": "Civilisation Intelligence — Creation & Systems Architecture",
            "brain_region_status": "Approved specialist connection; not another brain or Intelligence World",
            "registry_status": "ACTIVE",
            "runtime_status": "Bounded autonomous advisory — execution disabled",
            "permissions": ("READ", "ANALYSE", "DESIGN", "RECOMMEND", "DRAFT_BLUEPRINT"),
            "restrictions": (
                "Cannot override Human Authority",
                "Cannot execute or deploy without approval",
                "Cannot modify its own permissions or constitution",
                "Cannot create unregistered agents",
                "Cannot replace the GPT Chief Architect",
                "Every design and recommendation must be recorded in HRM",
            ),
            "chief_architect_relationship": (
                "GPT Chief Architect shapes architecture; Nirmata converts approved visions "
                "into buildable blueprints."
            ),
            "operational_pipeline": (
                "Receive vision",
                "Inspect existing organism",
                "Detect duplication",
                "Design upgrade",
                "Guardian review",
                "Human Authority approval",
                "Builder execution",
                "HRM record",
            ),
        }
    )
    agent["soul"] = {
        "purpose": "Transform approved human ideas into complete system blueprints.",
        "values": (
            "Human benefit",
            "Cultural respect",
            "Truth",
            "Responsible creation",
        ),
        "alignment": "OAP Constitution",
    }
    agent["mind"] = {
        "capabilities": (
            "Architecture",
            "Invention",
            "System modelling",
            "Dependency planning",
            "Gap detection",
            "Duplicate detection",
            "Builder handoff",
        ),
        "memory_access": "HRM Core — fully audited",
        "provider_assignment": "Not assigned",
    }
    agent["body"] = {
        "tools": ("read_only_analysis", "blueprint_drafting", "specification_drafting"),
        "actions": (
            "analyse",
            "design",
            "recommend",
            "draft_blueprint",
            "prepare_implementation_plan",
        ),
        "execution": "Disabled",
    }
    agent["memory"] = {"system": "HRM Core", "audit": True, "record_every_design": True}
    agent["memory_system"] = "HRM Core"
    agent["audit_required"] = True
    return agent


NIRMATA = _canonical_nirmata()
AGENT_REGISTRY = tuple(
    NIRMATA if agent["name"] == "Nirmata" else agent
    for agent in _legacy.AGENT_REGISTRY
)

AGENT_SPECS = tuple(
    {
        **item,
        **(
            {
                "agent_id": "NIRMATA-001",
                "role": "Creation Architect",
                "purpose": "Transform approved human ideas into complete system blueprints.",
                "capabilities": NIRMATA["mind"]["capabilities"],
            }
            if item["name"] == "Nirmata"
            else {}
        ),
    }
    for item in _legacy.AGENT_SPECS
)


def validate_agent_registry(
    families: Iterable[Mapping[str, Any]] = INTELLIGENCE_FAMILIES,
    agents: Iterable[Mapping[str, Any]] = AGENT_REGISTRY,
    providers: Iterable[Mapping[str, str]] = INTELLIGENCE_PROVIDERS,
) -> dict[str, Any]:
    """Validate the preserved roster plus canonical world/system alignment."""

    family_items = tuple(families)
    agent_items = tuple(agents)
    provider_items = tuple(providers)
    base = _legacy.validate_agent_registry(
        families=_legacy.INTELLIGENCE_FAMILIES,
        agents=agent_items,
        providers=provider_items,
    )
    errors = list(base["errors"])

    world_ids = tuple(world["id"] for world in INTELLIGENCE_WORLDS)
    expected_world_ids = (
        "earth",
        "language",
        "life",
        "movement",
        "civic",
        "civilisation",
        "matrix",
    )
    if world_ids != expected_world_ids:
        errors.append("The locked seven Intelligence Worlds are misaligned.")
    if len(set(world_ids)) != 7:
        errors.append("Intelligence World identifiers must be unique.")

    family_ids = tuple(family["id"] for family in family_items)
    if family_ids != LOCKED_FAMILY_IDS:
        errors.append("The locked Intelligence family set or order has changed.")
    unknown_worlds = sorted(
        {
            str(family.get("world_id", ""))
            for family in family_items
            if family.get("world_id") not in LOCKED_WORLD_IDS
        }
    )
    if unknown_worlds:
        errors.append("Unknown canonical Intelligence Worlds: " + ", ".join(unknown_worlds))

    system_names = {item["name"].casefold() for item in ORGANISM_NON_AGENT_SYSTEMS}
    agent_names = {str(item["name"]).casefold() for item in agent_items}
    leaked_systems = sorted(system_names & agent_names)
    if leaked_systems:
        errors.append("Organism systems cannot be counted as agents: " + ", ".join(leaked_systems))

    matrix_family = next(family for family in family_items if family["id"] == "matrix")
    if matrix_family["world_id"] != "matrix" or matrix_family["home_system"] != "Matrix System":
        errors.append("Matrix Intelligence agents must live in the Matrix System.")

    nirmata = next((item for item in agent_items if item["name"] == "Nirmata"), None)
    if not nirmata:
        errors.append("Nirmata is missing from Civilisation Intelligence.")
    else:
        if nirmata["agent_id"] != "NIRMATA-001":
            errors.append("Nirmata must use canonical agent ID NIRMATA-001.")
        if nirmata["family_id"] != "civilisation" or nirmata["role"] != "Creation Architect":
            errors.append("Nirmata must be the Creation Architect inside Civilisation Intelligence.")
        if "EXECUTE" in nirmata["permissions"] or nirmata["body"]["execution"] != "Disabled":
            errors.append("Nirmata cannot hold execution authority.")

    passed = not errors
    result = dict(base)
    result["errors"] = errors
    result["passed"] = passed
    result["registry_complete"] = passed and len(agent_items) == LOCKED_AGENT_COUNT
    result["ready_for_activation"] = (
        result["registry_complete"] and bool(base["human_activation_approved"])
    )
    result["checks"] = {
        **base["checks"],
        "worlds": len(INTELLIGENCE_WORLDS),
        "canonical_world_alignment": passed and not unknown_worlds,
        "non_agent_systems": len(ORGANISM_NON_AGENT_SYSTEMS),
        "matrix_home_system_aligned": matrix_family["home_system"] == "Matrix System",
        "nirmata_creation_architect_aligned": bool(
            nirmata and nirmata["agent_id"] == "NIRMATA-001"
        ),
    }
    return result


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
    """Return family status with canonical world/system placement."""

    counts = _family_counts(AGENT_REGISTRY)
    proposed = _family_counts(AGENT_REGISTRY, registry_status="PROPOSED")
    return [
        {
            **family,
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
    """Return the side-effect-free aligned agent directory."""

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
        "worlds": INTELLIGENCE_WORLDS,
        "families": families,
        "agents": selected_agents,
        "providers": INTELLIGENCE_PROVIDERS,
        "agent_anatomy": AGENT_ANATOMY,
        "non_agent_systems": ORGANISM_NON_AGENT_SYSTEMS,
        "validation": validation,
        "filters": {"family_id": family_id, "query": query.strip()[:80]},
        "human_authority": {
            "status": "Final approval required",
            "message": "No agent action or architecture change is enabled here.",
        },
    }
