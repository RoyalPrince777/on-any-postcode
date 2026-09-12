"""Canonical seven-judge War Room review for Sovereign Megaverse Intelligence.

The seven judges are review lenses, not autonomous execution authorities. Every
review is bounded, Founder-only through its caller, and records a local receipt
without claiming production Neon proof. Guardian and Green Gate remain separate
from the seven judge seats. Neo remains the recovery witness.
"""
from __future__ import annotations

from typing import Any

from . import smi_brain_protocol, smi_receipt_backend

CANONICAL_JUDGES: tuple[dict[str, str], ...] = tuple(
    dict(judge) for judge in smi_brain_protocol.WAR_ROOM_JUDGES
)
CANONICAL_JUDGE_NAMES: tuple[str, ...] = tuple(
    judge["name"] for judge in CANONICAL_JUDGES
)
ROTATING_JUDGES: tuple[str, ...] = ("Morpheus", "Akela", "Owl")
SEPARATE_GATES: tuple[str, ...] = ("Guardian", "Green Gate")
RECOVERY_WITNESS = "Neo"
FIRST_REVIEWER = "SMI First Look"
FINAL_REVIEWER = "Final SMI Review"
FOUNDER_AUTHORITY = "Founder Authority"


def _rotation_index(scope: str, command: str) -> int:
    """Choose a deterministic rotation focus without randomness or hidden state."""

    token = f"{scope.strip().lower()}|{command.strip().lower()}"
    return sum(ord(character) for character in token) % len(ROTATING_JUDGES)


def rotation_plan(scope: str = "all", command: str = "war_room") -> dict[str, Any]:
    """Return the canonical seven-seat review order and current rotation focus."""

    focus_index = _rotation_index(scope, command)
    focus = ROTATING_JUDGES[focus_index]
    rotating_order = ROTATING_JUDGES[focus_index:] + ROTATING_JUDGES[:focus_index]
    fixed_order = ("Shere Khan", "Bagheera", "Agent Smith", "Lion")
    review_order = fixed_order + rotating_order
    return {
        "canonical_count": len(CANONICAL_JUDGE_NAMES),
        "canonical_judges": CANONICAL_JUDGE_NAMES,
        "review_order": review_order,
        "rotation_pool": ROTATING_JUDGES,
        "rotation_focus": focus,
        "separate_gates": SEPARATE_GATES,
        "recovery_witness": RECOVERY_WITNESS,
        "first_reviewer": FIRST_REVIEWER,
        "final_reviewer": FINAL_REVIEWER,
        "founder_authority": FOUNDER_AUTHORITY,
        "all_judges_present": set(review_order) == set(CANONICAL_JUDGE_NAMES),
    }


def _judge_verdicts(
    *,
    evidence_current: int,
    local_receipt_green: bool,
    neon_mirror_green: bool,
) -> tuple[dict[str, str], ...]:
    """Run transparent rule lenses for all seven judges.

    These are inspectable rule checks, not claims that seven independent models
    spoke or acted. They exist to stop the UI from calling a partial review 7/7.
    """

    verdicts: list[dict[str, str]] = []
    for judge in CANONICAL_JUDGES:
        name = judge["name"]
        verdict = "PASS_LOCAL"
        reason = "Canonical review lens completed within the bounded War Room."

        if name == "Shere Khan" and evidence_current < 7:
            verdict = "HOLD"
            reason = "Pressure review holds full green while evidence is below 7/7."
        elif name == "Bagheera" and not local_receipt_green:
            verdict = "HOLD"
            reason = "Protection review requires a readable local review receipt."
        elif name == "Agent Smith" and len(set(CANONICAL_JUDGE_NAMES)) != 7:
            verdict = "BLOCK"
            reason = "Integrity review found duplicate or missing canonical judge seats."
        elif name == "Lion" and not neon_mirror_green:
            verdict = "HOLD"
            reason = "CEO readiness cannot certify full green without Neon mirror proof."
        elif name == "Morpheus" and evidence_current < 7:
            verdict = "HOLD"
            reason = "Truth review rejects a false-green claim while evidence is incomplete."
        elif name == "Akela" and len(CANONICAL_JUDGE_NAMES) != 7:
            verdict = "BLOCK"
            reason = "Order review requires the complete seven-seat chain."
        elif name == "Owl" and not local_receipt_green:
            verdict = "HOLD"
            reason = "Memory/law review requires a persisted and readable local receipt."

        verdicts.append(
            {
                "judge": name,
                "presence": judge["presence"],
                "role": judge["role"],
                "checks": judge["checks"],
                "mode": "bounded_rule_lens",
                "verdict": verdict,
                "reason": reason,
            }
        )
    return tuple(verdicts)


