"""Founder-only coherent automation planner for SMI.

This module composes existing OAP evidence and signal language into one bounded
planning contract. It never performs external execution, never grants authority,
and never turns missing proof green. Human Authority remains final.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from . import atlas_live_sources, live_signals, smi_brain_protocol, telemetry

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


def _runtime_observation(generated_at: str) -> dict[str, Any]:
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

    return {
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


def _map_observation(generated_at: str) -> dict[str, Any]:
    try:
        evidence = atlas_live_sources.last_fetch_status()
    except Exception:  # noqa: BLE001 - monitor must fail closed.
        evidence = {}

    fetch_status = str(evidence.get("fetch_status") or "unseen")
    freshness = str(evidence.get("freshness") or "unseen")
    source_timestamp = evidence.get("fetched_at")
    result_count = int(evidence.get("result_count") or 0)
    source_backed = bool(evidence.get("source_backed"))

    if source_backed and freshness == "fresh":
        observed_signal = live_signals.get_signal("connected")
        proof_state = "proven"
    elif source_timestamp:
        observed_signal = live_signals.get_signal("warning")
        proof_state = "proof_required"
    else:
        observed_signal = live_signals.get_signal("offline")
        proof_state = "proof_required"

    return {
        "id": "map_intelligence_source",
        "name": "Map Intelligence Source",
        "signal": observed_signal,
        "source": str(evidence.get("source") or "OpenStreetMap / Nominatim"),
        "source_timestamp": source_timestamp,
        "observed_at": generated_at,
        "freshness": freshness,
        "freshness_window_seconds": int(evidence.get("freshness_window_seconds") or 300),
        "evidence": {
            "fetch_status": fetch_status,
            "result_count": result_count,
            "source_backed": source_backed,
            "passive_only": bool(evidence.get("passive_only", True)),
            "hidden_tracking": bool(evidence.get("hidden_tracking", False)),
            "stores_user_location": bool(evidence.get("stores_user_location", False)),
        },
        "proof_state": proof_state,
        "external_authority": False,
    }


def operational_monitor() -> dict[str, Any]:
    """Return source-backed observations without inventing live proof."""

    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    observations = (
        _runtime_observation(generated_at),
        _map_observation(generated_at),
    )
    return {
        "name": "Signal Intelligence Monitor",
        "generated_at": generated_at,
        "source_backed": any(bool(item.get("source_timestamp")) for item in observations),
        "observation_count": len(observations),
        "observations": observations,
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
