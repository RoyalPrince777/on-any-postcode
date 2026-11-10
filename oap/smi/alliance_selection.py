"""Bounded Alliance selection: advisory roles, not agent processes or authority."""

from __future__ import annotations

from dataclasses import dataclass

from oap.smi.capability_fabric import select_capabilities

# Existing Alliance roles only. Each capability has one accountable lead.
_ROLE_CAPABILITIES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Neo", ("agentic_code_review", "workspace_isolation", "artifact_workflows")),
    ("Spider", ("long_context_synthesis", "parallel_retrieval", "evidence_first")),
    ("Fox", ("local_first_failover", "budget_aware_handoff", "long_horizon_delivery")),
    ("Octopus", ("tool_orchestration", "multi_expert_synthesis", "context_compaction")),
    ("Owl", ("advisor_challenger", "structured_output", "financial_analysis")),
    ("Queen Bee", ("scale_out_swarm", "persistent_subagents")),
    ("Falcon", ("cost_aware_routing", "safe_process_telemetry")),
    ("Oracle", ("live_signal_awareness", "cited_live_research")),
    ("Elephant", ("memory_reconstruction", "context_tiering")),
    ("Bagheera", ("agent_governance",)),
    ("Shere Khan", ("gap_adversarial_review",)),
    ("Trinity", ("multimodal_fusion", "realtime_audio_visual")),
    ("Morpheus", ("adaptive_reasoning", "skill_distillation")),
    ("Tigress", ("live_steering",)),
    ("Gyata", ("alignment",)),
)


@dataclass(frozen=True)
class AllianceSelection:
    capabilities: tuple[str, ...]
    specialists: tuple[str, ...]
    unassigned_capabilities: tuple[str, ...]
    advisory_only: bool = True
    founder_final: bool = True


def select_alliance(
    task_type: str,
    query: str,
    *,
    high_impact: bool = False,
    distributed_work: bool = False,
    limit: int = 8,
) -> AllianceSelection:
    """Select the smallest mapped team without spawning workers or granting access."""
    capabilities = select_capabilities(
        task_type, query, high_impact=high_impact, limit=limit
    )
    selected: list[str] = []
    unassigned: list[str] = []
    for capability in capabilities:
        owner = next(
            (name for name, owned in _ROLE_CAPABILITIES if capability in owned),
            None,
        )
        if owner is None:
            unassigned.append(capability)
        elif owner != "Queen Bee" or distributed_work:
            if owner not in selected:
                selected.append(owner)
        else:
            unassigned.append(capability)
    return AllianceSelection(capabilities, tuple(selected), tuple(unassigned))


@dataclass(frozen=True)
class PassportVerifiedSelection:
    """An advisory mission team grounded in the canonical agent registry."""

    capabilities: tuple[str, ...]
    specialists: tuple[str, ...]
    unassigned_capabilities: tuple[str, ...]
    excluded_unregistered: tuple[str, ...]
    excluded_inactive: tuple[str, ...]
    advisory_only: bool = True
    authority_granted: bool = False
    founder_final: bool = True


def select_passport_verified_alliance(
    task_type: str,
    query: str,
    *,
    high_impact: bool = False,
    distributed_work: bool = False,
    limit: int = 8,
) -> PassportVerifiedSelection:
    """Choose a task-specific advisory team; never register or activate an agent.

    Legacy capability recommendations stay intact. Missing, duplicate, proposed,
    or inactive passport entries fail closed without inventing aliases or IDs.
    """
    from mission_control.agents import AGENT_REGISTRY

    proposed = select_alliance(
        task_type, query, high_impact=high_impact,
        distributed_work=distributed_work, limit=limit,
    )
    by_name: dict[str, list[object]] = {}
    for entry in AGENT_REGISTRY:
        name = str(entry.get("name", "")).casefold()
        if name:
            by_name.setdefault(name, []).append(entry)

    selected: list[str] = []
    unregistered: list[str] = []
    inactive: list[str] = []
    for name in proposed.specialists:
        passports = by_name.get(name.casefold(), [])
        if len(passports) != 1 or not passports[0].get("agent_id"):
            unregistered.append(name)
            continue
        if passports[0].get("registry_status") != "ACTIVE":
            inactive.append(name)
            continue
        selected.append(name)
    return PassportVerifiedSelection(
        capabilities=proposed.capabilities,
        specialists=tuple(selected),
        unassigned_capabilities=proposed.unassigned_capabilities,
        excluded_unregistered=tuple(unregistered),
        excluded_inactive=tuple(inactive),
    )