def run_review(
    *,
    scope: str = "all",
    command: str = "war_room",
    evidence_current: int = 3,
    local_receipt_green: bool = False,
    neon_mirror_green: bool = False,
) -> dict[str, Any]:
    """Run all seven canonical review lenses and write one local review receipt."""

    plan = rotation_plan(scope, command)
    verdicts = _judge_verdicts(
        evidence_current=evidence_current,
        local_receipt_green=local_receipt_green,
        neon_mirror_green=neon_mirror_green,
    )
    reviewed_names = tuple(result["judge"] for result in verdicts)
    all_reviewed = set(reviewed_names) == set(CANONICAL_JUDGE_NAMES)
    holds = tuple(
        result["judge"] for result in verdicts if result["verdict"] in {"HOLD", "BLOCK"}
    )

    receipt = smi_receipt_backend.write_receipt(
        "war_room_live_proof_receipt",
        {
            "brain_part": scope,
            "gate": 6,
            "command": command,
            "signal": "🟡" if holds else "🟢",
            "guardian": "required_separate_gate",
            "green_gate": "required_separate_gate",
            "founder_final": "required_for_full_green",
            "safe_payload": {
                "review_mode": "canonical_seven_bounded_rule_lenses",
                "canonical_judges": CANONICAL_JUDGE_NAMES,
                "review_order": plan["review_order"],
                "rotation_focus": plan["rotation_focus"],
                "reviewed_judges": reviewed_names,
                "holds": holds,
                "neo_role": RECOVERY_WITNESS,
                "guardian_and_green_gate_are_judges": False,
                "external_action_taken": False,
                "neon_mirror_claimed": False,
            },
        },
    )
    receipt_ok = bool(receipt.get("ok") and receipt.get("read_back_ok"))
    review_complete = bool(all_reviewed and receipt_ok)

    return {
        "mode": "canonical_seven_bounded_rule_lenses",
        "scope": scope,
        "command": command,
        "canonical_count": 7,
        "reviewed_count": len(set(reviewed_names)),
        "canonical_judges": CANONICAL_JUDGE_NAMES,
        "review_order": plan["review_order"],
        "rotation_pool": ROTATING_JUDGES,
        "rotation_focus": plan["rotation_focus"],
        "judge_results": verdicts,
        "holds": holds,
        "separate_gates": SEPARATE_GATES,
        "recovery_witness": RECOVERY_WITNESS,
        "receipt": receipt,
        "receipt_ok": receipt_ok,
        "review_complete_local": review_complete,
        "neon_mirror_green": bool(neon_mirror_green),
        "founder_final_required": True,
        "full_green": False,
        "truth_boundary": (
            "7/7 means all seven canonical rule lenses ran locally and were receipted; "
            "it does not mean production Neon proof or Founder approval exists."
        ),
    }


def status() -> dict[str, Any]:
    """Return a no-write status projection for the judge system."""

    plan = rotation_plan()
    return {
        "name": "Canonical Seven Judge Rotation",
        "canonical_count": 7,
        "canonical_judges": CANONICAL_JUDGE_NAMES,
        "rotation_pool": ROTATING_JUDGES,
        "rotation_focus": plan["rotation_focus"],
        "separate_gates": SEPARATE_GATES,
        "recovery_witness": RECOVERY_WITNESS,
        "all_judges_present": plan["all_judges_present"],
        "review_receipt_required": True,
        "neon_mirror_required_for_full_green": True,
        "founder_final_required": True,
        "full_green": False,
    }
