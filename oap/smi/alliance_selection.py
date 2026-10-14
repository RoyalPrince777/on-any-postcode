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
    ("Shark", ("early_signal_detection",)),
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
