"""Founder-only coherent automation planner for SMI.

This module composes existing OAP evidence and signal language into one bounded
planning contract. It never performs external execution, never grants authority,
and never turns missing proof green. Human Authority remains final.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from . import live_signals, smi_brain_protocol, telemetry

AUTOMATION_ID = "oap-coherent-automation"
AUTOMATION_NAME = "OAP Coherent Automation"


def _signal_pack() -> tuple[dict[str, str], ...]:
    return tuple(dict(item) for item in live_signals.LIVE_SIGNALS)


def _iso_from_epoch(value: object) -> str | None:
    try:
        epoch = float(value)
    except (TypeError, ValueError):
        return None
    if epoch <= 0:
        return None
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def operational_monitor() -> dict[str, Any]:
    """Return a source-backed runtime observation without inventing live proof."""

    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    try:
        runtime = telemetry.status()
    except Exception:  # noqa: BLE001 - monitor must fail closed.
        runtime = {}

    source_epoch = max(
        int(runtime.get("local_last_request_epoch") or 0),
        int(runtime.get("local_last_health_success_epoch") or 0),
        int(runtime.get("last_success_epoch") or 0),
    )
    source_timestamp = _iso_from_epoch(source_epoch)
    observability_ready = bool(runtime.get("observability_ready"))
    request_count = int(runtime.get("local_request_count") or 0)
    health_success_count = int(runtime.get("local_health_success_count") or 0)
    activity_seen = bool(source_timestamp or request_count or health_success_count)

    if observability_ready:
        observed_signal = live_signals.get_signal("connected")
        freshness = "fresh"
    elif activity_seen:
        observed_signal = live_signals.get_signal("warning")
        freshness = "stale_or_incomplete"
    else:
        observed_signal = live_signals.get_signal("offline")
        freshness = "unseen"

    observation = {
        "id": "runtime_observability",
        "name": "SMI Runtime Observability",
        "signal": observed_signal,
        "source": "mission_control.telemetry.status",
        "source_timestamp": source_timestamp,
        "observed_at": generated_at,
        "freshness": freshness,
        "freshness_window_seconds": int(runtime.get("local_fresh_seconds") or 300),
        "evidence": {
            "request_count": request_count,
            "health_success_count": health_success_count,
            "error_count": int(runtime.get("local_error_count") or 0),
            "observability_ready": observability_ready,
            "external_delivery_verified": bool(runtime.get("delivery_verified")),
        },
        "proof_state": "proven" if observability_ready else "proof_required",
        "external_authority": False,
    }
    return {
        "name": "Signal Intelligence Monitor",
        "generated_at": generated_at,
        "source_backed": bool(source_timestamp),
        "observation_count": 1,
        "observations": (observation,),
        "registry_signal_count": len(live_signals.LIVE_SIGNALS),
        "registry_is_not_live_evidence": True,
        "execution_allowed": False,
        "human_authority_final": True,
    }


def status() -> dict[str, Any]:
    validation = live_signals.validate_signal_language()
    monitor = operational_monitor()
    return {
        "id": AUTOMATION_ID,
        "name": AUTOMATION_NAME,
        "ready": bool(validation.get("passed")),
        "mode": "plan-route-check-receipt",
        "signal_count": len(live_signals.LIVE_SIGNALS),
        "signals": _signal_pack(),
        "signals_valid": bool(validation.get("passed")),
        "signal_intelligence_monitor": monitor,
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
