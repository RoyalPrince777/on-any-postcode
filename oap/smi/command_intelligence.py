"""Bounded general-intelligence capabilities inside the single SMI brain.

AGI remains the cross-domain routing capability. This module contributes the
other eight core capabilities in the locked command spine and six supporting
capabilities that feed the spine without becoming extra brains, worlds or
authority holders.

Core: AGI -> SGI -> TGI -> OGI -> DGI -> PGI -> RGI -> AdGI -> MGI.
Support: CGI, CoGI, EGI, LGI, TeGI and ReGI.
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
    {
        "id": "adgi",
        "name": "Adaptive General Intelligence",
        "verb": "adapt",
        "question": "What should change when new evidence changes the situation?",
    },
    {
        "id": "mgi",
        "name": "Meta General Intelligence",
        "verb": "self_check",
        "question": "Is the reasoning itself sound, complete and calibrated?",
    },
)

SUPPORTING_INTELLIGENCE: tuple[dict[str, str], ...] = (
    {
        "id": "cgi",
        "name": "Creative General Intelligence",
        "focus": "alternatives_and_invention",
        "feeds": "SGI,TGI,War Room",
    },
    {
        "id": "cogi",
        "name": "Coordination General Intelligence",
        "focus": "agents_domains_and_parallel_work",
        "feeds": "OGI,Agent Registry,Corpus Callosum",
    },
    {
        "id": "egi",
        "name": "Evidence General Intelligence",
        "focus": "proof_provenance_confidence_and_contradictions",
        "feeds": "DGI,MGI,Judgement,HRM",
    },
    {
        "id": "lgi",
        "name": "Learning General Intelligence",
        "focus": "outcomes_lessons_and_durable_improvement",
        "feeds": "AdGI,MGI,HRM,Hippocampus",
    },
    {
        "id": "tegi",
        "name": "Temporal General Intelligence",
        "focus": "timing_sequence_deadlines_and_change",
        "feeds": "SGI,TGI,PGI,AdGI",
    },
    {
        "id": "regi",
        "name": "Resource General Intelligence",
        "focus": "capacity_compute_people_money_energy_and_tools",
        "feeds": "SGI,OGI,RGI",
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
    """Build the eight-stage bounded command review beneath AGI routing."""

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
        domain_text = (
            ", ".join(domains) if domains else "approved specialist intelligence"
        )
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
                    "Choose the smallest useful next step that produces proof, keeps "
                    "rollback possible and does not cross the Human Authority boundary."
                ),
            },
            {
                "id": "ogi",
                "name": "Operational General Intelligence",
                "focus": "dependencies_and_readiness",
                "advice": (
                    "Check identity, permissions, data provenance, service health, "
                    "monitoring, capacity, audit and rollback readiness before treating "
                    "the step as operational."
                ),
            },
            {
                "id": "dgi",
                "name": "Diagnostic General Intelligence",
                "focus": "cause_and_gap_isolation",
                "triggered": diagnostic_triggered,
                "advice": (
                    "Isolate the failing or uncertain boundary using observed evidence "
                    "before retrying, repairing or changing dependencies."
                    if diagnostic_triggered
                    else "Investigate only observed failures, gaps or contradictions."
                ),
            },
            {
                "id": "pgi",
                "name": "Predictive General Intelligence",
                "focus": "bounded_forecast",
                "advice": (
                    "Forecast consequences as scenarios, never facts; attach confidence "
                    "and identify evidence that would confirm or falsify the forecast."
                ),
                "prediction_is_fact": False,
            },
            {
                "id": "rgi",
                "name": "Resilience General Intelligence",
                "focus": "continuity_and_recovery",
                "advice": (
                    "Preserve a fail-closed path, rollback or safe degraded mode so one "
                    "failed dependency cannot force unsafe continuation."
                ),
            },
            {
                "id": "adgi",
                "name": "Adaptive General Intelligence",
                "focus": "evidence_driven_replanning",
                "advice": (
                    "If material evidence changes, compare the active plan with the new "
                    "conditions and propose a bounded re-route; never silently mutate an "
                    "approved consequential action."
                ),
            },
            {
                "id": "mgi",
                "name": "Meta General Intelligence",
                "focus": "reasoning_quality_and_calibration",
                "advice": (
                    "Challenge framing, assumptions, confidence, blind spots and internal "
                    "contradictions before progression to War Room and Judgement."
                ),
                "decision_authority": False,
            },
        )

        support = tuple(
            {
                **item,
                "advisory_only": True,
                "decision_authority": False,
                "execution_authority": False,
            }
            for item in SUPPORTING_INTELLIGENCE
        )

        return {
            "component": self.component,
            "task_type": task,
            "core_path": ("agi", *(stage["id"] for stage in stages)),
            "command_path": tuple(stage["id"] for stage in stages),
            "stages": stages,
            "supporting_intelligence": support,
            "supporting_ids": tuple(item["id"] for item in support),
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
        command_path = tuple(item["id"] for item in COMMAND_STAGES)
        support_ids = tuple(item["id"] for item in SUPPORTING_INTELLIGENCE)
        return {
            "component": self.component,
            "ready": True,
            "kind": "bounded_general_intelligence_command_and_support_layer",
            "brain_count": 0,
            "stage_count": len(COMMAND_STAGES),
            "stages": COMMAND_STAGES,
            "command_path": command_path,
            "core_path": ("agi", *command_path),
            "core_general_intelligence_count": 1 + len(COMMAND_STAGES),
            "supporting_intelligence": SUPPORTING_INTELLIGENCE,
            "supporting_ids": support_ids,
            "supporting_count": len(SUPPORTING_INTELLIGENCE),
            "total_general_intelligence_capabilities": (
                1 + len(COMMAND_STAGES) + len(SUPPORTING_INTELLIGENCE)
            ),
            "independent_execute": False,
            "independent_approval": False,
            "prediction_claims_fact": False,
            "fail_closed_resilience": True,
            "adaptive_mutates_approved_action": False,
            "meta_decision_authority": False,
            "human_authority_final": True,
            "truth_boundary": (
                "General-intelligence capabilities remain advisory inside the single SMI "
                "brain. They do not prove achieved AGI, autonomous authority or a second "
                "brain. War Room, Judgement, Guardian/Aegis and Human Authority retain "
                "their existing boundaries."
            ),
        }
