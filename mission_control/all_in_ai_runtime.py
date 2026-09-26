"""Founder-facing Mission Keeper adapter over the existing single SMI brain.

This module does not create another brain and grants no execution or approval
authority. It reuses the existing AGI routing and General Intelligence command
layers, then projects a Truth Mode / Red Team mission plan for Founder review.
"""

from __future__ import annotations

from typing import Any

from oap.smi.agi_core import AGICore
from oap.smi.command_intelligence import CommandIntelligence

from . import all_in_ai

_MAX_MISSION_LENGTH = 4000
_ALLOWED_RESEARCH_MODES = {"standard", "alien_research"}


def _clean_mission(value: object) -> str:
    mission = str(value or "").strip()
    if not mission:
        raise ValueError("mission_required")
    if len(mission) > _MAX_MISSION_LENGTH:
        raise ValueError("mission_too_long")
    return mission


def _clean_task_type(value: object) -> str:
    task_type = str(value or "GENERAL").strip().upper() or "GENERAL"
    return task_type[:64]


def _clean_research_mode(value: object) -> str:
    mode = str(value or "standard").strip().casefold() or "standard"
    if mode not in _ALLOWED_RESEARCH_MODES:
        raise ValueError("unsupported_research_mode")
    return mode


def plan_mission(
    mission: object,
    *,
    task_type: object = "GENERAL",
    high_impact: bool = False,
    research_mode: object = "standard",
) -> dict[str, Any]:
    """Route one Founder mission through existing SMI intelligence capabilities."""

    clean_mission = _clean_mission(mission)
    clean_task_type = _clean_task_type(task_type)
    clean_research_mode = _clean_research_mode(research_mode)

    agi = AGICore()
    command = CommandIntelligence()
    route = agi.route(clean_mission, clean_task_type)
    review = command.review(
        clean_mission,
        clean_task_type,
        route,
        high_impact=bool(high_impact),
    )
    agi_status = agi.status()

    alien_research = {
        "active": clean_research_mode == "alien_research",
        "purpose": (
            "Explore unconventional hypotheses and architectures while keeping "
            "speculation separate from verified fact."
        ),
        "claims_fact_without_evidence": False,
        "requires_truth_mode_evidence": True,
        "execution_authority": False,
    }

    red_team = {
        "challenge_assumptions": True,
        "diagnostic_review_present": "dgi" in review["command_path"],
        "resilience_review_present": "rgi" in review["command_path"],
        "meta_review_present": "mgi" in review["command_path"],
        "prediction_claims_fact": False,
        "fail_closed_without_evidence": True,
        "war_room_next": bool(review["war_room_next"]),
        "judgement_next": bool(review["judgement_next"]),
    }

    return {
        "component": "ALL IN A.I. Mission Keeper Runtime",
        "identity": all_in_ai.IDENTITY,
        "mission": {
            "task_type": clean_task_type,
            "high_impact": bool(high_impact),
            "research_mode": clean_research_mode,
            "length": len(clean_mission),
        },
        "smi_binding": {
            "brain_count_added": 0,
            "single_smi_brain_preserved": True,
            "agi_route": route,
            "command_review": review,
            "agi_achieved": bool(agi_status["agi_achieved"]),
            "general_intelligence_certified": bool(
                agi_status["general_intelligence_certified"]
            ),
        },
        "alien_research": alien_research,
        "red_team": red_team,
        "truth_mode": {
            "status": "planned_not_executed",
            "evidence_required_before_green": True,
            "simulation_is_live_proof": False,
            "execution_granted": False,
            "approval_granted": False,
        },
        "authority": {
            "independent_execute": False,
            "independent_approval": False,
            "financial_execution_autonomous": False,
            "founder_final": True,
            "human_authority_final": True,
        },
        "next_boundary": (
            "Founder-authorised execution must pass the existing governed SMI, "
            "Guardian/Aegis, Judgement, audit and recovery gates."
        ),
    }


def status() -> dict[str, Any]:
    """Return static runtime truth for the Founder-facing adapter."""

    agi = AGICore().status()
    command = CommandIntelligence().status()
    return {
        "component": "ALL IN A.I. Mission Keeper Runtime",
        "ready": bool(agi["ready"] and command["ready"]),
        "brain_count_added": 0,
        "single_smi_brain_preserved": True,
        "agi_core_ready": bool(agi["ready"]),
        "agi_achieved": bool(agi["agi_achieved"]),
        "general_intelligence_certified": bool(
            agi["general_intelligence_certified"]
        ),
        "general_intelligence_capabilities": int(
            command["total_general_intelligence_capabilities"]
        ),
        "research_modes": tuple(sorted(_ALLOWED_RESEARCH_MODES)),
        "independent_execute": False,
        "independent_approval": False,
        "human_authority_final": True,
    }
