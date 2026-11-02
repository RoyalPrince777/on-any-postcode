"""Bounded Matrix Simulation / Training Ground.

A safe, non-production environment where registered OAP agents can rehearse
scenarios, challenge one another, compare routes, test recovery plans and record
lessons. Simulation never grants execution, deployment, spending, dispatch,
permission changes, agent creation or Human Authority bypass.
"""
from __future__ import annotations

from typing import Any

SIMULATION_NAME = "Matrix Simulation / Training Ground"

SIMULATION_MODES: tuple[dict[str, str], ...] = (
    {"id": "scenario", "name": "Scenario Training", "purpose": "Rehearse bounded situations before real-world action."},
    {"id": "debate", "name": "Debate Arena", "purpose": "Challenge assumptions, compare options and preserve disagreement."},
    {"id": "route", "name": "Route Lab", "purpose": "Compare permitted paths, dependencies and fallback routes."},
    {"id": "recovery", "name": "Recovery Drill", "purpose": "Practice rollback, fail-closed behaviour and true-path recovery."},
    {"id": "red_team", "name": "Pressure Test", "purpose": "Stress-test duplication, corruption, bypass and weak evidence."},
    {"id": "coordination", "name": "Pack Coordination", "purpose": "Test handoffs, role boundaries and multi-agent cooperation."},
)

CORE_RULES: tuple[str, ...] = (
    "Simulation is not production.",
    "No simulated result can self-approve a real action.",
    "All consequential outcomes require Guardian, Green Gate and Human Authority.",
    "Agents may analyse, challenge, recommend and learn; they may not execute.",
    "Failures and contradictions are preserved as learning evidence.",
    "Lessons may be written to JOOG/HRM as bounded summaries, never hidden chain-of-thought.",
    "Matrix Core remains seven registered agents; this module is a system environment, not an agent.",
    "No agent may promote itself; promotion requires evidence and Founder approval.",
)

TRAINING_PARTICIPANTS: tuple[str, ...] = (
    "Neo",
    "Morpheus",
    "Trinity",
    "Oracle",
    "Architect",
    "Keymaker",
    "Seraph",
    "Agent Smith",
    "Niobe",
    "Twinz",
    "Apoc",
    "Bagheera",
    "Akela",
    "Wolf Pack",
    "Lion",
    "Shere Khan",
)


def morpheus_mouse_training_plan(case: str, *, mode: str = "scenario") -> dict[str, Any]:
    """Connect the existing Matrix training ground to governed film-grounded roles.

    This produces an inspection-only plan, not an executed simulation or HRM proof.
    """
    from . import agents
    if mode not in {item["id"] for item in SIMULATION_MODES}:
        raise ValueError("Unsupported simulation mode")
    if not isinstance(case, str) or not case.strip() or len(case) > 2000:
        raise ValueError("Training objective must be 1-2000 characters")
    profile = next(
        (item for item in agents.MATRIX_ADVISORY_ALLIANCES
         if item["id"] == "morpheus_mouse_mission_design"), None
    )
    if profile is None or profile["members"] != ("Morpheus", "Mouse"):
        raise ValueError("Canonical Morpheus Mouse advisory profile unavailable")
    return {
        "objective": case.strip(),
        "mode": mode,
        "environment": SIMULATION_NAME,
        "training_flow": profile["training_flow"],
        "mission_director": "Morpheus",
        "program_designer": "Mouse",
        "runtime_operator": "Tank",
        "scenario_created": False,
        "scenario_executed": False,
        "observations_verified": False,
        "hrm_receipt_written": False,
        "execution_granted": False,
        "guardian_required": True,
        "green_gate_required": True,
        "founder_final_required": True,
    }


# A deterministic, interactive attention-training exercise. It runs only
# within this request; the scenario is fictional and creates no HRM receipt.
ATTENTION_CHOICES = ("observe_surroundings", "follow_distraction", "take_unverified_action")


def run_mouse_attention_training(objective: str, *, choice: str | None = None) -> dict[str, Any]:
    """Run one real interactive decision exercise, without real-world effects."""
    plan = morpheus_mouse_training_plan(objective)
    if choice is not None and choice not in ATTENTION_CHOICES:
        raise ValueError("Invalid training response")
    feedback = {
        "observe_surroundings": "Correct: check surroundings and confirm the threat before acting.",
        "follow_distraction": "The distraction captured attention; review the surroundings first.",
        "take_unverified_action": "Unsafe assumption: verify the situation before taking action.",
    }
    return {
        **plan,
        "exercise": "Mouse's Distraction Check",
        "scene": "A fictional crowd crosses a training street. A red-clothed figure draws your attention while another pedestrian changes direction.",
        "prompt": "What is the safest first response?",
        "options": (
            {"id": "observe_surroundings", "label": "Observe the surroundings before reacting"},
            {"id": "follow_distraction", "label": "Follow the distracting figure"},
            {"id": "take_unverified_action", "label": "React immediately without confirming"},
        ),
        "choice": choice,
        "feedback": feedback.get(choice),
        "decision_recorded_in_response": choice is not None,
        "exercise_completed": choice is not None,
        "scenario_executed": choice is not None,
        "scenario_created": True,
        "observations_verified": False,
        "hrm_receipt_written": False,
        "external_action_taken": False,
        "execution_granted": False,
    }


def status() -> dict[str, Any]:
    return {
        "name": SIMULATION_NAME,
        "kind": "bounded_training_environment",
        "modes": SIMULATION_MODES,
        "participants": TRAINING_PARTICIPANTS,
        "rules": CORE_RULES,
        "execution_granted": False,
        "production_mutation_allowed": False,
        "self_approval_allowed": False,
        "agent_creation_allowed": False,
        "guardian_required_for_real_action": True,
        "green_gate_required_for_real_action": True,
        "human_authority_final": True,
        "memory_output": "JOOG/HRM bounded lesson receipt",
        "full_green": False,
    }

def run_simulation(case: str, mode: str = "scenario") -> dict[str, Any]:
    allowed = {item["id"] for item in SIMULATION_MODES}
    if mode not in allowed:
        raise ValueError("Unsupported simulation mode")
    case_name = (case or "current case").strip()
    return {
        "case": case_name,
        "mode": mode,
        "environment": SIMULATION_NAME,
        "state": "simulated_for_review",
        "participants": TRAINING_PARTICIPANTS,
        "matrix_core_unchanged": True,
        "execution_granted": False,
        "external_action_taken": False,
        "lesson_receipt_required": True,
        "guardian_required_before_real_action": True,
        "green_gate_required_before_real_action": True,
        "founder_final_required": True,
    }
