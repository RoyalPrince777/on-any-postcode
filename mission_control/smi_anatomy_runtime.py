"""Founder-safe SMI 21 Anatomy Runtime Certificate.

SMI remains one brain. Fourteen biological regions organise responsibilities;
3/7/21 is the adaptive reasoning depth and 21 is also the Mind/Body/Soul
governance protocol length. This certificate never turns protocol presence into
live proof without a matching runtime receipt.
"""
from __future__ import annotations

from typing import Any

from . import (
    smi_brain_evidence_protocol,
    smi_brain_protocol,
    smi_receipt_backend,
)

RECEIPT_GATE_MAP: dict[str, str] = {
    "agent_tool_connection_receipt": "agent_tool_connected",
    "hrm_neon_evidence_receipt": "hrm_neon_receipt",
    "war_room_live_proof_receipt": "live_war_room_proof",
    "matrix_learning_receipt": "matrix_learning_loop",
}

BASE_PASSED_GATES: tuple[str, ...] = (
    "named",
    "role_defined",
    "protocol_mapped",
)


def status() -> dict[str, Any]:
    """Return per-region truth without writing receipts or making network calls."""

    protocol = smi_brain_evidence_protocol.evidence_gate_status()
    receipts = smi_receipt_backend.latest_receipts(200)
    by_part: dict[str, set[str]] = {}
    for receipt in receipts.get("receipts", ()):
        gate_id = RECEIPT_GATE_MAP.get(str(receipt.get("receipt_kind") or ""))
        part_id = str(receipt.get("brain_part") or "")
        if gate_id and part_id:
            by_part.setdefault(part_id, set()).add(gate_id)

    parts = []
    for target in protocol["brain_parts"]:
        part_id = str(target["id"])
        receipt_gates = by_part.get(part_id, set())
        passed = set(BASE_PASSED_GATES) | receipt_gates
        gates = []
        for gate in protocol["gates"]:
            gate_id = str(gate["id"])
            proven = gate_id in passed
            gates.append(
                {
                    "id": gate_id,
                    "label": gate["label"],
                    "proven": proven,
                    "light": "🟢" if proven else "🟣",
                    "evidence_source": (
                        "canonical_anatomy_protocol"
                        if gate_id in BASE_PASSED_GATES
                        else "runtime_receipt"
                        if proven
                        else "runtime_receipt_required"
                    ),
                }
            )
        score = sum(1 for item in gates if item["proven"])
        parts.append(
            {
                "id": part_id,
                "target": target["target"],
                "live_case": target["live_case"],
                "evidence_score": score,
                "evidence_possible": 7,
                "evidence_label": f"{score}/7",
                "light": "🟢" if score == 7 else "🟣",
                "gates": tuple(gates),
                "missing": tuple(
                    item["id"] for item in gates if not item["proven"]
                ),
            }
        )

    fully_proven = sum(1 for part in parts if part["evidence_score"] == 7)
    total_evidence = sum(int(part["evidence_score"]) for part in parts)
    possible_evidence = len(parts) * 7

    return {
        "component": "SMI 21 Anatomy Runtime Certificate",
        "brain_name": "Sovereign Megaverse Intelligence",
        "brain_count": 1,
        "anatomical_region_count": len(parts),
        "anatomical_region_target": 14,
        "adaptive_depths": (3, 7, 21),
        "protocol_stages": 21,
        "mind_body_soul_blocks": 3,
        "laws_count": len(smi_brain_protocol.LAWS_21),
        "signals_count": len(smi_brain_protocol.SIGNALS_21),
        "regions": tuple(parts),
        "fully_proven_regions": fully_proven,
        "evidence_current": total_evidence,
        "evidence_possible": possible_evidence,
        "evidence_percentage": round(
            (total_evidence / possible_evidence) * 100, 1
        )
        if possible_evidence
        else 0.0,
        "receipt_backend": {
            "backend": receipts.get("backend"),
            "durable": bool(receipts.get("durable")),
            "fallback_used": bool(receipts.get("fallback_used")),
        },
        "anatomy_complete": len(parts) == 14,
        "protocol_complete": (
            len(smi_brain_protocol.LAWS_21) == 21
            and len(smi_brain_protocol.SIGNALS_21) == 21
        ),
        "full_runtime_green": bool(fully_proven == 14),
        "full_runtime_light": "🟢" if fully_proven == 14 else "🟣",
        "network_calls_made": False,
        "execution_granted": False,
        "approval_granted": False,
        "human_authority_final": True,
    }
