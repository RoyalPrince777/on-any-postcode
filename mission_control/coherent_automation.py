"""Founder-only coherent automation planner for SMI.

This module composes existing OAP evidence and signal language into one bounded
planning contract. It never performs external execution, never grants authority,
and never turns missing proof green. Human Authority remains final.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from . import (
    atlas_live_sources,
    live_signals,
    movement_proof,
    smi_brain_protocol,
    telemetry,
    travel_supply_core,
)

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


def _movement_observation(generated_at: str) -> dict[str, Any]:
    try:
        evidence = movement_proof.last_route_status()
    except Exception:  # noqa: BLE001 - monitor must fail closed.
        evidence = {}

    source_timestamp = evidence.get("source_timestamp")
    freshness = str(evidence.get("freshness") or "unseen")
    source_backed = bool(evidence.get("source_backed"))
    proof_status = str(evidence.get("proof_status") or "unseen")
    route_estimate_ready = bool(
        evidence.get("verified_area_pair")
        and evidence.get("distance_estimate_present")
        and evidence.get("eta_estimate_present")
    )

    if source_backed and route_estimate_ready and freshness == "fresh":
        observed_signal = live_signals.get_signal("connected")
        proof_state = "bounded_proof"
    elif source_timestamp:
        observed_signal = live_signals.get_signal("warning")
        proof_state = "proof_required"
    else:
        observed_signal = live_signals.get_signal("offline")
        proof_state = "proof_required"

    return {
        "id": "movement_intelligence_route",
        "name": "Movement Intelligence Route Evidence",
        "signal": observed_signal,
        "source": str(evidence.get("source") or "OAP Movement"),
        "source_timestamp": source_timestamp,
        "observed_at": generated_at,
        "freshness": freshness,
        "freshness_window_seconds": int(evidence.get("freshness_window_seconds") or 300),
        "evidence": {
            "proof_status": proof_status,
            "source_backed": source_backed,
            "verified_area_pair": bool(evidence.get("verified_area_pair")),
            "distance_estimate_present": bool(evidence.get("distance_estimate_present")),
            "eta_estimate_present": bool(evidence.get("eta_estimate_present")),
            "route_geometry_proven": bool(evidence.get("route_geometry_proven", False)),
            "live_traffic_proven": bool(evidence.get("live_traffic_proven", False)),
            "dispatch_enabled": bool(evidence.get("dispatch_enabled", False)),
            "hidden_tracking": bool(evidence.get("hidden_tracking", False)),
            "stores_origin_destination": bool(evidence.get("stores_origin_destination", False)),
            "stores_coordinates": bool(evidence.get("stores_coordinates", False)),
            "passive_only": bool(evidence.get("passive_only", True)),
        },
        "proof_state": proof_state,
        "external_authority": False,
    }


def _direct_observation(generated_at: str) -> dict[str, Any]:
    try:
        evidence = travel_supply_core.status()
    except Exception:  # noqa: BLE001 - monitor must fail closed.
        evidence = {}

    schema_ready = bool(evidence.get("schema_ready"))
    certified_suppliers = int(evidence.get("certified_supplier_count") or 0)
    active_listings = int(evidence.get("active_listing_count") or 0)
    live_inventory = int(evidence.get("live_inventory_slot_count") or 0)
    supply_counts_ready = bool(certified_suppliers and active_listings and live_inventory)

    # The current Supply Core status proves live read-only counts, but it does not
    # yet expose Certified commercial-terms count or the inventory row's own
    # observed_at timestamp. Keep those requirements explicit instead of
    # upgrading a database count into a complete Direct proof claim.
    source_timestamp = generated_at if schema_ready else None
    terms_proven = False
    inventory_timestamp_proven = False

    if schema_ready and supply_counts_ready:
        observed_signal = live_signals.get_signal("warning")
        proof_state = "partial_proof"
        freshness = "checked_now_missing_required_fields"
    elif schema_ready:
        observed_signal = live_signals.get_signal("warning")
        proof_state = "proof_required"
        freshness = "checked_now"
    else:
        observed_signal = live_signals.get_signal("offline")
        proof_state = "proof_required"
        freshness = "unseen"

    return {
        "id": "oap_direct_supply",
        "name": "OAP Direct Supply Evidence",
        "signal": observed_signal,
        "source": "mission_control.travel_supply_core.status",
        "source_timestamp": source_timestamp,
        "observed_at": generated_at,
        "freshness": freshness,
        "freshness_window_seconds": 0,
        "evidence": {
            "schema_ready": schema_ready,
            "certified_supplier_count": certified_suppliers,
            "active_listing_count": active_listings,
            "live_inventory_slot_count": live_inventory,
            "supply_counts_ready": supply_counts_ready,
            "certified_terms_proven": terms_proven,
            "inventory_observation_timestamp_proven": inventory_timestamp_proven,
            "live_direct_supply": bool(evidence.get("live_direct_supply")),
            "direct_booking_runtime_ready": bool(evidence.get("direct_booking_runtime_ready")),
            "payment_capture_live": bool(evidence.get("payment_capture_live", False)),
            "external_provider_authority": bool(evidence.get("external_provider_authority", False)),
            "read_only": True,
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
        _movement_observation(generated_at),
        _direct_observation(generated_at),
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
