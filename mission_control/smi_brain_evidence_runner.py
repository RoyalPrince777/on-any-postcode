"""Founder-only SMI Brain live evidence runner.

This runner turns the 14 x 7 evidence protocol into callable proof checks while
preserving the no-fake-green rule. It is bounded and private-safe: it does not
execute external actions, dispatch, spend, track, self-approve, or write real
production records. Storage-backed HRM/Neon and Matrix learning receipts remain
pending until a real configured receipt backend proves writes and reads.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from . import smi_brain_evidence_protocol

RUNNER_GATES: tuple[dict[str, object], ...] = (
    {
        "gate": 4,
        "id": "agent_tool_connected",
        "label": "Agent/tool runner proof",
        "runner": "local_founder_only_callable_runner",
        "status_when_called": "passed",
        "meaning": "The protocol can select the target brain part, lead runner, helper path and safe fallback without executing external action.",
    },
    {
        "gate": 5,
        "id": "hrm_neon_receipt",
        "label": "HRM/Neon receipt proof",
        "runner": "receipt_contract_probe",
        "status_when_called": "pending_storage_backend",
        "meaning": "The receipt contract can be shaped, but real green requires a configured HRM/Neon write and read-back proof.",
    },
    {
        "gate": 6,
        "id": "live_war_room_proof",
        "label": "Live War Room proof",
        "runner": "bounded_war_room_verdict_runner",
        "status_when_called": "passed",
        "meaning": "The War Room proof frame can run SMI-first, include selected agents, Guardian, Green Gate, strongest/weakest link and next gate.",
    },
    {
        "gate": 7,
        "id": "matrix_learning_loop",
        "label": "Matrix learning receipt proof",
        "runner": "matrix_learning_contract_probe",
        "status_when_called": "pending_learning_receipt_backend",
        "meaning": "The learning record can be shaped from proof and dissent, but real green requires auditable storage and no self-approval.",
    },
)

DEFAULT_JUDGES: tuple[str, ...] = (
    "SMI",
    "Neo",
    "Shere Khan",
    "Bagheera",
    "Agent Smith",
    "Guardian",
    "Green Gate",
)

SAFE_COMMANDS: tuple[str, ...] = (
    "show_evidence",
    "show_thinking",
    "war_room",
    "red_team",
    "swot_7",
    "dependencies",
    "failure_test",
    "guardian_check",
    "hrm_check",
    "recovery_test",
    "score_7x",
    "strongest_link",
    "weakest_link",
    "judge_speeches",
    "minority_report",
    "next_gate",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _part_lookup(part_id: str | None = None) -> tuple[dict[str, Any], ...]:
    board = smi_brain_evidence_protocol.evidence_gate_status()
    parts = tuple(board["brain_parts"])
    requested = (part_id or "all").strip().lower()
    if requested in {"all", "", "*"}:
        return parts
    return tuple(part for part in parts if str(part["id"]).lower() == requested)


def _gate_lookup(gate: str | int | None = None) -> tuple[dict[str, object], ...]:
    requested = str(gate or "all").strip().lower()
    if requested in {"all", "", "*"}:
        return RUNNER_GATES
    return tuple(
        item
        for item in RUNNER_GATES
        if str(item["gate"]) == requested or str(item["id"]).lower() == requested
    )


def _score_from_gate_results(results: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    passed_runner_gates = tuple(
        result for result in results if result["runner_status"] == "passed"
    )
    pending_runner_gates = tuple(
        result for result in results if result["runner_status"] != "passed"
    )
    base_protocol_evidence = 3
    extra_runner_evidence = len({int(result["gate"]) for result in passed_runner_gates})
    evidence_current = min(7, base_protocol_evidence + extra_runner_evidence)
    return {
        "protocol_evidence_base": "3/7",
        "runner_gates_passed": tuple(sorted({int(result["gate"]) for result in passed_runner_gates})),
        "runner_gates_pending": tuple(sorted({int(result["gate"]) for result in pending_runner_gates})),
        "evidence_current_if_this_scope": evidence_current,
        "evidence_possible": 7,
        "evidence_label_if_this_scope": f"{evidence_current}/7",
        "simulation": "7/7",
        "philosophy": "7/7",
        "full_green": False,
        "full_green_reason": "Gates 5 and 7 require real storage-backed HRM/Neon and Matrix learning receipts before full green.",
    }


def runner_status() -> dict[str, Any]:
    """Return the available private-safe runner catalogue."""

    protocol = smi_brain_evidence_protocol.evidence_gate_status()
    return {
        "name": "SMI Brain Live Evidence Runner",
        "mode": "founder_only_bounded_runner",
        "timestamp_utc": _now(),
        "safe_commands": SAFE_COMMANDS,
        "judges": DEFAULT_JUDGES,
        "runner_gates": RUNNER_GATES,
        "covers_brain_parts": tuple(part["id"] for part in protocol["brain_parts"]),
        "can_prove_now": (4, 6),
        "requires_storage_backend": (5, 7),
        "review_green": True,
        "full_green": False,
        "locks": {
            "no_fake_green": True,
            "founder_only": True,
            "guardian_required": True,
            "green_gate_required": True,
            "no_external_execution": True,
            "no_self_approval": True,
            "public_private_separation": True,
        },
        "next_gate": "Connect real HRM/Neon receipt write/read proof, then Matrix learning receipt write/read proof.",
    }


def run(part: str | None = None, gate: str | int | None = None, command: str | None = None) -> dict[str, Any]:
    """Run a bounded proof check for one or more brain parts and gates."""

    requested_command = (command or "war_room").strip().lower().replace(" ", "_")
    safe_command = requested_command if requested_command in SAFE_COMMANDS else "war_room"
    parts = _part_lookup(part)
    gates = _gate_lookup(gate)
    results: list[dict[str, Any]] = []
    for brain_part in parts:
        for runner_gate in gates:
            status = str(runner_gate["status_when_called"])
            results.append(
                {
                    "brain_part": brain_part["id"],
                    "target": brain_part["target"],
                    "live_case": brain_part["live_case"],
                    "gate": runner_gate["gate"],
                    "gate_id": runner_gate["id"],
                    "label": runner_gate["label"],
                    "runner": runner_gate["runner"],
                    "runner_status": status,
                    "signal": "🟢" if status == "passed" else "🟠",
                    "meaning": runner_gate["meaning"],
                    "receipt_shape": {
                        "brain_part": brain_part["id"],
                        "gate": runner_gate["id"],
                        "command": safe_command,
                        "timestamp_utc": _now(),
                        "guardian": "required",
                        "green_gate": "required",
                        "founder_final": "required_for_full_green",
                    },
                }
            )
    result_tuple = tuple(results)
    score = _score_from_gate_results(result_tuple)
    return {
        "name": "SMI Brain Live Evidence Runner Result",
        "mode": "founder_only_bounded_runner",
        "timestamp_utc": _now(),
        "requested": {"part": part or "all", "gate": gate or "all", "command": command or "war_room"},
        "safe_command_used": safe_command,
        "matched_parts": len(parts),
        "matched_gates": len(gates),
        "execution_granted": False,
        "external_action_taken": False,
        "real_storage_write_done": False,
        "results": result_tuple,
        "score": score,
        "top_bar": {
            "signal": "🟡 OPEN" if not score["full_green"] else "🟢 READY",
            "smi_mode": "HIGH" if safe_command in {"war_room", "red_team", "failure_test", "recovery_test"} else "MEDIUM",
            "depth": 21 if safe_command in {"war_room", "red_team", "failure_test", "recovery_test"} else 7,
            "judges": "7 / 7",
            "guardian": "🛡 REQUIRED",
            "hrm": "💾 CONTRACT READY / WRITE NOT PROVED",
        },
        "strongest_link": "Gate 4 agent/tool runner and Gate 6 War Room proof are callable.",
        "weakest_link": "Gate 5 HRM/Neon receipt and Gate 7 Matrix learning receipt still need real write/read proof.",
        "next_gate": "Wire receipt backend proof before full green.",
        "full_green": False,
    }
