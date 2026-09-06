"""Founder-only SMI Brain 14 x 7 evidence completion protocol.

This module completes the protocol contract for turning the SMI Brain from
3/7 evidence to 7/7 evidence per brain part. It is still read-only: it does not
execute, deploy, approve, dispatch, track, spend, or write production records.

Full real green is only allowed when every evidence gate has live proof,
HRM/Neon receipts, acceptance tests, Matrix learning receipts, Guardian pass,
Green Gate pass, and Founder Authority.
"""
from __future__ import annotations

from typing import Any

EVIDENCE_7_GATES: tuple[dict[str, object], ...] = (
    {
        "id": "named",
        "position": 1,
        "label": "Named",
        "current_status": "passed",
        "required_proof": "Canonical brain-part name exists and is stable.",
        "receipt": "protocol_name_lock",
        "green_rule": "Name cannot be blank, duplicated, or renamed without Founder review.",
    },
    {
        "id": "role_defined",
        "position": 2,
        "label": "Role defined",
        "current_status": "passed",
        "required_proof": "The brain part has one clear role inside SMI.",
        "receipt": "protocol_role_lock",
        "green_rule": "Role must not replace Founder, Guardian, Green Gate, HRM, Nexus, or War Room.",
    },
    {
        "id": "protocol_mapped",
        "position": 3,
        "label": "Protocol mapped",
        "current_status": "passed",
        "required_proof": "The brain part is mapped to Mind/Body/Soul, 21 Laws, 21 Signals, and safety boundaries.",
        "receipt": "protocol_map_lock",
        "green_rule": "Protocol mapping must show when to use 7, 14, or 21 stages.",
    },
    {
        "id": "agent_tool_connected",
        "position": 4,
        "label": "Agent/tool connected",
        "current_status": "protocol_ready",
        "required_proof": "Lead agent, helper agents, allowed tools, forbidden tools, and fallback path are declared.",
        "receipt": "agent_tool_connection_receipt",
        "green_rule": "Connection is not real green until one safe live runner proves the path without bypass.",
    },
    {
        "id": "hrm_neon_receipt",
        "position": 5,
        "label": "HRM/Neon receipt connected",
        "current_status": "protocol_ready",
        "required_proof": "The evidence result can be written to HRM and mirrored to Neon without leaking private data.",
        "receipt": "hrm_neon_evidence_receipt",
        "green_rule": "No receipt means no full green; failed receipt means hold or orange block.",
    },
    {
        "id": "live_war_room_proof",
        "position": 6,
        "label": "Live runner + War Room proof",
        "current_status": "protocol_ready",
        "required_proof": "War Room can run the case with SMI, selected agents, judges, Guardian, Green Gate, and output a verdict.",
        "receipt": "war_room_live_proof_receipt",
        "green_rule": "Simulation green is not enough; live proof must be timestamped and reversible.",
    },
    {
        "id": "matrix_learning_loop",
        "position": 7,
        "label": "Matrix learning loop",
        "current_status": "protocol_ready",
        "required_proof": "The result feeds a safe learning record from proof, blocks, failures, and Founder decisions.",
        "receipt": "matrix_learning_receipt",
        "green_rule": "Learning must be auditable, bounded, reversible, and unable to self-approve.",
    },
)

BRAIN_14_EVIDENCE_TARGETS: tuple[dict[str, str], ...] = (
    {"id": "left_hemisphere", "target": "logic/code proof runner", "live_case": "one safe code/proof check with HRM receipt"},
    {"id": "right_hemisphere", "target": "vision/culture/pattern runner", "live_case": "one OAP language, culture, or design meaning check"},
    {"id": "frontal_lobe", "target": "planning/next-action runner", "live_case": "one safe decision between answer, check, simulate, patch, deploy, recover, or stop"},
    {"id": "parietal_lobe", "target": "map/place hierarchy runner", "live_case": "one postcode-borough-county-country-continent check"},
    {"id": "temporal_lobe", "target": "language/Link intent runner", "live_case": "one Link/OAP vocabulary correction and receipt"},
    {"id": "occipital_lobe", "target": "UI/visual surface checker", "live_case": "one private/public UI boundary check"},
    {"id": "prefrontal_cortex", "target": "judgement depth runner", "live_case": "one 7 vs 14 vs 21 risk-depth decision"},
    {"id": "corpus_callosum", "target": "left-right coherence runner", "live_case": "one proof-vs-vision merge with debate and better option"},
    {"id": "thalamus", "target": "signal router runner", "live_case": "one signal-to-agent route using Agent Cone or Founder selection"},
    {"id": "hypothalamus", "target": "stability/recovery runner", "live_case": "one 97 recovery / offline / continue decision"},
    {"id": "hippocampus", "target": "HRM/Neon receipt runner", "live_case": "one stored receipt lookup with private boundary"},
    {"id": "amygdala", "target": "risk/fake-green alarm runner", "live_case": "one fake-green or bypass block"},
    {"id": "cerebellum", "target": "coordination/handoff runner", "live_case": "one tool/deploy/handoff proof chain"},
    {"id": "brainstem", "target": "health/fail-closed runner", "live_case": "one health/fail-closed proof check"},
)

