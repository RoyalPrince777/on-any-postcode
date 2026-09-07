"""Unified read-only status for every governed OAP Intelligence layer.

This module projects the single-SMI architecture as:

    one SMI brain
        -> seven canonical Intelligence Worlds
            -> specialist agent families and cross-system capabilities

It never treats a specialist family, provider or capability as another brain or
another top-level Intelligence World.  Status is evidence-aware: architecture,
registry and routing can be green while universal live-runtime proof remains
purple/incomplete.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from oap.smi.agi_core import AGICore

from . import agents, smi_capabilities

_WORLD_ICONS = {
    "earth": "🌍",
    "language": "🗣️",
    "life": "🌱",
    "movement": "🧭",
    "civic": "🏘️",
    "civilisation": "🏛️",
    "matrix": "🧩",
}


def _agent_counts() -> Counter[str]:
    return Counter(str(agent["family_id"]) for agent in agents.AGENT_REGISTRY)


def _provider_assignment_count(family_id: str) -> int:
    return sum(
        1
        for agent in agents.AGENT_REGISTRY
        if agent["family_id"] == family_id and tuple(agent.get("provider_ids") or ())
    )


def _world_family_projection(counts: Counter[str]) -> tuple[dict[str, Any], ...]:
    projected: list[dict[str, Any]] = []
    for family in agents.INTELLIGENCE_FAMILIES:
        family_id = str(family["id"])
        registered = int(counts[family_id])
        provider_assignments = _provider_assignment_count(family_id)
        projected.append(
            {
                "id": family_id,
                "name": str(family["name"]),
                "purpose": str(family["purpose"]),
                "world_id": str(family["world_id"]),
                "home_system": str(family["home_system"]),
                "classification": str(family["classification"]),
                "cross_world_ids": tuple(family.get("cross_world_ids") or ()),
                "registered_agents": registered,
                "human_approved_agents": registered,
                "provider_assignments": provider_assignments,
                "registry_light": "🟢" if registered > 0 else "🟣",
                "provider_light": "🟢" if provider_assignments else "🟣",
            }
        )
    return tuple(projected)


def status() -> dict[str, Any]:
    """Return the complete non-operational Intelligence hierarchy."""

    registry_validation = agents.validate_agent_registry()
    capability_status = smi_capabilities.smi_capability_status()
    capability_validation = capability_status["validation"]
    router = AGICore().status()
    counts = _agent_counts()
    families = _world_family_projection(counts)

    canonical_ids = tuple(str(item["id"]) for item in agents.INTELLIGENCE_WORLDS)
    router_ids = tuple(str(item) for item in router.get("world_ids", ()))
    routing_aligned = bool(
        router.get("ready")
        and router.get("canonical_world_model")
        and router_ids == canonical_ids
        and len(canonical_ids) == 7
    )

    specialist_status = capability_status.get("specialist_status", {})
    worlds: list[dict[str, Any]] = []
    for world in agents.INTELLIGENCE_WORLDS:
        world_id = str(world["id"])
        world_families = tuple(
            family for family in families if family["world_id"] == world_id
        )
        registered_agents = sum(
            int(family["registered_agents"]) for family in world_families
        )
        provider_assignments = sum(
            int(family["provider_assignments"]) for family in world_families
        )
        direct_specialist = specialist_status.get(world_id)
        direct_architecture = (
            bool(direct_specialist.get("architecture_passed"))
            if isinstance(direct_specialist, dict)
            and "architecture_passed" in direct_specialist
            else True
        )
        architecture_ready = bool(
            capability_validation["passed"]
            and routing_aligned
            and direct_architecture
        )
        worlds.append(
            {
                **dict(world),
                "icon": _WORLD_ICONS.get(world_id, "🧠"),
                "architecture_ready": architecture_ready,
                "routing_ready": routing_aligned and world_id in router_ids,
                "families": world_families,
                "family_count": len(world_families),
                "registered_agents": registered_agents,
                "provider_assignments": provider_assignments,
                "dedicated_family_roster": bool(world_families),
                "architecture_light": "🟢" if architecture_ready else "🟠",
                "routing_light": (
                    "🟢" if routing_aligned and world_id in router_ids else "🟠"
                ),
                "runtime_light": "🟣",
                "runtime_truth": (
                    "Architecture and bounded routing proven; universal live-data/provider "
                    "proof is evaluated capability-by-capability."
                ),
            }
        )

    registry_green = bool(
        registry_validation["passed"]
        and registry_validation["registry_complete"]
        and registry_validation["checks"]["registered_agents"]
        == agents.LOCKED_AGENT_COUNT
        and registry_validation["checks"]["human_approved_passports"]
        == agents.LOCKED_AGENT_COUNT
    )
    architecture_green = bool(
        capability_validation["passed"]
        and routing_aligned
        and all(bool(world["architecture_ready"]) for world in worlds)
    )
    memory_governed = all(
        agent.get("memory_system") == "HRM Core"
        and bool(agent.get("audit_required"))
        for agent in agents.AGENT_REGISTRY
    )

    command = capability_status["command_intelligence"]
    return {
        "component": "All OAP Intelligence",
        "brain": {
            "name": "Sovereign Megaverse Intelligence",
            "count": 1,
            "single_brain": True,
            "architecture_light": "🟢" if architecture_green else "🟠",
        },
        "world_count": len(worlds),
        "world_ids": canonical_ids,
        "worlds": tuple(worlds),
        "family_count": len(families),
        "families": families,
        "agent_count": len(agents.AGENT_REGISTRY),
        "agent_target": agents.LOCKED_AGENT_COUNT,
        "registry_green": registry_green,
        "registry_light": "🟢" if registry_green else "🟠",
        "architecture_green": architecture_green,
        "architecture_light": "🟢" if architecture_green else "🟠",
        "routing_green": routing_aligned,
        "routing_light": "🟢" if routing_aligned else "🟠",
        "memory_governed": memory_governed,
        "memory_light": "🟢" if memory_governed else "🟠",
        "runtime_light": "🟣",
        "runtime_truth": (
            "All-Intelligence architecture is not the same as universal live external-data "
            "proof. Live/current-data proof remains capability-specific."
        ),
        "cross_system_capabilities": capability_status["cross_system_capabilities"],
        "internal_capabilities": capability_status["internal_capabilities"],
        "general_intelligence": {
            "core_count": command["core_general_intelligence_count"],
            "supporting_count": command["supporting_count"],
            "total_count": command["total_general_intelligence_capabilities"],
            "core_path": command["core_path"],
            "supporting_ids": command["supporting_ids"],
            "independent_execute": False,
            "independent_approval": False,
        },
        "router": router,
        "validation": {
            "agent_registry": registry_validation,
            "capability_registry": capability_validation,
        },
        "providers_are_agents": False,
        "specialist_families_are_extra_worlds": False,
        "execution_granted": False,
        "approval_granted": False,
        "human_authority_final": True,
    }


def public_safe_status() -> dict[str, Any]:
    """Return a Founder-safe projection without provider or passport internals."""

    snapshot = status()
    return {
        "component": snapshot["component"],
        "brain": snapshot["brain"],
        "world_count": snapshot["world_count"],
        "world_ids": snapshot["world_ids"],
        "worlds": snapshot["worlds"],
        "family_count": snapshot["family_count"],
        "families": snapshot["families"],
        "agent_count": snapshot["agent_count"],
        "agent_target": snapshot["agent_target"],
        "registry_green": snapshot["registry_green"],
        "registry_light": snapshot["registry_light"],
        "architecture_green": snapshot["architecture_green"],
        "architecture_light": snapshot["architecture_light"],
        "routing_green": snapshot["routing_green"],
        "routing_light": snapshot["routing_light"],
        "memory_governed": snapshot["memory_governed"],
        "memory_light": snapshot["memory_light"],
        "runtime_light": snapshot["runtime_light"],
        "runtime_truth": snapshot["runtime_truth"],
        "cross_system_capabilities": snapshot["cross_system_capabilities"],
        "internal_capabilities": snapshot["internal_capabilities"],
        "general_intelligence": snapshot["general_intelligence"],
        "providers_are_agents": False,
        "specialist_families_are_extra_worlds": False,
        "execution_granted": False,
        "approval_granted": False,
        "human_authority_final": True,
    }
