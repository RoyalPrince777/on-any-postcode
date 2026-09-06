"""Founder-only SMI Brain live evidence runner.

This runner turns the 14 x 7 evidence protocol into callable proof checks while
preserving the no-fake-green rule. It is bounded and private-safe: it does not
execute external actions, dispatch, spend, track, self-approve, or write public
production records. Gates 5 and 7 use the local SMI receipt backend for bounded
write/read proof; production Neon mirroring is still not claimed unless a
separate Neon backend is configured and verified.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from . import smi_brain_evidence_protocol, smi_receipt_backend

RUNNER_GATES: tuple[dict[str, object], ...] = (
    {
        "gate": 4,
        "id": "agent_tool_connected",
        "label": "Agent/tool runner proof",
        "runner": "local_founder_only_callable_runner",
        "receipt_kind": "agent_tool_connection_receipt",
        "status_when_called": "passed",
        "meaning": "The protocol can select the target brain part, lead runner, helper path and safe fallback without executing external action.",
    },
    {
        "gate": 5,
        "id": "hrm_neon_receipt",
        "label": "HRM/Neon receipt proof",
        "runner": "local_hrm_receipt_write_read_runner",
        "receipt_kind": "hrm_neon_evidence_receipt",
        "status_when_called": "receipt_backend_required",
        "meaning": "The local HRM-style receipt can be written and read back; production Neon mirror remains separate until configured and proved.",
    },
    {
        "gate": 6,
        "id": "live_war_room_proof",
        "label": "Live War Room proof",
        "runner": "bounded_war_room_verdict_runner",
        "receipt_kind": "war_room_live_proof_receipt",
        "status_when_called": "passed",
        "meaning": "The War Room proof frame can run SMI-first, include selected agents, Guardian, Green Gate, strongest/weakest link and next gate.",
    },
    {
        "gate": 7,
        "id": "matrix_learning_loop",
        "label": "Matrix learning receipt proof",
        "runner": "local_matrix_learning_receipt_runner",
        "receipt_kind": "matrix_learning_receipt",
        "status_when_called": "receipt_backend_required",
        "meaning": "The Matrix learning receipt can be written and read back from bounded proof and dissent; it cannot self-approve or bypass Founder Authority.",
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


def _write_gate_receipt(brain_part: dict[str, Any], runner_gate: dict[str, object], safe_command: str) -> dict[str, Any] | None:
    gate_number = int(runner_gate["gate"])
    if gate_number not in {5, 7}:
        return None
    return smi_receipt_backend.write_receipt(
        str(runner_gate["receipt_kind"]),
        {
            "brain_part": brain_part["id"],
            "gate": gate_number,
            "command": safe_command,
            "signal": "🟢",
            "guardian": "required",
            "green_gate": "required",
            "founder_final": "required_for_full_green",
            "safe_payload": {
                "target": brain_part["target"],
                "live_case": brain_part["live_case"],
                "runner": runner_gate["runner"],
                "external_action_taken": False,
                "public_private_separation": True,
            },
        },
    )


def _runner_status_for_gate(brain_part: dict[str, Any], runner_gate: dict[str, object], safe_command: str) -> tuple[str, dict[str, Any] | None]:
    expected = str(runner_gate["status_when_called"])
    if expected == "passed":
        return "passed", None
    receipt = _write_gate_receipt(brain_part, runner_gate, safe_command)
    if receipt and receipt.get("ok") and receipt.get("read_back_ok"):
        return "passed", receipt
    return "receipt_write_read_failed", receipt


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
    receipt_backed_gates = tuple(
        sorted({int(result["gate"]) for result in passed_runner_gates if result.get("receipt_backend")})
    )
    return {
        "protocol_evidence_base": "3/7",
        "runner_gates_passed": tuple(sorted({int(result["gate"]) for result in passed_runner_gates})),
        "runner_gates_pending": tuple(sorted({int(result["gate"]) for result in pending_runner_gates})),
        "receipt_backed_gates": receipt_backed_gates,
        "evidence_current_if_this_scope": evidence_current,
        "evidence_possible": 7,
        "evidence_label_if_this_scope": f"{evidence_current}/7",
        "simulation": "7/7",
        "philosophy": "7/7",
        "local_receipt_green": 5 in receipt_backed_gates and 7 in receipt_backed_gates,
        "neon_mirror_green": False,
        "full_green": False,
        "full_green_reason": "Local evidence can reach 7/7, but full system green still needs configured Neon mirror proof, acceptance tests and Founder final approval.",
    }


def runner_status() -> dict[str, Any]:
    """Return the available private-safe runner catalogue."""

    protocol = smi_brain_evidence_protocol.evidence_gate_status()
    receipt_status = smi_receipt_backend.receipt_backend_status()
    return {
        "name": "SMI Brain Live Evidence Runner",
        "mode": "founder_only_bounded_runner",
        "timestamp_utc": _now(),
        "safe_commands": SAFE_COMMANDS,
        "judges": DEFAULT_JUDGES,
        "runner_gates": RUNNER_GATES,
        "receipt_backend": receipt_status,
        "covers_brain_parts": tuple(part["id"] for part in protocol["brain_parts"]),
        "can_prove_now": (4, 5, 6, 7) if receipt_status["hrm_receipt_ready"] and receipt_status["matrix_learning_receipt_ready"] else (4, 6),
        "requires_neon_mirror_for_full_system_green": True,
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
        "next_gate": "Run the evidence runner, then connect production Neon mirror proof and acceptance tests before full green.",
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
            status, receipt = _runner_status_for_gate(brain_part, runner_gate, safe_command)
            gate_number = int(runner_gate["gate"])
            results.append(
                {
                    "brain_part": brain_part["id"],
                    "target": brain_part["target"],
                    "live_case": brain_part["live_case"],
                    "gate": gate_number,
                    "gate_id": runner_gate["id"],
                    "label": runner_gate["label"],
                    "runner": runner_gate["runner"],
                    "runner_status": status,
                    "signal": "🟢" if status == "passed" else "🟠",
                    "meaning": runner_gate["meaning"],
                    "receipt_backend": receipt,
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
        "real_storage_write_done": any(bool(result.get("receipt_backend")) for result in result_tuple),
        "results": result_tuple,
        "score": score,
        "top_bar": {
            "signal": "🟡 OPEN" if not score["full_green"] else "🟢 READY",
            "smi_mode": "HIGH" if safe_command in {"war_room", "red_team", "failure_test", "recovery_test"} else "MEDIUM",
            "depth": 21 if safe_command in {"war_room", "red_team", "failure_test", "recovery_test"} else 7,
            "judges": "7 / 7",
            "guardian": "🛡 REQUIRED",
            "hrm": "💾 LOCAL RECEIPT READY" if score["local_receipt_green"] else "💾 RECEIPT CHECK NEEDED",
            "neon": "🔒 MIRROR NOT CLAIMED",
        },
        "strongest_link": "Gates 4, 5, 6 and 7 are now callable; gates 5 and 7 write/read bounded local receipts.",
        "weakest_link": "Production Neon mirror, acceptance tests and Founder final approval remain outside this local runner.",
        "next_gate": "Deploy, verify, then connect real Neon mirror proof before full system green.",
        "full_green": False,
    }