PROTOCOL_BUTTONS: tuple[dict[str, str], ...] = (
    {"button": "🧠", "name": "SMI First Look", "does": "classify the case and pick 7, 14, or 21 depth"},
    {"button": "🔺", "name": "Agent Cone", "does": "bring closest lead/support/judge/risk agents forward"},
    {"button": "🎛️", "name": "Founder Select Agents", "does": "let Founder choose which agents enter review"},
    {"button": "✍️", "name": "Rewrite / Sharpen", "does": "restart from beginning or sharpen only the weak part"},
    {"button": "⚖️", "name": "Judge Review", "does": "run SMI, Neo, Shere Khan, Bagheera, Agent Smith, Guardian, Green Gate"},
    {"button": "🟢", "name": "Pass Review", "does": "keep review green only, not full green"},
    {"button": "🟡", "name": "Hold / Sharpen", "does": "keep useful item but fix boundary or wording"},
    {"button": "🟠", "name": "Orange Block", "does": "pause controlled risk until proof improves"},
    {"button": "🔴", "name": "Red Block", "does": "remove, reject, or quarantine unsafe/bypassing item"},
    {"button": "🔒", "name": "Full Green Lock", "does": "block fake full-green until all proof exists"},
    {"button": "👑", "name": "Founder Final", "does": "Founder decides final approval, hold, remove, rename, or send back"},
)

EVIDENCE_DECISION_STATES: tuple[dict[str, str], ...] = (
    {"state": "pass_review", "signal": "🟢", "meaning": "protocol/review is clean enough to continue"},
    {"state": "hold_sharpen", "signal": "🟡", "meaning": "useful but needs sharper boundary, role, wording, or selected agents"},
    {"state": "orange_block", "signal": "🟠", "meaning": "controlled pause because proof, runner, receipt, or duplicate risk is not ready"},
    {"state": "red_block", "signal": "🔴", "meaning": "unsafe, authority-breaking, privacy-breaking, or duplicate beyond repair"},
    {"state": "learning", "signal": "🟣", "meaning": "practice, review again, or feed safe lesson into Matrix learning"},
    {"state": "full_green_locked", "signal": "🔒", "meaning": "do not call full green until all seven evidence gates are live-proved"},
    {"state": "founder_final", "signal": "👑", "meaning": "final authority stays with Founder"},
)

FULL_GREEN_REQUIREMENTS: tuple[str, ...] = (
    "14 brain parts present",
    "7 evidence gates present for every brain part",
    "agent/tool runner declared and safely callable",
    "Guardian pass recorded",
    "Green Gate pass recorded",
    "HRM receipt written and readable",
    "Neon receipt written and readable when Neon is available",
    "War Room live proof result recorded",
    "Matrix learning receipt recorded from the result",
    "acceptance tests pass",
    "public/private boundary passes",
    "no hidden tracking, payment capture, dispatch, self-approval, or fake green",
    "Founder Authority final approval",
)


def evidence_gate_status() -> dict[str, Any]:
    """Return the completed 14 x 7 evidence protocol without claiming live proof."""

    current_real_evidence = 3
    possible = len(EVIDENCE_7_GATES)
    parts = []
    for target in BRAIN_14_EVIDENCE_TARGETS:
        gates = []
        for gate in EVIDENCE_7_GATES:
            position = int(gate["position"])
            gates.append(
                {
                    **gate,
                    "evidence_passed_now": position <= current_real_evidence,
                    "evidence_light": "green" if position <= current_real_evidence else "orange",
                    "next_action": "keep" if position <= current_real_evidence else gate["required_proof"],
                }
            )
        parts.append(
            {
                **target,
                "evidence_current": current_real_evidence,
                "evidence_possible": possible,
                "evidence_label": f"{current_real_evidence}/{possible}",
                "protocol_complete": True,
                "live_full_green": False,
                "gates": tuple(gates),
                "missing_gates": tuple(gate["label"] for gate in gates if not gate["evidence_passed_now"]),
            }
        )

    total_current = len(parts) * current_real_evidence
    total_possible = len(parts) * possible
    return {
        "name": "SMI Brain 14 x 7 Evidence Completion Protocol",
        "mode": "read_only_founder_review",
        "protocol_complete": True,
        "live_full_green": False,
        "review_green": True,
        "evidence_current": total_current,
        "evidence_possible": total_possible,
        "evidence_label": f"{total_current}/{total_possible}",
        "evidence_light": "orange",
        "simulation_light": "green",
        "philosophy_light": "green",
        "buttons": PROTOCOL_BUTTONS,
        "decision_states": EVIDENCE_DECISION_STATES,
        "gates": EVIDENCE_7_GATES,
        "brain_parts": tuple(parts),
        "full_green_requirements": FULL_GREEN_REQUIREMENTS,
        "founder_final_required": True,
        "green_gate_reason": "Protocol is finished, but real evidence remains 3/7 until live runners, receipts, tests and Founder final approval prove gates 4-7.",
    }


def completion_check(part_id: str | None = None) -> dict[str, Any]:
    """Return one part or the full protocol evidence gate board."""

    status = evidence_gate_status()
    requested = (part_id or "all").strip().lower()
    if requested in {"all", "", "*"}:
        return status

    matches = tuple(part for part in status["brain_parts"] if str(part["id"]).lower() == requested)
    return {
        "name": "SMI Brain Evidence Completion Check",
        "requested": requested,
        "match_found": bool(matches),
        "brain_part": matches[0] if matches else None,
        "protocol_complete": status["protocol_complete"],
        "live_full_green": False,
        "founder_final_required": True,
    }
