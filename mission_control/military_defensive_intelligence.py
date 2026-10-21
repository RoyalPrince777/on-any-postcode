"""Fail-closed defensive intelligence intake; no collection or execution authority.

Reuses the canonical world observation envelope and preserves source provenance.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from . import world_observation

ALLOWED_EVENTS = frozenset({"environmental_hazard", "service_outage", "cyber_incident", "safety_report"})
ALLOWED_OWNERSHIP = frozenset({"oap_owned", "founder_approved_external"})


def assess(observation: Mapping[str, Any], *, authorised_public_sources: frozenset[str] = frozenset()) -> dict[str, Any]:
    """Admit bounded defensive evidence only; never dispatch an action."""
    record = world_observation.normalise(observation)
    if record["event_type"] not in ALLOWED_EVENTS:
        raise ValueError("defensive event type required")
    if record["source_ownership"] not in ALLOWED_OWNERSHIP:
        raise ValueError("source ownership not authorised")
    if record["source_ownership"] == "founder_approved_external":
        if record["source"] not in authorised_public_sources:
            raise ValueError("public source lacks explicit approval")
        if record["first_party"]["observation"]:
            raise ValueError("public observations are never first-party")
    if record["source_ownership"] == "oap_owned" and not record["first_party"]["observation"]:
        raise ValueError("OAP-owned observation provenance required")
    if not record["evidence"] or record["freshness_state"] not in {"fresh", "aging"}:
        raise ValueError("fresh supporting evidence required")
    if record["evidence_class"] != "observed":
        raise ValueError("verified observation class required")
    return {
        "observation": record,
        "classification": "defensive_review_only",
        "public_source_separately_labelled": record["source_ownership"] != "oap_owned",
        "guardian_review_required": True,
        "hrm_receipt_required": True,
        "founder_final_required": True,
        "execution_granted": False,
        "production_ready": False,
    }
