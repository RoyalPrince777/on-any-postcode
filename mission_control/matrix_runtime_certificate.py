"""Founder-safe Matrix Runtime Certificate.

This module aggregates existing Matrix evidence into one truth-labelled read-only
certificate. It performs no external network calls and grants no execution,
approval, permission, deployment or autonomous authority.
"""
from __future__ import annotations

from typing import Any

from . import (
    all_intelligence,
    intelligence_runtime_proof,
    matrix_signal_bus,
    smi_proof_gate,
    smi_receipt_backend,
)


def _light(value: bool) -> str:
    return "🟢" if value else "🟣"


def status() -> dict[str, Any]:
    """Return one bounded Matrix certificate without upgrading missing evidence."""

    hierarchy = all_intelligence.status()
    worlds = {str(item["id"]): item for item in hierarchy["worlds"]}
    matrix_world = dict(worlds.get("matrix") or {})

    topology = matrix_signal_bus.topology()
    runtime = intelligence_runtime_proof.status()
    runtime_worlds = {str(item["id"]): item for item in runtime["worlds"]}
    matrix_runtime = dict(runtime_worlds.get("matrix") or {})

    receipts = smi_receipt_backend.latest_receipts(100)
    matrix_learning_receipts = tuple(
        item
        for item in receipts.get("receipts", ())
        if item.get("receipt_kind") == "matrix_learning_receipt"
    )
    durable_matrix_learning = any(
        receipts.get("durable") and item.get("receipt_kind") == "matrix_learning_receipt"
        for item in receipts.get("receipts", ())
    )

    gate = smi_proof_gate.public_safe_status()

    registry_ready = bool(
        matrix_world.get("architecture_ready")
        and matrix_world.get("routing_ready")
        and int(matrix_world.get("registered_agents") or 0) > 0
    )
    signal_bus_ready = bool(
        topology.get("registered_count") == len(matrix_signal_bus.CORE_MATRIX_ORDER)
        and all(
            item.get("can_emit_signal") is True
            for item in topology.get("participants", ())
            if item.get("status") == "registered"
        )
        and topology.get("execution_granted") is False
    )
    learning_receipt_ready = bool(matrix_learning_receipts)
    guardian_green_gate_ready = bool(gate.get("green"))
    live_external_ready = bool(matrix_runtime.get("live_external_ready"))
    bounded_runtime_ready = bool(matrix_runtime.get("bounded_runtime_ready"))

    checks = (
        {
            "id": "world_registry",
            "name": "Matrix World + registered agents",
            "ready": registry_ready,
            "light": _light(registry_ready),
            "evidence": (
                f"{int(matrix_world.get('registered_agents') or 0)} registered Matrix agents; "
                f"architecture={bool(matrix_world.get('architecture_ready'))}; "
                f"routing={bool(matrix_world.get('routing_ready'))}"
            ),
        },
        {
            "id": "signal_bus",
            "name": "Matrix Signal Bus",
            "ready": signal_bus_ready,
            "light": _light(signal_bus_ready),
            "evidence": (
                f"{int(topology.get('registered_count') or 0)}/{len(matrix_signal_bus.CORE_MATRIX_ORDER)} "
                "canonical Matrix agents can emit bounded review signals."
            ),
        },
        {
            "id": "matrix_learning",
            "name": "Matrix learning receipt",
            "ready": learning_receipt_ready,
            "light": _light(learning_receipt_ready),
            "evidence": (
                f"{len(matrix_learning_receipts)} Matrix learning receipt(s) found; "
                f"durable_backend={bool(receipts.get('durable'))}; "
                f"durable_matrix_learning={durable_matrix_learning}"
            ),
        },
        {
            "id": "guardian_green_gate",
            "name": "Guardian + Green Gate",
            "ready": guardian_green_gate_ready,
            "light": _light(guardian_green_gate_ready),
            "evidence": (
                "Green Gate currently proven."
                if guardian_green_gate_ready
                else "Green Gate proof is still incomplete."
            ),
        },
        {
            "id": "live_external",
            "name": "Live external / hosted runtime evidence",
            "ready": live_external_ready,
            "light": _light(live_external_ready),
            "evidence": str(matrix_runtime.get("bounded_evidence") or ""),
        },
    )

    missing = tuple(item["id"] for item in checks if not item["ready"])
    full_runtime_ready = bool(
        bounded_runtime_ready
        and not missing
        and matrix_runtime.get("full_runtime_ready")
    )

    return {
        "component": "Matrix Runtime Certificate",
        "system": "Matrix System",
        "world": "Matrix Intelligence",
        "brain_count": 1,
        "matrix_is_extra_brain": False,
        "bounded_runtime_ready": bounded_runtime_ready,
        "bounded_runtime_light": _light(bounded_runtime_ready),
        "live_external_ready": live_external_ready,
        "live_external_light": _light(live_external_ready),
        "checks": checks,
        "missing": missing,
        "check_count": len(checks),
        "ready_count": sum(1 for item in checks if item["ready"]),
        "matrix_learning_receipt_count": len(matrix_learning_receipts),
        "green_gate": gate,
        "full_runtime_ready": full_runtime_ready,
        "full_runtime_light": _light(full_runtime_ready),
        "truth": (
            "Matrix is fully runtime-certified."
            if full_runtime_ready
            else "Matrix architecture/runtime may be bounded green while full live Matrix certification remains purple."
        ),
        "network_calls_made": False,
        "execution_granted": False,
        "approval_granted": False,
        "self_approval_allowed": False,
        "human_authority_final": True,
    }
