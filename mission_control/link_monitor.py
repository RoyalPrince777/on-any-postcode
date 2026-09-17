"""Read-only Link Up evidence for Signal Intelligence Monitor.

This adapter reports the protected communications contract and fail-closed
realtime capability state. It does not read message bodies, participants,
location, media, or invent live delivery/activity proof.
"""
from __future__ import annotations

from typing import Any

from . import link_realtime, linkup


def observation(observed_at: str) -> dict[str, Any]:
    """Return privacy-safe Link Up readiness without claiming live activity."""

    try:
        scope = linkup.validate_link_scope()
        runtime = dict(linkup.PROTECTED_LINK_RUNTIME)
        capabilities = link_realtime.capability_state()
    except Exception:  # noqa: BLE001 - evidence monitor must fail closed.
        scope = {"passed": False, "checks": {}}
        runtime = {}
        capabilities = []

    protected_runtime_ready = bool(
        scope.get("passed")
        and runtime.get("authenticated_identity_required")
        and runtime.get("sender_recipient_scope")
        and runtime.get("rate_limit_enabled")
        and runtime.get("guardian_message_screening")
        and runtime.get("public_message_projection") is False
    )
    ready_capabilities = sum(bool(item.get("ready")) for item in capabilities)
    total_capabilities = len(capabilities)

    # No trusted activity timestamp currently exists in the canonical Link Up
    # status surface. Architecture/protection proof must not become fake live chat.
    source_timestamp = None
    live_message_activity_proven = False
    delivery_activity_proven = False
    read_activity_proven = False

    return {
        "id": "the_link_link_up",
        "name": "The Link / Link Up Evidence",
        "source": "mission_control.linkup + mission_control.link_realtime",
        "source_timestamp": source_timestamp,
        "observed_at": observed_at,
        "freshness": "runtime_contract_only",
        "freshness_window_seconds": 0,
        "evidence": {
            "scope_valid": bool(scope.get("passed")),
            "protected_runtime_ready": protected_runtime_ready,
            "authenticated_identity_required": bool(runtime.get("authenticated_identity_required")),
            "sender_recipient_scope": bool(runtime.get("sender_recipient_scope")),
            "postgres_message_persistence_declared": runtime.get("message_persistence") == "Postgres Communications store",
            "rate_limit_enabled": bool(runtime.get("rate_limit_enabled")),
            "guardian_message_screening": bool(runtime.get("guardian_message_screening")),
            "read_receipts_declared": bool(runtime.get("read_receipts")),
            "public_message_projection": bool(runtime.get("public_message_projection", False)),
            "realtime_capability_ready_count": ready_capabilities,
            "realtime_capability_total": total_capabilities,
            "live_message_activity_proven": live_message_activity_proven,
            "delivery_activity_proven": delivery_activity_proven,
            "read_activity_proven": read_activity_proven,
            "around_now_live_proven": False,
            "live_spot_live_proven": False,
            "call_live_proven": False,
            "face_up_live_proven": False,
            "reads_message_content": False,
            "reads_participant_identity": False,
            "reads_location": False,
        },
        "proof_state": "partial_proof" if protected_runtime_ready else "proof_required",
        "external_authority": False,
    }
