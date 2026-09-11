"""Founder-only coherent automation planner for SMI.

This module composes existing OAP evidence and signal language into one bounded
planning contract. It never performs external execution, never grants authority,
and never turns missing proof green. Human Authority remains final.
"""
from __future__ import annotations

from typing import Any

from . import live_signals, smi_brain_protocol

AUTOMATION_ID = "oap-coherent-automation"
AUTOMATION_NAME = "OAP Coherent Automation"


def _signal_pack() -> tuple[dict[str, str], ...]:
    return tuple(dict(item) for item in live_signals.LIVE_SIGNALS)


def status() -> dict[str, Any]:
    validation = live_signals.validate_signal_language()
    return {
        "id": AUTOMATION_ID,
        "name": AUTOMATION_NAME,
        "ready": bool(validation.get("passed")),
        "mode": "plan-route-check-receipt",
        "signal_count": len(live_signals.LIVE_SIGNALS),
        "signals": _signal_pack(),
        "signals_valid": bool(validation.get("passed")),
        "mind_body_soul": smi_brain_protocol.MIND_BODY_SOUL_777,
        "laws_21": smi_brain_protocol.LAWS_21,
        "proof_signals_21": smi_brain_protocol.SIGNALS_21,
        "flow": (
            "Observe",
            "Classify",
            "Verify",
            "Plan",
            "Guardian",
            "Green Gate",
            "Human Authority",
            "Execute only through an authenticated adapter",
            "Receipt",
            "Learn",
        ),
        "duplicate_execution_prevention": True,
        "external_execution_enabled": False,
        "human_authority_final": True,
        "no_fake_green": True,
    }


def plan(command: object, *, target: object = "SMI") -> dict[str, Any]:
    clean_command = " ".join(str(command or "").split())[:2000]
    clean_target = " ".join(str(target or "SMI").split())[:120]
    if not clean_command:
        return {
            "accepted": False,
            "state": "warning",
            "light": "🟡",
            "reason": "command_required",
            "execution_allowed": False,
        }

    return {
        "accepted": True,
        "state": "working",
        "light": "⏳",
        "command": clean_command,
        "target": clean_target,
        "protocol": "Observe → Classify → Verify → Fix/Plan → Retest → Record → Learn",
        "depth": "21-stage available; consequence level decides actual depth",
        "required_before_execution": (
            "source/tool proof",
            "Guardian pass",
            "Green Gate result",
            "Human Authority approval",
            "authenticated adapter",
            "receipt destination",
            "rollback path where consequential",
        ),
        "execution_allowed": False,
        "next": "route_to_governed_adapter_after_required_proof",
        "human_authority_final": True,
    }
