"""Canonical, read-only anatomy for the OAP Digital Organism.

This module is an architecture registry, not an execution engine.  It keeps
approved system boundaries in one place and validates them before they are
rendered.  It never reads or writes the database and exposes no mutation
operations.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any

INTELLIGENCE_WORLDS = (
    "GPT Intelligence",
    "Claude Intelligence",
    "Gemini Intelligence",
    "Kimi Intelligence",
    "Grok Intelligence",
    "Edge/Copilot Intelligence",
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

ADVISORY_AGENTS = ("Neo", "Akela", "Bagheera", "Gyata", "Shere Khan")

# Named advisors are preserved, but no region or governance-role assignment is
# approved in this read-only slice.  Assignments must be added only after human
# approval and will be checked for duplicate ownership by validate_architecture.
AGENT_ROLE_ASSIGNMENTS: tuple[dict[str, str], ...] = ()

GOVERNANCE_LAW = (
    {"actor": "Intelligence", "action": "proposes"},
    {"actor": "Guardian", "action": "protects"},
    {"actor": "Builder", "action": "creates"},
    {"actor": "Identity", "action": "validates"},
    {
        "actor": "Sovereign",
        "action": "decides",
        "authority": "Human Authority",
    },
    {"actor": "HRM", "action": "remembers"},
    {"actor": "Organism", "action": "grows"},
)

SMI_OUTPUT_STATES = (
    "RECOMMENDATION_READY",
    "REVIEW_REQUIRED",
    "BLOCK_REQUEST",
    "SYSTEM_LOG_ONLY",
)

APPROVED_STATE_PATH = (
    "RECEIVED",
    "IDENTITY_VERIFIED",
    "SMI_REVIEWED",
    "GUARDIAN_PASSED",
    "HUMAN_REVIEW_REQUIRED",
    "HUMAN_APPROVED",
    "KERNEL_EXECUTED",
    "HRM_RECORDED",
)

REJECTED_STATE_PATH = (
    "HUMAN_REJECTED",
    "EXECUTION_BLOCKED",
    "HRM_RECORDED",
)


ORGANISM_SYSTEMS: tuple[dict[str, Any], ...] = (
    {
        "id": "oasis",
        "name": "OASIS",
        "anatomy": "Environment",
        "responsibility": "Hosts the organism's local and global operating habitat.",
        "aliases": (),
    },
    {
        "id": "sp_signals",
        "name": "SP Signals",
        "anatomy": "Senses",
        "responsibility": "Receives observable signals without deciding their outcome.",
        "aliases": (),
    },
    {
        "id": "nexus",
        "name": "NEXUS",
        "anatomy": "Nervous system",
        "responsibility": "Carries signals between systems; it is not another brain.",
        "aliases": (),
    },
    {
        "id": "identity",
        "name": "Identity Engine",
        "anatomy": "Identity and DNA validation",
        "responsibility": "Validates the requester and applicable permissions.",
        "aliases": ("Identity",),
    },
    {
        "id": "smi",
        "name": "SMI",
        "anatomy": "Brain",
        "responsibility": "Coordinates intelligence and produces recommendations only.",
        "aliases": ("Sovereign Megaverse Intelligence",),
    },
    {
        "id": "aegis",
        "name": "Aegis",
        "anatomy": "Defensive shield",
        "responsibility": "Performs rapid technical and constitutional safety checks.",
        "aliases": (),
    },
    {
        "id": "guardian",
        "name": "Guardian",
        "anatomy": "Protective gate",
        "responsibility": "Protects the organism and blocks unsafe progression.",
        "aliases": (),
    },
    {
        "id": "war_room",
        "name": "War Room",
        "anatomy": "Strategic simulation chamber",
        "responsibility": "Simulates consequences; it never makes the final decision.",
        "aliases": (),
    },
    {
        "id": "human_authority",
        "name": "Human Authority",
        "anatomy": "Sovereign will",
        "responsibility": "Approves or rejects; it is the only final authority.",
        "aliases": ("Sovereign",),
    },
    {
        "id": "living_kernel",
        "name": "Living Kernel",
        "anatomy": "Heart",
        "responsibility": "Coordinates only actions carrying recorded human approval.",
        "aliases": ("OAP Kernel",),
    },
    {
        "id": "body_systems",
        "name": "Body Systems",
        "anatomy": "Body and execution",
        "responsibility": "Builder creates and bounded systems execute approved work.",
        "aliases": ("Builder", "Execution Systems"),
    },
    {
        "id": "memory",
        "name": "HRM and JOOG MEMORY",
        "anatomy": "Memory",
        "responsibility": "Records context, decisions, outcomes and organism learning.",
        "aliases": ("HRM Core",),
    },
)


SMI_REGIONS: tuple[dict[str, str], ...] = (
    {
        "id": "left_hemisphere",
        "name": "Left hemisphere",
        "responsibility": "Logic, rules, code, mathematics and structured analysis.",
        "connection": "Registry and specialist Intelligence",
        "kind": "internal_region",
    },
    {
        "id": "right_hemisphere",
        "name": "Right hemisphere",
        "responsibility": "Creativity, culture, scenarios and human meaning.",
        "connection": "Synthetic Mind and cultural Intelligence",
        "kind": "internal_region",
    },
    {
        "id": "corpus_callosum",
        "name": "Corpus callosum",
        "responsibility": "Merges logical and creative analysis into one recommendation.",
        "connection": "Both hemispheres",
        "kind": "internal_region",
    },
    {
        "id": "frontal_lobe",
        "name": "Frontal lobe",
        "responsibility": "Planning, strategy, judgement and recommendations.",
        "connection": "War Room",
        "kind": "internal_region",
    },
    {
        "id": "parietal_lobe",
        "name": "Parietal lobe",
        "responsibility": "Postcodes, maps, navigation and spatial organism state.",
        "connection": "OASIS and movement systems",
        "kind": "internal_region",
    },
    {
        "id": "temporal_lobe",
        "name": "Temporal lobe",
        "responsibility": "Language, sound, conversation and contextual recognition.",
        "connection": "LinkUp, Media and HRM retrieval",
        "kind": "internal_region",
    },
    {
        "id": "occipital_lobe",
        "name": "Occipital lobe",
        "responsibility": "Images, video, visual recognition and design interpretation.",
        "connection": "Vision inputs and Media",
        "kind": "internal_region",
    },
    {
        "id": "thalamus",
        "name": "Thalamus",
        "responsibility": "Receives, filters and routes incoming signals.",
        "connection": "SP Signals and NEXUS",
        "kind": "internal_region",
    },
    {
        "id": "hypothalamus",
        "name": "Hypothalamus",
        "responsibility": "Balances priority, resources, urgency and system needs.",
        "connection": "Infrastructure and performance",
        "kind": "internal_region",
    },
    {
        "id": "hippocampus",
        "name": "Hippocampus",
        "responsibility": "Forms and retrieves contextual memories.",
        "connection": "HRM Core",
        "kind": "internal_region",
    },
    {
        "id": "amygdala",
        "name": "Amygdala",
        "responsibility": "Performs rapid threat and risk detection.",
        "connection": "Aegis and Guardian",
        "kind": "internal_region",
    },
    {
        "id": "cerebellum",
        "name": "Cerebellum",
        "responsibility": "Coordinates accuracy, timing, testing and correction.",
        "connection": "Execution systems",
        "kind": "internal_region",
    },
    {
        "id": "brainstem",
        "name": "Brainstem",
        "responsibility": "Maintains health, continuity and the brain-to-body bridge.",
        "connection": "NEXUS and Living Kernel",
        "kind": "bridge",
    },
    {
        "id": "synthetic_mind",
        "name": "Synthetic Mind",
        "responsibility": "Supports integrated reasoning inside the single SMI brain.",
        "connection": "Right hemisphere and corpus callosum",
        "kind": "internal_organ",
    },
)


BOUNDARY_GUARDS = (
    {
        "components": "SMI / Synthetic Mind",
        "resolution": "Synthetic Mind is an internal SMI organ, never a second brain.",
    },
    {
        "components": "NEXUS / Brainstem",
        "resolution": "NEXUS carries signals; Brainstem is the SMI-to-body bridge.",
    },
    {
        "components": "Living Kernel / OAP Kernel",
        "resolution": "Both names resolve to one canonical heart: Living Kernel.",
    },
    {
        "components": "War Room / Human Authority",
        "resolution": "War Room simulates and reviews; Human Authority decides.",
    },
    {
        "components": "Aegis / Guardian",
        "resolution": "Aegis checks threats; Guardian protects the governance gate.",
    },
)


PROPOSED_REFINEMENTS = (
    {
        "title": "Confirm Body Systems membership",
        "description": (
            "Approve the exact Infrastructure, SIKA, Trust, LinkUp, Media and "
            "movement interfaces that sit behind the existing Body Systems boundary."
        ),
        "requires_human_approval": True,
    },
    {
        "title": "Approve named-agent region assignments",
        "description": (
            "Map preserved advisory agents to SMI regions only after checking every "
            "assignment for role overlap."
        ),
        "requires_human_approval": True,
    },
    {
        "title": "Reconcile legacy governance labels",
        "description": (
            "Inventory historical labels and compatibility paths before applying the "
            "canonical Intelligence terminology across active documentation."
        ),
        "requires_human_approval": True,
    },
)


def _normalise(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def _duplicates(values: Iterable[str]) -> list[str]:
    seen: dict[str, str] = {}
    duplicates: set[str] = set()
    for value in values:
        normalised = _normalise(value)
        if normalised in seen:
            duplicates.add(value)
        else:
            seen[normalised] = value
    return sorted(duplicates)


def validate_architecture(
    systems: Iterable[Mapping[str, Any]] = ORGANISM_SYSTEMS,
    regions: Iterable[Mapping[str, str]] = SMI_REGIONS,
    worlds: Iterable[str] = INTELLIGENCE_WORLDS,
    governance: Iterable[Mapping[str, str]] = GOVERNANCE_LAW,
    agent_roles: Iterable[Mapping[str, str]] = AGENT_ROLE_ASSIGNMENTS,
) -> dict[str, Any]:
    """Validate uniqueness and locked authority boundaries without side effects."""

    system_items = tuple(systems)
    region_items = tuple(regions)
    world_items = tuple(worlds)
    governance_items = tuple(governance)
    agent_role_items = tuple(agent_roles)
    errors: list[str] = []

    duplicate_ids = _duplicates(item["id"] for item in system_items)
    if duplicate_ids:
        errors.append("Duplicate system identifiers: " + ", ".join(duplicate_ids))

    system_labels = [item["name"] for item in system_items]
    for item in system_items:
        system_labels.extend(item.get("aliases", ()))
    duplicate_labels = _duplicates(system_labels)
    if duplicate_labels:
        errors.append("Duplicate system names or aliases: " + ", ".join(duplicate_labels))

    duplicate_anatomy_roles = _duplicates(item["anatomy"] for item in system_items)
    if duplicate_anatomy_roles:
        errors.append(
            "Overlapping overall-system anatomy roles: "
            + ", ".join(duplicate_anatomy_roles)
        )

    brains = [item for item in system_items if item["anatomy"] == "Brain"]
    if len(brains) != 1 or brains[0]["id"] != "smi":
        errors.append("SMI must be the one and only brain.")

    final_authorities = [
        item for item in system_items if item["id"] == "human_authority"
    ]
    if (
        len(final_authorities) != 1
        or "only final authority"
        not in final_authorities[0]["responsibility"].casefold()
    ):
        errors.append("Human Authority must remain the only final authority.")

    duplicate_regions = _duplicates(item["id"] for item in region_items)
    duplicate_region_names = _duplicates(item["name"] for item in region_items)
    if duplicate_regions or duplicate_region_names:
        errors.append("SMI region names and identifiers must be unique.")

    region_by_id = {item["id"]: item for item in region_items}
    if region_by_id.get("brainstem", {}).get("kind") != "bridge":
        errors.append("Brainstem must remain a bridge, not a second Kernel.")
    if region_by_id.get("synthetic_mind", {}).get("kind") != "internal_organ":
        errors.append("Synthetic Mind must remain an internal SMI organ.")

    if len(world_items) != 6 or _duplicates(world_items):
        errors.append("The six Intelligence worlds must remain unique and complete.")

    duplicate_advisors = _duplicates(ADVISORY_AGENTS)
    duplicate_agent_assignments = _duplicates(
        item["agent"] for item in agent_role_items
    )
    duplicate_agent_roles = _duplicates(item["role"] for item in agent_role_items)
    if duplicate_advisors:
        errors.append("Duplicate advisory agents: " + ", ".join(duplicate_advisors))
    if duplicate_agent_assignments:
        errors.append(
            "Agents assigned to overlapping roles: "
            + ", ".join(duplicate_agent_assignments)
        )
    if duplicate_agent_roles:
        errors.append("Duplicate agent roles: " + ", ".join(duplicate_agent_roles))

    expected_law = (
        ("Intelligence", "proposes"),
        ("Guardian", "protects"),
        ("Builder", "creates"),
        ("Identity", "validates"),
        ("Sovereign", "decides"),
        ("HRM", "remembers"),
        ("Organism", "grows"),
    )
    actual_law = tuple(
        (item.get("actor"), item.get("action")) for item in governance_items
    )
    if actual_law != expected_law:
        errors.append("The locked governance law has changed.")

    sovereign = next(
        (item for item in governance_items if item.get("actor") == "Sovereign"),
        {},
    )
    if sovereign.get("authority") != "Human Authority":
        errors.append("Sovereign decisions must belong to Human Authority.")

    canonical_names = system_labels + [item["name"] for item in region_items]
    canonical_names += list(world_items) + list(ADVISORY_AGENTS)
    banned_names = [
        name
        for name in canonical_names
        if _normalise(name) == "kaa" or "council" in name.casefold()
    ]
    if banned_names:
        errors.append("Prohibited or legacy names found: " + ", ".join(banned_names))

    anatomy_names = tuple(part["name"] for part in AGENT_ANATOMY)
    if anatomy_names != ("Soul", "Mind", "Body"):
        errors.append("Every agent anatomy must remain Soul, Mind and Body only.")

    return {
        "passed": not errors,
        "errors": errors,
        "checks": {
            "canonical_systems": len(system_items),
            "smi_regions": len(region_items),
            "intelligence_worlds": len(world_items),
            "duplicate_systems": len(duplicate_ids),
            "duplicate_names": len(duplicate_labels),
            "overlapping_anatomy_roles": len(duplicate_anatomy_roles),
            "duplicate_agent_roles": len(duplicate_agent_roles),
            "brain_count": len(brains),
            "final_authority": "Human Authority",
        },
    }


def get_public_anatomy() -> dict[str, Any]:
    """Return the immutable architecture as a template-ready public projection."""

    validation = validate_architecture()
    return {
        "systems": ORGANISM_SYSTEMS,
        "smi_regions": SMI_REGIONS,
        "intelligence_worlds": INTELLIGENCE_WORLDS,
        "agent_anatomy": AGENT_ANATOMY,
        "advisory_agents": ADVISORY_AGENTS,
        "governance_law": GOVERNANCE_LAW,
        "smi_output_states": SMI_OUTPUT_STATES,
        "approved_state_path": APPROVED_STATE_PATH,
        "rejected_state_path": REJECTED_STATE_PATH,
        "boundary_guards": BOUNDARY_GUARDS,
        "proposed_refinements": PROPOSED_REFINEMENTS if validation["passed"] else (),
        "validation": validation,
        "human_authority": {
            "status": "Final approval required",
            "message": "This view cannot execute or approve architecture changes.",
        },
    }
