"""Founder-governed, advisory-only defensive intelligence assessment.

Uses the canonical world observation envelope; never collects, intercepts,
executes, or treats public reporting as an OAP-owned observation.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from . import world_observation

DIVISIONS = (
    "strategic", "tactical", "earth_geoint", "signals",
    "cyber", "human", "counterintelligence",
)
ALLOWED_EVENTS = frozenset(("hazard", "outage", "integrity", "incident", "report"))
ALLOWED_OWNERSHIP = frozenset(("oap_owned", "founder_approved_external", "external_public"))


def assess(
    observation: Mapping[str, Any],
    *,
    division: str,
    founder_authorised: bool = False,
    public_source_authorised: bool = False,
) -> dict[str, Any]:
    """Return a bounded assessment only when authority and evidence are present."""
    if division not in DIVISIONS:
        raise ValueError("unknown defensive intelligence division")
    if not founder_authorised:
        raise PermissionError("Founder authority required")
    envelope = world_observation.normalise(observation)
    ownership = envelope["source_ownership"]
    if ownership not in ALLOWED_OWNERSHIP:
        raise PermissionError("source ownership not allowed")
    if ownership != "oap_owned" and not public_source_authorised:
        raise PermissionError("external source requires explicit authorisation")
    if envelope["event_type"] not in ALLOWED_EVENTS:
        raise ValueError("event outside defensive scope")
    if not envelope["evidence"] or envelope["evidence_class"] == "unverified":
        raise ValueError("defensive assessment requires evidence")
    if envelope["freshness_state"] in ("unknown", "expired"):
        raise ValueError("observation time missing or expired")
    return {
        "division": division,
        "observation": envelope,
        "advisory_only": True,
        "execution_granted": False,
        "human_authority_final": True,
        "public_source_separately_labelled": ownership != "oap_owned",
        "production_ready": False,
    }


def status() -> dict[str, Any]:
    return {
        "name": "OAP Defensive Intelligence 777",
        "divisions": DIVISIONS,
        "live_sensors_connected": False,
        "external_feeds_connected": False,
        "execution_granted": False,
        "production_ready": False,
        "human_authority_final": True,
    }
