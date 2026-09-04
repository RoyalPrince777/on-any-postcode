"""Bounded command-intelligence chain inside the single SMI brain.

SGI, TGI, OGI, DGI, PGI and RGI are advisory capabilities. They do not create
new brains, Intelligence worlds, execution authority or approval authority.
They turn AGI specialist routing into an explainable command review before the
existing War Room, Judgement, Guardian/Aegis and Human Authority boundaries.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

COMMAND_STAGES: tuple[dict[str, str], ...] = (
    {
        "id": "sgi",
        "name": "Strategic General Intelligence",
        "verb": "strategise",
        "question": "Where are we trying to go and what matters most?",
    },
    {
        "id": "tgi",
        "name": "Tactical General Intelligence",
        "verb": "choose_next_move",
        "question": "What is the smartest bounded move next?",
    },
    {
        "id": "ogi",
        "name": "Operational General Intelligence",
        "verb": "operationalise",
        "question": "What dependencies and readiness checks are required?",
    },
    {
        "id": "dgi",
        "name": "Diagnostic General Intelligence",
        "verb": "diagnose",
        "question": "What could be wrong, missing or contradictory?",
    },
    {
        "id": "pgi",
        "name": "Predictive General Intelligence",
        "verb": "forecast",
        "question": "What could happen next, with uncertainty made explicit?",
    },
    {
        "id": "rgi",
        "name": "Resilience General Intelligence",
        "verb": "protect_continuity",
        "question": "How do we remain safe and recover if the plan fails?",
    },
)

_FAILURE_TERMS = (
    "fail",
    "failed",
    "error",
    "broken",
    "down",
    "timeout",
    "regression",
    "unhealthy",
    "missing",
    "blocked",
)


def _domains(agi_route: Mapping[str, Any]) -> tuple[str, ...]:
    values = agi_route.get("domains", ())
    if not isinstance(values, (tuple, list)):
        return ()
    return tuple(str(item) for item in values if str(item).strip())


class CommandIntelligence:
    """Build a six-stage advisory command review with no action authority."""

    component = "SMI Command Intelligence"

    def review(
        self,
        content: object,
        task_type: object,
        agi_route: Mapping[str, Any],
        *,
        high_impact: bool = False,
    ) -> dict[str, Any]:
        text = str(content or "").strip()
        lowered = text.casefold()
        task = str(task_type or "GENERAL").strip().upper() or "GENERAL"
        domains = _domains(agi_route)
        domain_text = ", ".join(domains) if domains else "approved specialist intelligence"
        diagnostic_triggered = any(term in lowered for term in _FAILURE_TERMS)

        stages = (
            {
                "id": "sgi",
                "name": "Strategic General Intelligence",
                "focus": "direction_and_priorities",
                "advice": (
                    f"Align {task} work to the requested outcome using {domain_text}; "
                    "prefer evidence-backed, reversible progress over premature scale."
                ),
            },
            {
                "id": "tgi",
                "name": "Tactical General Intelligence",
                "focus": "best_next_bounded_move",
                "advice": (
                    "Choose the smallest useful next step that produces proof, keeps rollback "
                    "possible and does not cross the Human Authority boundary."
                ),
            },
            {
                "id": "ogi",
                "name": "Operational General Intelligence",
                "focus": "dependencies_and_readiness",
                "advice": (
                    "Check identity, permissions, data provenance, service health, monitoring, "
                    "capacity, audit and rollback readiness before treating the step as operational."
                ),
            },
            {
                "id": "dgi",
                "name": "Diagnostic General Intelligence",
                "focus": "cause_and_gap_isolation",
                "triggered": diagnostic_triggered,
                "advice": (
                    "Isolate the failing or uncertain boundary using observed evidence before "
                    "retrying, repairing or changing dependencies."
                    if diagnostic_triggered
                    else "Keep diagnostic evidence available and investigate only observed failures or contradictions."
                ),
            },
            {
                "id": "pgi",
                "name": "Predictive General Intelligence",
                "focus": "bounded_forecast",
                "advice": (
                    "Forecast likely consequences as scenarios, not facts; attach confidence and "
                    "identify the evidence that would confirm or falsify the forecast."
                ),
                "prediction_is_fact": False,
            },
            {
                "id": "rgi",
                "name": "Resilience General Intelligence",
                "focus": "continuity_and_recovery",
                "advice": (
                    "Preserve a fail-closed path, rollback or safe degraded mode so one failed "
                    "dependency cannot force unsafe continuation."
                ),
            },
        )

        return {
            "component": self.component,
            "task_type": task,
            "command_path": tuple(stage["id"] for stage in stages),
            "stages": stages,
            "specialist_domains": domains,
            "high_impact": bool(high_impact),
            "human_review_required": bool(high_impact),
            "war_room_next": True,
            "judgement_next": True,
            "guardian_boundary_preserved": True,
            "execution_authority": False,
            "approval_authority": False,
            "human_authority_final": True,
        }

    def status(self) -> dict[str, Any]:
        return {
            "component": self.component,
            "ready": True,
            "kind": "bounded_command_capability_chain",
            "brain_count": 0,
            "stage_count": len(COMMAND_STAGES),
            "stages": COMMAND_STAGES,
            "command_path": tuple(item["id"] for item in COMMAND_STAGES),
            "independent_execute": False,
            "independent_approval": False,
            "prediction_claims_fact": False,
            "fail_closed_resilience": True,
            "human_authority_final": True,
            "truth_boundary": (
                "Command Intelligence produces strategic, tactical, operational, diagnostic, "
                "predictive and resilience advice only. War Room, Judgement, Guardian/Aegis and "
                "Human Authority retain their existing boundaries."
            ),
        }
