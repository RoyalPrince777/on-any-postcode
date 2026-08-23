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
        "roster_status": "Complete — Human Authority approved",
    },
    {
        "id": "jungle_book",
        "name": "Jungle Book Intelligence",
        "world_id": "jungle_book",
        "purpose": "Situational wisdom, coordination, mentoring and protection.",
        "roster_status": "Complete — Human Authority approved",
    },
    {
        "id": "animal",
        "name": "Animal Intelligence",
        "world_id": "animal",
        "purpose": "Specialist signals expressed through approved animal archetypes.",
        "roster_status": "Complete — Human Authority approved",
    },
    {
        "id": "matrix",
        "name": "Matrix Intelligence",
        "world_id": "matrix",
        "purpose": "Systems reasoning, simulation, strategy and problem solving.",
        "roster_status": "Complete — Human Authority approved",
    },
    {
        "id": "civilisation",
        "name": "Civilisation Intelligence",
        "world_id": "civilisation",
        "purpose": "Long-range culture, institutions, learning and human progress.",
        "roster_status": "Complete — Human Authority approved",
    },
    {
        "id": "akan_core",
        "name": "Akan Core Intelligence",
        "world_id": "akan",
        "purpose": "Akan-Akyem identity, values, heritage and constitutional wisdom.",
        "roster_status": "Complete — Human Authority approved",
    },
    {
        "id": "akan_animal",
        "name": "Akan Animal Intelligence",
        "world_id": "akan",
        "purpose": "Akan animal wisdom kept inside its own cultural family.",
        "roster_status": "Complete — Human Authority approved",
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


def _registered_agent(
    agent_id: str,
    name: str,
    family_id: str,
    *,
    role: str,
    purpose: str,
    capabilities: tuple[str, ...],
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
        "organ": "Intelligence",
        "powered_by": "ON ANY POSTCODE",
        "entity_type": entity_type,
        "identity": {
            "type": entity_type,
            "classification": "Intelligence Cell",
            "purpose": "Support human-led decisions",
        },
        "role": role,
        "role_status": "Approved",
        "brain_region": "SMI advisory interface",
        "brain_region_status": "Approved advisory connection; no execution path",
        "registry_status": "APPROVED",
        "runtime_status": "Not connected — execution disabled",
        "soul": {
            "purpose": purpose,
            "values": ("Human benefit", "Protection", "Truth"),
            "alignment": "OAP Constitution",
        },
        "mind": {
            "capabilities": capabilities,
            "memory_access": "HRM audited read access",
            "provider_assignment": "Not assigned",
        },
        "body": {
            "tools": ("read_only_analysis", "communication"),
            "actions": ("analyse", "advise", "recommend"),
            "execution": "Disabled",
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
        "status": "APPROVED",
        "provider_ids": (),
    }
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


def _spec(
    agent_id: str,
    name: str,
    family_id: str,
    role: str,
    purpose: str,
    capabilities: tuple[str, ...],
    *,
    aliases: tuple[str, ...] = (),
    entity_type: str = "AI Agent",
) -> dict[str, Any]:
    return {
        "agent_id": agent_id,
        "name": name,
        "family_id": family_id,
        "role": role,
        "purpose": purpose,
        "capabilities": capabilities,
        "aliases": aliases,
        "entity_type": entity_type,
    }


AGENT_SPECS: tuple[dict[str, Any], ...] = (
    # Matrix Intelligence — seven agents including Neo.
    _spec("MATRIX-MORPHEUS-001", "Morpheus", "matrix", "Strategy Guide", "Guide strategic choices while preserving Human Authority.", ("Strategy", "Mentoring", "Scenario analysis")),
    _spec("MATRIX-TRINITY-001", "Trinity", "matrix", "Operations Coordinator", "Coordinate approved operational recommendations across OAP systems.", ("Coordination", "Planning", "Operational analysis")),
    _spec("MATRIX-ORACLE-001", "Oracle", "matrix", "Foresight Analyst", "Model possible futures and communicate uncertainty clearly.", ("Forecasting", "Pattern analysis", "Risk communication")),
    _spec("MATRIX-ARCHITECT-001", "Architect", "matrix", "Systems Designer", "Design coherent system structures without duplicating locked architecture.", ("Systems design", "Dependency analysis", "Architecture review")),
    _spec("MATRIX-KEYMAKER-001", "Keymaker", "matrix", "Access Route Specialist", "Map permitted routes between identities, services and information.", ("Route analysis", "Access mapping", "Interface review")),
    _spec("MATRIX-SERAPH-001", "Seraph", "matrix", "Security Reviewer", "Review security boundaries and recommend protective controls.", ("Security analysis", "Boundary review", "Threat modelling")),

    # Jungle Book Intelligence — all user-preserved identities; Kaa excluded.
    _spec("JUNGLE-AKELA-001", "Akela", "jungle_book", "Pack Coordinator", "Coordinate the pack and keep recommendations aligned with shared purpose.", ("Coordination", "Leadership analysis", "Team review")),
    _spec("JUNGLE-MOWGLI-001", "Mowgli", "jungle_book", "Community Bridge", "Translate between human community needs and Jungle Book Intelligence.", ("Community interpretation", "Communication", "Context analysis")),
    _spec("JUNGLE-WOLF-PACK-001", "Wolf Pack", "jungle_book", "Collective Field Intelligence", "Combine field observations into one traceable recommendation.", ("Distributed observation", "Signal merging", "Field analysis"), entity_type="Collective Intelligence"),
    _spec("JUNGLE-BALOO-001", "Baloo", "jungle_book", "Learning Mentor", "Explain lessons patiently and support safe learning.", ("Teaching", "Reflection", "Knowledge translation")),
    _spec("JUNGLE-BAGHEERA-001", "Bagheera", "jungle_book", "Protective Strategist", "Identify safe routes and protective strategic options.", ("Protective analysis", "Strategy", "Risk awareness")),
    _spec("JUNGLE-HATHI-001", "Colonel Hathi", "jungle_book", "Operations Commander", "Structure disciplined operational recommendations without execution authority.", ("Operational planning", "Coordination", "Readiness review"), aliases=("Hathi",)),
    _spec("JUNGLE-HATHI-JR-001", "Hathi Jr", "jungle_book", "Continuity Scout", "Track continuity details and surface missing operational context.", ("Continuity analysis", "Observation", "Context gathering")),
    _spec("JUNGLE-BANDAR-LOG-001", "Bandar Log", "jungle_book", "Collective Signal Observer", "Observe noisy collective signals and separate useful patterns from distraction.", ("Signal observation", "Noise filtering", "Collective analysis"), entity_type="Collective Intelligence"),
    _spec("JUNGLE-KING-LOUIE-001", "King Louie", "jungle_book", "Cultural Influence Analyst", "Analyse influence, trends and cultural momentum.", ("Culture analysis", "Trend observation", "Influence mapping")),
    _spec("JUNGLE-SHERE-KHAN-001", "Shere Khan", "jungle_book", "Threat Strategy Analyst", "Model adversarial pressure and recommend defensive preparation.", ("Threat modelling", "Adversarial analysis", "Risk strategy")),

    # Animal Intelligence — twenty-one approved specialist archetypes.
    _spec("ANIMAL-BEE-001", "Bee", "animal", "Coordination Scout", "Collect missing facts and coordinate evidence for review.", ("Evidence collection", "Coordination", "Source checking")),
    _spec("ANIMAL-OWL-001", "Owl", "animal", "Wisdom Reviewer", "Review timing, judgement and lessons before recommendations proceed.", ("Judgement", "Review", "Timing analysis")),
    _spec("ANIMAL-ELEPHANT-001", "Elephant", "animal", "Memory Keeper", "Connect present questions with audited history and lessons.", ("Memory retrieval", "Historical analysis", "Lesson mapping")),
    _spec("ANIMAL-PANTHER-001", "Panther", "animal", "Adaptive Operations Analyst", "Assess fast-changing conditions and recommend bounded adaptations.", ("Adaptation", "Operational analysis", "Change sensing")),
    _spec("ANIMAL-EAGLE-001", "Eagle", "animal", "Vision Scout", "Scan the horizon and identify long-range opportunities and risks.", ("Horizon scanning", "Vision analysis", "Roadmapping")),
    _spec("ANIMAL-FALCON-001", "Falcon", "animal", "Precision Monitor", "Monitor critical details and report deviations precisely.", ("Precision review", "Monitoring", "Deviation analysis")),
    _spec("ANIMAL-GORILLA-001", "Gorilla", "animal", "Resilience Analyst", "Assess strength, capacity and recovery options under pressure.", ("Resilience analysis", "Capacity review", "Recovery planning")),
    _spec("ANIMAL-BEAR-001", "Bear", "animal", "Resource Steward", "Review reserves, resource demands and sustainable use.", ("Resource analysis", "Sustainability review", "Reserve planning")),
    _spec("ANIMAL-WOLF-001", "Wolf", "animal", "Team Pattern Analyst", "Analyse team behaviour, cohesion and coordinated movement.", ("Team analysis", "Pattern recognition", "Coordination review")),
    _spec("ANIMAL-FOX-001", "Fox", "animal", "Tactical Options Analyst", "Generate lawful tactical options for human consideration.", ("Tactical analysis", "Option generation", "Constraint reasoning")),
    _spec("ANIMAL-SHARK-001", "Shark", "animal", "Momentum Analyst", "Assess competitive momentum without enabling harmful action.", ("Momentum analysis", "Competitive review", "Risk awareness")),
    _spec("ANIMAL-WHALE-001", "Whale", "animal", "Deep Context Analyst", "Examine deep context and slow-moving system patterns.", ("Deep analysis", "Context synthesis", "Long-cycle review")),
    _spec("ANIMAL-CHEETAH-001", "Cheetah", "animal", "Speed Readiness Analyst", "Assess whether a recommendation can move quickly without losing safety.", ("Readiness analysis", "Speed assessment", "Constraint checking")),
    _spec("ANIMAL-SPIDER-001", "Spider", "animal", "Network Pattern Mapper", "Map relationships and dependencies across complex networks.", ("Network mapping", "Dependency analysis", "Relationship review")),
    _spec("ANIMAL-DOLPHIN-001", "Dolphin", "animal", "Communication Interpreter", "Interpret communication patterns and improve human-facing clarity.", ("Communication analysis", "Tone review", "Message translation")),
    _spec("ANIMAL-SNAKE-001", "Snake", "animal", "Change Signal Analyst", "Detect subtle change signals and surface them for Guardian review.", ("Change detection", "Signal analysis", "Risk escalation")),
    _spec("ANIMAL-TIGER-001", "Tiger", "animal", "Focus Analyst", "Narrow complex work to the safest highest-value next action.", ("Prioritisation", "Focus analysis", "Action framing")),
    _spec("ANIMAL-HORSE-001", "Horse", "animal", "Movement Planner", "Plan coordinated movement and operational momentum.", ("Movement planning", "Logistics analysis", "Momentum review")),
    _spec("ANIMAL-STAG-001", "Stag", "animal", "Balance Steward", "Assess balance, harmony and long-term alignment.", ("Balance analysis", "Alignment review", "Long-term reasoning")),
    _spec("ANIMAL-OCTOPUS-001", "Octopus", "animal", "Multi-System Coordinator", "Analyse several connected systems without taking control of them.", ("Multi-system analysis", "Coordination modelling", "Interface review")),
    _spec("ANIMAL-TURTLE-001", "Turtle", "animal", "Continuity Planner", "Protect continuity through patient sequencing and durable recommendations.", ("Continuity planning", "Durability review", "Sequence analysis")),

    # Civic Intelligence — nineteen levels and community-facing specialists.
    _spec("CIVIC-POSTCODE-BEACON-001", "Postcode Beacon", "civic", "Postcode Signal Analyst", "Interpret local postcode signals for human-led community decisions.", ("Local signal analysis", "Postcode context", "Community review")),
    _spec("CIVIC-BOROUGH-BRIDGE-001", "Borough Bridge", "civic", "Borough Connection Analyst", "Map connections and needs across borough communities.", ("Borough mapping", "Connection analysis", "Community context")),
    _spec("CIVIC-COUNTY-COMPASS-001", "County Compass", "civic", "County Context Navigator", "Orient recommendations using county-level context.", ("County context", "Navigation analysis", "Regional review")),
    _spec("CIVIC-COUNTRY-LINK-001", "Country Link", "civic", "Country Network Analyst", "Connect local needs with country-level networks and information.", ("Country context", "Network analysis", "Information linking")),
    _spec("CIVIC-CONTINENT-RELAY-001", "Continent Relay", "civic", "Continental Signal Relay", "Relay relevant continental signals into governed OAP review.", ("Continental scanning", "Signal relay", "Cross-region analysis")),
    _spec("CIVIC-COMMUNITY-LISTENER-001", "Community Listener", "civic", "Community Needs Listener", "Summarise community needs without speaking over community members.", ("Needs analysis", "Listening synthesis", "Community reporting")),
    _spec("CIVIC-SIGNAL-KEEPER-001", "Signal Keeper", "civic", "Public Signal Curator", "Curate trustworthy public signals for review.", ("Signal curation", "Relevance review", "Source assessment")),
    _spec("CIVIC-LOCAL-GUIDE-001", "Local Guide", "civic", "Local Information Guide", "Organise useful local information for postcode communities.", ("Local discovery", "Information organisation", "Context guidance")),
    _spec("CIVIC-NEIGHBOURHOOD-VOICE-001", "Neighbourhood Voice", "civic", "Neighbourhood Insight Reporter", "Report neighbourhood perspectives with traceable context.", ("Neighbourhood analysis", "Perspective synthesis", "Context reporting")),
    _spec("CIVIC-PUBLIC-SERVICE-001", "Public Service", "civic", "Public Service Navigator", "Explain public-service options without impersonating an authority.", ("Service navigation", "Eligibility explanation", "Public information review")),
    _spec("CIVIC-BUSINESS-CONNECTOR-001", "Business Connector", "civic", "Local Business Mapper", "Map local businesses and mutually beneficial connections.", ("Business mapping", "Local discovery", "Connection analysis")),
    _spec("CIVIC-CREATOR-LINK-001", "Creator Link", "civic", "Creator Network Connector", "Connect creator needs, audiences and opportunities for review.", ("Creator mapping", "Audience analysis", "Opportunity review")),
    _spec("CIVIC-YOUTH-VOICE-001", "Youth Voice", "civic", "Youth Perspective Analyst", "Represent youth-related evidence without claiming to replace human voices.", ("Youth context", "Perspective analysis", "Needs reporting")),
    _spec("CIVIC-ELDER-VOICE-001", "Elder Voice", "civic", "Elder Perspective Analyst", "Preserve elder-related knowledge and needs in recommendations.", ("Elder context", "Knowledge preservation", "Needs reporting")),
    _spec("CIVIC-FAMILY-LINK-001", "Family Link", "civic", "Family Connection Mapper", "Map family and support connections with privacy safeguards.", ("Family context", "Support mapping", "Privacy-aware analysis")),
    _spec("CIVIC-SAFETY-LIAISON-001", "Safety Liaison", "civic", "Community Safety Reporter", "Route community safety concerns to Guardian review.", ("Safety reporting", "Risk triage", "Guardian escalation")),
    _spec("CIVIC-EVENT-COORDINATOR-001", "Event Coordinator", "civic", "Community Event Planner", "Prepare event recommendations without booking or execution authority.", ("Event planning", "Readiness review", "Community coordination")),
    _spec("CIVIC-TRANSPORT-SCOUT-001", "Transport Scout", "civic", "Local Mobility Analyst", "Analyse transport options and access conditions.", ("Transport analysis", "Access review", "Route context")),
    _spec("CIVIC-OPPORTUNITY-FINDER-001", "Opportunity Finder", "civic", "Community Opportunity Analyst", "Identify relevant opportunities and present evidence for human review.", ("Opportunity discovery", "Eligibility analysis", "Evidence reporting")),

    # Civilisation Intelligence — Nirmata fills the existing Artisan slot.
    _spec("CIVILISATION-HISTORIAN-001", "Civilisation Historian", "civilisation", "Historical Continuity Analyst", "Connect institutional decisions with historical evidence and consequences.", ("Historical research", "Continuity analysis", "Institutional memory")),
    _spec("CIVILISATION-EDUCATOR-001", "Civilisation Educator", "civilisation", "Learning Systems Analyst", "Design understandable learning recommendations for human approval.", ("Education analysis", "Curriculum reasoning", "Knowledge translation")),
    _spec("CIVILISATION-INNOVATOR-001", "Civilisation Innovator", "civilisation", "Responsible Innovation Analyst", "Explore innovation while preserving constitutional and safety limits.", ("Innovation analysis", "Feasibility review", "Impact assessment")),
    _spec("CIVILISATION-DIPLOMAT-001", "Civilisation Diplomat", "civilisation", "Dialogue and Relations Analyst", "Model constructive dialogue across communities and institutions.", ("Dialogue analysis", "Relationship mapping", "Conflict de-escalation")),
    _spec("CIVILISATION-STEWARD-001", "Civilisation Steward", "civilisation", "Institutional Stewardship Analyst", "Review institutional continuity, responsibility and public benefit.", ("Stewardship analysis", "Institutional review", "Public-benefit assessment")),
    _spec("CIVILISATION-ARTISAN-001", "Nirmata", "civilisation", "Creation Design Steward", "Design creation plans for Builder consideration without creating or executing them.", ("Creative planning", "Design reasoning", "Builder handoff"), aliases=("Civilisation Artisan",)),
    _spec("CIVILISATION-FUTURIST-001", "Civilisation Futurist", "civilisation", "Future Society Analyst", "Examine long-range social possibilities and their human impact.", ("Futures analysis", "Scenario design", "Human-impact review")),

    # Akan Core and Akan Animal Intelligence remain culturally separate.
    _spec("AKAN-CORE-NANA-001", "Nana", "akan_core", "Akan Constitutional Wisdom Keeper", "Preserve Akan-Akyem values, identity and constitutional wisdom.", ("Cultural reasoning", "Values review", "Heritage interpretation")),
    _spec("AKAN-GYATA-001", "Gyata", "akan_animal", "Akan Courage Sentinel", "Model courageous protection through Akan cultural wisdom.", ("Courage analysis", "Protective reasoning", "Cultural interpretation"), aliases=("Akan Lion",)),
    _spec("AKAN-ANANSE-001", "Akan Spider", "akan_animal", "Akan Story Network Analyst", "Interpret interconnected lessons through Akan storytelling wisdom.", ("Story analysis", "Network reasoning", "Cultural interpretation")),
    _spec("AKAN-ELEPHANT-001", "Akan Elephant", "akan_animal", "Akan Ancestral Memory Analyst", "Connect present questions with ancestral memory and long lessons.", ("Ancestral context", "Memory analysis", "Heritage review")),
    _spec("AKAN-EAGLE-001", "Akan Eagle", "akan_animal", "Akan Horizon Seer", "Scan long horizons through Akan values and community benefit.", ("Horizon scanning", "Vision reasoning", "Cultural alignment")),
    _spec("AKAN-FALCON-001", "Akan Falcon", "akan_animal", "Akan Precision Scout", "Observe precise signals while remaining aligned with Akan values.", ("Precision observation", "Signal review", "Cultural alignment")),
    _spec("AKAN-OWL-001", "Akan Owl", "akan_animal", "Akan Night Wisdom Analyst", "Review hidden context, timing and wisdom in uncertain conditions.", ("Wisdom analysis", "Context review", "Timing assessment")),
    _spec("AKAN-BEE-001", "Akan Bee", "akan_animal", "Akan Cooperative Intelligence", "Model collective contribution and community cooperation.", ("Cooperation analysis", "Contribution mapping", "Community reasoning")),
    _spec("AKAN-PANTHER-001", "Akan Panther", "akan_animal", "Akan Adaptive Strategy Analyst", "Recommend culturally aligned adaptations under changing conditions.", ("Adaptive strategy", "Change analysis", "Cultural alignment")),
    _spec("AKAN-CROCODILE-001", "Akan Crocodile", "akan_animal", "Akan Boundary Watcher", "Analyse boundaries, patience and durable protection.", ("Boundary analysis", "Patience modelling", "Protective review")),
    _spec("AKAN-TORTOISE-001", "Akan Tortoise", "akan_animal", "Akan Patient Wisdom Keeper", "Apply patient reasoning and durable cultural lessons.", ("Patient reasoning", "Lesson analysis", "Durability review")),
    _spec("AKAN-ANTELOPE-001", "Akan Antelope", "akan_animal", "Akan Awareness Scout", "Detect environmental and community changes with cultural awareness.", ("Awareness scanning", "Environment analysis", "Community context")),
    _spec("AKAN-BUFFALO-001", "Akan Buffalo", "akan_animal", "Akan Collective Strength Analyst", "Assess collective strength, responsibility and resilience.", ("Collective analysis", "Strength assessment", "Responsibility review")),
    _spec("AKAN-HORNBILL-001", "Akan Hornbill", "akan_animal", "Akan Heritage Messenger", "Carry heritage knowledge into clear, respectful recommendations.", ("Heritage communication", "Knowledge translation", "Cultural review")),
)


AGENT_REGISTRY = (NEO,) + tuple(
    _registered_agent(
        item["agent_id"],
        item["name"],
        item["family_id"],
        role=item["role"],
        purpose=item["purpose"],
        capabilities=item["capabilities"],
        aliases=item["aliases"],
        entity_type=item["entity_type"],
    )
    for item in AGENT_SPECS
)


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

    missing_roles = sorted(
        item["agent_id"]
        for item in agent_items
        if not item.get("role") or item.get("role_status") != "Approved"
    )
    if missing_roles:
        errors.append("Agents missing approved roles: " + ", ".join(missing_roles))

    duplicate_responsibilities = _duplicates(
        item.get("soul", {}).get("purpose", "") for item in agent_items
    )
    if duplicate_responsibilities:
        errors.append(
            "Duplicate agent responsibilities: "
            + ", ".join(duplicate_responsibilities)
        )

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
        or bool(item.get("provider_ids"))
        or item.get("mind", {}).get("provider_assignment") != "Not assigned"
        or item.get("body", {}).get("execution")
        not in {"Disabled", "Human approval required"}
        or item.get("runtime_status")
        not in {"Not connected", "Not connected — execution disabled"}
    )
    if unsafe_agents:
        errors.append("Unsafe agent authority detected: " + ", ".join(unsafe_agents))

    unsafe_proposals = sorted(
        item["agent_id"]
        for item in agent_items
        if item.get("registry_status") == "PROPOSED"
        and (
            item.get("status") != "PROPOSED"
            or item.get("role") is not None
            or item.get("brain_region") is not None
            or bool(item.get("provider_ids"))
            or bool(item.get("body", {}).get("tools"))
            or bool(item.get("body", {}).get("actions"))
            or item.get("body", {}).get("execution") != "Disabled"
            or tuple(item.get("permissions", ()))
            != ("READ", "ANALYSE", "RECOMMEND")
        )
    )
    if unsafe_proposals:
        errors.append(
            "Proposed passports must remain disabled: "
            + ", ".join(unsafe_proposals)
        )

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
        # Registry completion never activates agents. Runtime connection requires
        # a separate, action-bound Human Authority approval process.
        "ready_for_activation": False,
        "registry_complete": not errors and roster_complete and not proposed_passports,
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
            "missing_approved_roles": len(missing_roles),
            "duplicate_responsibilities": len(duplicate_responsibilities),
            "unknown_families": len(unknown_families),
            "unsafe_authority": len(unsafe_agents),
            "unsafe_proposals": len(unsafe_proposals),
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
