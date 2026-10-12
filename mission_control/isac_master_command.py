"""ISAC master command projection over existing spatial status.

This does not manufacture crisis feeds, cameras, rights advice, or 24h coverage.
All sections derive from real supplied evidence; missing evidence fails closed.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any


def master_isac_status(
    spatial: dict[str, Any],
    *,
    crisis_feed: dict[str, Any] | None = None,
    surveillance: dict[str, Any] | None = None,
    communications: dict[str, Any] | None = None,
    rights: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return privacy-minimal Founder dashboard state, not operational authority."""
    def source_state(source: dict[str, Any] | None) -> dict[str, Any]:
        if not isinstance(source, dict) or not source.get("verified") or not source.get("checked_at"):
            return {"status": "NOT_CONNECTED", "last_checked": None}
        try:
            checked_at = datetime.fromisoformat(str(source["checked_at"]))
            now = datetime.now(UTC)
            if checked_at.tzinfo is None or not (timedelta(0) <= now - checked_at <= timedelta(minutes=15)):
                return {"status": "STALE", "last_checked": source["checked_at"]}
        except (ValueError, TypeError, OverflowError):
            return {"status": "EVIDENCE_REQUIRED", "last_checked": None}
        if not source.get("operational"):
            return {"status": "INTERRUPTED", "last_checked": source["checked_at"]}
        return {"status": "CONNECTED", "last_checked": source["checked_at"]}

    radio = bool(spatial.get("live_radio_connected"))
    hardware = bool(spatial.get("hardware_green"))
    return {
        "scope": "FOUNDER_PRIVATE",
        "monitor": {
            "spatial_software": "READY" if spatial.get("software_ready") else "EVIDENCE_REQUIRED",
            "radio": "CONNECTED" if radio and hardware else "NOT_CONNECTED",
            "surveillance": source_state(surveillance),
            "communications": source_state(communications),
        },
        "incoming": {"world_crisis": source_state(crisis_feed)},
        "intelligence": {
            "human_rights": source_state(rights),
            "source_claims_require_evidence": True,
            "event_truth_not_implied_by_source_verification": True,
        },
        "guardian": {"permissions_required": True, "raw_rf_export": False},
        "gorilla": {"physical_actions_authorized": False},
        "fox": {"offline_recovery_verified": False},
        "founder_final": True,
        "continuous_monitoring_verified": False,
        "overall": "EVIDENCE_REQUIRED",
    }
