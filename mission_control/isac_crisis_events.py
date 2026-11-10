"""Founder-private ISAC civilian emergency event projection.

This is an offline policy foundation, not a connected alert feed, a sensor, or
an emergency-response service. Never infer an all-clear from missing data.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SourceKind(str, Enum):
    SENSOR = "sensor"
    OFFICIAL_ALERT = "official_alert"
    HUMAN_REPORT = "human_report"


class EvidenceStatus(str, Enum):
    OBSERVED = "observed"
    REPORTED = "reported"
    INFERRED = "inferred"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class CrisisEvent:
    event_id: str
    source_id: str
    source_kind: SourceKind
    evidence_status: EvidenceStatus
    recorded_at: str
    description: str
    location_sensitive: bool = False
    personal_data: bool = False
    verified_source: bool = False


def project_crisis_event(
    event: CrisisEvent, *, founder_authenticated: bool, access_granted: bool
) -> dict:
    """Fail closed on identity, consent, and unverified provenance."""
    if not founder_authenticated or not access_granted:
        return {"status": "DENIED", "event": None}
    if not event.verified_source:
        return {
            "status": "UNVERIFIED_SOURCE",
            "event": None,
            "action_authorized": False,
        }
    return {
        "status": "ADVISORY_ONLY",
        "event": {
            "event_id": event.event_id,
            "source_id": event.source_id,
            "source_kind": event.source_kind.value,
            "evidence_status": event.evidence_status.value,
            "recorded_at": event.recorded_at,
            "description": event.description,
            "location_sensitive": event.location_sensitive,
            "personal_data": event.personal_data,
        },
        "source_verified": True,
        "event_truth_verified": False,
        "freshness_verified": False,
        "emergency_services_contacted": False,
        "action_authorized": False,
        "monitoring_active": False,
    }
