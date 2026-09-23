"""Governed recursive self-improvement loop for the OAP organism.

This module turns observed weaknesses into bounded improvement proposals. It can
analyse, recommend, route Matrix Signals and record learning receipts, but it
cannot rewrite its own authority, modify permissions, create agents, deploy,
self-approve, or bypass Guardian, Green Gate, War Room or Human Authority.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from . import matrix_signal_bus, smi_receipt_backend

SELF_IMPROVEMENT_CYCLE: tuple[str, ...] = (
    "observe",
    "measure",
    "detect_weakness",
    "matrix_analyse",
    "smi_recommend",
    "war_room_review",
    "human_authority_approve",
    "builder_change",
    "tests",
    "green_gate",
    "deploy",
    "hrm_receipt",
    "learn",
    "repeat",
)

ALLOWED_IMPROVEMENT_DOMAINS: tuple[str, ...] = (
    "knowledge",
    "routing",
    "prompts",
    "recommendations",
    "architecture",
    "test_coverage",
    "reliability",
    "observability",
    "performance",
    "recovery",
)

FORBIDDEN_SELF_CHANGE_DOMAINS: tuple[str, ...] = (
    "authority",
    "permissions",
    "constitution",
    "security_boundaries",
    "agent_registry",
    "founder_identity",
    "guardian_authority",
    "green_gate_authority",
    "war_room_authority",
    "deployment_authority",
)

MATRIX_LEADS_BY_DOMAIN: dict[str, str] = {
    "knowledge": "Oracle",
    "routing": "Keymaker",
    "prompts": "Morpheus",
    "recommendations": "Oracle",
    "architecture": "Architect",
    "test_coverage": "Trinity",
    "reliability": "Neo",
    "observability": "Trinity",
    "performance": "Architect",
    "recovery": "Neo",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _clean_items(items: Iterable[str]) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(str(item).strip() for item in items if str(item).strip())
    )


def status() -> dict[str, Any]:
    """Return the bounded self-improvement contract."""

    return {
        "name": "OAP Recursive Self-Improvement",
        "mode": "governed_learning_loop",
        "timestamp_utc": _now(),
        "cycle": SELF_IMPROVEMENT_CYCLE,
        "allowed_domains": ALLOWED_IMPROVEMENT_DOMAINS,
        "forbidden_self_change_domains": FORBIDDEN_SELF_CHANGE_DOMAINS,
        "matrix_signal_bus": "required",
        "smi_review": "required",
        "hrm_learning_receipt": "matrix_learning_receipt",
        "guardian": "required",
        "green_gate": "required",
        "war_room": "required_for_consequential_change",
        "human_authority": "final",
        "builder_execution": "separate_approved_path_only",
        "execution_granted": False,
        "self_approval_allowed": False,
        "permission_change_allowed": False,
        "authority_growth_allowed": False,
        "agent_creation_allowed": False,
        "automatic_deploy_allowed": False,
        "full_green": False,
    }


def _normalise_observation(observation: Mapping[str, Any]) -> dict[str, Any]:
    domain = str(observation.get("domain") or "").strip().lower()
    if domain in FORBIDDEN_SELF_CHANGE_DOMAINS:
        raise ValueError(f"Self-improvement cannot modify protected domain: {domain}")
    if domain not in ALLOWED_IMPROVEMENT_DOMAINS:
        raise ValueError(f"Unsupported improvement domain: {domain or 'missing'}")

    problem = str(observation.get("problem") or "").strip()
    if not problem:
        raise ValueError("Observation problem is required")

    evidence = _clean_items(observation.get("evidence") or ())
    metric = str(observation.get("metric") or "").strip()
    current_value = observation.get("current_value")
    target_value = observation.get("target_value")
    severity = str(observation.get("severity") or "medium").strip().lower()
    if severity not in {"low", "medium", "high", "critical"}:
        raise ValueError("Unsupported observation severity")

    return {
        "domain": domain,
        "problem": problem,
        "evidence": evidence,
        "metric": metric,
        "current_value": current_value,
        "target_value": target_value,
        "severity": severity,
    }


def propose_improvement(
    observation: Mapping[str, Any],
    *,
    recommendation: str,
    rollback: str,
    tests: Iterable[str],
    consequential: bool = False,
) -> dict[str, Any]:
    """Turn one measured weakness into a bounded improvement proposal."""

    item = _normalise_observation(observation)
    recommendation = recommendation.strip()
    rollback = rollback.strip()
    test_plan = _clean_items(tests)
    if not recommendation:
        raise ValueError("Recommendation is required")
    if not rollback:
        raise ValueError("Rollback plan is required")
    if not test_plan:
        raise ValueError("At least one test is required")

    proposal_id = f"RSI-{uuid4().hex[:12].upper()}"
    lead = MATRIX_LEADS_BY_DOMAIN[item["domain"]]
    signal = matrix_signal_bus.route_signal(
        sender=lead,
        topic=f"Recursive improvement: {item['problem']}",
        kind="self_improvement_proposal",
        recipients=("Trinity", "SMI"),
        urgency=(
            "critical"
            if item["severity"] == "critical"
            else "high"
            if item["severity"] == "high"
            else "normal"
        ),
        evidence=item["evidence"],
        requested_action="review_improvement_proposal",
        consequential=consequential,
    )

    return {
        "proposal_id": proposal_id,
        "timestamp_utc": _now(),
        "state": "proposed_for_review",
        "observation": item,
        "recommendation": recommendation,
        "rollback": rollback,
        "tests": test_plan,
        "matrix_lead": lead,
        "matrix_signal": signal,
        "smi_review_required": True,
        "guardian_required": True,
        "green_gate_required": True,
        "war_room_required": consequential,
        "human_authority_required": consequential,
        "builder_change_allowed_only_after_approval": True,
        "execution_granted": False,
        "external_action_taken": False,
        "self_approval_allowed": False,
        "automatic_deploy_allowed": False,
        "full_green": False,
    }


def review_gate(
    proposal: Mapping[str, Any],
    *,
    guardian_pass: bool,
    war_room_reviewed: bool,
    human_authority_approved: bool,
    rollback_ready: bool,
    tests_defined: bool,
) -> dict[str, Any]:
    """Evaluate whether a proposal may be handed to a separate Builder path."""

    consequential = bool(proposal.get("war_room_required"))
    required = {
        "guardian_pass": bool(guardian_pass),
        "war_room_reviewed": bool(war_room_reviewed) if consequential else True,
        "human_authority_approved": (
            bool(human_authority_approved) if consequential else True
        ),
        "rollback_ready": bool(rollback_ready),
        "tests_defined": bool(tests_defined),
    }
    ready = all(required.values())
    return {
        "proposal_id": str(proposal.get("proposal_id") or "unknown"),
        "requirements": required,
        "ready_for_separate_builder_path": ready,
        "builder_may_be_requested": ready,
        "execution_granted": False,
        "automatic_deploy_allowed": False,
        "self_approval_allowed": False,
        "next_gate": (
            "Separate approved Builder path may implement with tests and rollback."
            if ready
            else "Hold until all required governance evidence is present."
        ),
    }


def record_learning(
    proposal: Mapping[str, Any],
    *,
    outcome: str,
    before_state: str,
    after_state: str,
    lesson: str,
    tests_passed: bool,
    rollback_available: bool,
    reviewed_outcome_ref: str = "",
) -> dict[str, Any]:
    """Write a governed Matrix learning receipt only with reviewed outcome provenance."""

    proposal_id = str(proposal.get("proposal_id") or "").strip()
    if not proposal_id:
        raise ValueError("proposal_id is required")
    lesson = lesson.strip()
    if not lesson:
        raise ValueError("Learning lesson is required")
    reviewed_outcome_ref = reviewed_outcome_ref.strip()
    if not reviewed_outcome_ref:
        raise ValueError("Reviewed outcome reference is required")

    receipt = smi_receipt_backend.write_receipt(
        "matrix_learning_receipt",
        {
            "brain_part": "recursive_self_improvement",
            "gate": 7,
            "command": "record_learning",
            "signal": "🟡" if tests_passed else "🟠",
            "guardian": "required",
            "green_gate": "required",
            "founder_final": "required_for_full_green",
            "safe_payload": {
                "proposal_id": proposal_id,
                "reviewed_outcome_ref": reviewed_outcome_ref,
                "outcome": str(outcome).strip(),
                "before_state": str(before_state).strip(),
                "after_state": str(after_state).strip(),
                "lesson": lesson,
                "tests_passed": bool(tests_passed),
                "rollback_available": bool(rollback_available),
                "external_action_taken_by_learning_loop": False,
                "authority_changed": False,
                "permissions_changed": False,
                "automatic_deploy": False,
            },
        },
        require_durable=True,
    )
    durable_learning = bool(
        receipt.get("ok") is True
        and receipt.get("read_back_ok") is True
        and receipt.get("durable") is True
        and receipt.get("fallback_used") is False
        and receipt.get("receipt_kind") == "matrix_learning_receipt"
    )

    return {
        "proposal_id": proposal_id,
        "reviewed_outcome_ref": reviewed_outcome_ref,
        "state": "learning_recorded" if durable_learning else "durable_learning_unproven",
        "receipt": receipt,
        "tests_passed": bool(tests_passed),
        "rollback_available": bool(rollback_available),
        "matrix_update_allowed": durable_learning,
        "authority_changed": False,
        "permissions_changed": False,
        "execution_granted": False,
        "full_green": False,
    }
