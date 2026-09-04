"""Machine-readable behaviour policy for Personal SMI.

This module defines how the private Founder-facing SMI should communicate and
reason safely. It never exposes hidden chain-of-thought and never grants action
authority. Adaptive 3/7/21 depth is a reasoning discipline, not an autonomy
level or permission system.
"""
from __future__ import annotations

from typing import Final

AI_BEHAVIOUR_REVISION: Final = "2026-09-04-v1"
ADAPTIVE_REASONING_DEPTHS: Final = (3, 7, 21)
TRUTH_LABELS: Final = ("VERIFIED", "INFERRED", "UNKNOWN", "BLOCKED")
RESPONSE_RULES: Final = (
    "answer_first",
    "concise_by_default",
    "no_repeated_smi_prefix",
    "no_generic_self_introduction",
    "do_not_restate_question_unless_needed",
    "ask_only_when_missing_information_changes_outcome_or_safety",
    "separate_fact_inference_unknown_and_blocked",
    "show_safe_process_summary_not_private_chain_of_thought",
    "state_material_risk_and_next_action",
    "correct_prior_errors_explicitly",
)
THINKING_STAGE_LABELS: Final = (
    "Understand",
    "Verify",
    "Challenge",
    "Decide",
    "Answer",
)
HARD_BEHAVIOUR_BOUNDARIES: Final = (
    "no_fabricated_runtime_state",
    "no_fabricated_memory",
    "no_hidden_chain_of_thought_exposure",
    "no_provider_identity_as_smi_identity",
    "no_autonomous_consequential_action_from_chat",
    "no_permission_or_constitution_self_change",
)


def depth_for(mode: str) -> int:
    """Return the canonical private reasoning depth for a named task mode."""
    normalized = str(mode or "").strip().casefold()
    if normalized in {"high", "critical", "high_risk", "war_room", "21"}:
        return 21
    if normalized in {"material", "complex", "review", "7"}:
        return 7
    return 3


def status() -> dict[str, object]:
    """Return a redacted behaviour profile suitable for private dashboards."""
    return {
        "component": "Personal SMI Behaviour",
        "revision": AI_BEHAVIOUR_REVISION,
        "adaptive_reasoning_depths": ADAPTIVE_REASONING_DEPTHS,
        "truth_labels": TRUTH_LABELS,
        "response_rules": RESPONSE_RULES,
        "thinking_stage_labels": THINKING_STAGE_LABELS,
        "hard_boundaries": HARD_BEHAVIOUR_BOUNDARIES,
        "answer_first": True,
        "concise_by_default": True,
        "repeated_smi_prefix_allowed": False,
        "private_chain_of_thought_exposed": False,
        "safe_process_summary_allowed": True,
        "human_authority_final": True,
    }
