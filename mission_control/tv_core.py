"""Canonical first-party OAP TV control plane.

This module models the governed TV lifecycle and release gates.  It deliberately
does not claim media transport, transcoding, CDN delivery, payments or device
acceptance unless runtime evidence is supplied.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

CANONICAL_FLOW = (
    "studio",
    "rights",
    "catalogue",
    "schedule",
    "broadcast",
    "distribution",
    "player",
    "analytics",
    "revenue",
    "records",
)

SERVICES = (
    "tv-core",
    "media-catalogue",
    "rights-core",
    "schedule-core",
    "broadcast-core",
    "distribution-core",
    "player-core",
    "entitlement-core",
    "studio-core",
    "archive-core",
    "analytics-core",
    "revenue-core",
    "safety-core",
)

GEOGRAPHY = (
    "postcode",
    "borough_or_district",
    "county_or_region",
    "country",
    "continent",
    "global",
)

REQUIRED_RIGHTS_FIELDS = (
    "asset_id",
    "owner",
    "rights_holder",
    "licence_type",
    "evidence_reference",
    "allowed_territories",
    "starts_at",
    "expires_at",
    "audience_rating",
    "distribution_permissions",
)

RUNTIME_GATES = (
    "real_media_ingest",
    "adaptive_playback",
    "schedule_epg",
    "rights_enforcement",
    "territory_enforcement",
    "viewer_entitlement",
    "stop_and_recovery",
    "archive_readback",
    "youth_safety",
    "device_acceptance",
)

def rights_gate(asset: Mapping[str, Any]) -> dict[str, Any]:
    missing = [field for field in REQUIRED_RIGHTS_FIELDS if not asset.get(field)]
    certified = asset.get("rights_status") == "certified"
    human_approved = asset.get("human_approved") is True
    passed = not missing and certified and human_approved
    return {
        "passed": passed,
        "missing": missing,
        "rights_certified": certified,
        "human_approved": human_approved,
        "public_distribution_allowed": passed,
        "reason": "rights_gate_passed" if passed else "rights_evidence_or_approval_missing",
    }

def distribution_gate(
    asset: Mapping[str, Any],
    *,
    stop_active: bool,
    entitlement_required: bool,
    entitlement_granted: bool,
) -> dict[str, Any]:
    rights = rights_gate(asset)
    territory = asset.get("requested_territory")
    allowed = asset.get("allowed_territories") or ()
    territory_allowed = territory in allowed or "global" in allowed
    entitlement_ok = (not entitlement_required) or entitlement_granted
    passed = rights["passed"] and territory_allowed and entitlement_ok and not stop_active
    return {
        "passed": passed,
        "rights": rights,
        "territory_allowed": territory_allowed,
        "entitlement_ok": entitlement_ok,
        "stop_active": bool(stop_active),
        "playback_authorised": passed,
        "fail_closed": not passed,
    }

def red_team_report(evidence: Mapping[str, Any] | None = None) -> dict[str, Any]:
    evidence = evidence or {}
    gates = {name: bool(evidence.get(name)) for name in RUNTIME_GATES}
    passed = [name for name, ok in gates.items() if ok]
    blocked = [name for name, ok in gates.items() if not ok]
    percentage = round((len(passed) / len(RUNTIME_GATES)) * 100)
    return {
        "gates": gates,
        "passed": passed,
        "blocked": blocked,
        "software_readiness_percent": percentage,
        "green": not blocked,
        "truth_mode": True,
        "human_authority_final": True,
    }

def status(evidence: Mapping[str, Any] | None = None) -> dict[str, Any]:
    red_team = red_team_report(evidence)
    return {
        "system": "OAP TV",
        "mode": "first_party_broadcast_distribution_os",
        "canonical_flow": CANONICAL_FLOW,
        "services": SERVICES,
        "geography": GEOGRAPHY,
        "red_team": red_team,
        "live_broadcast_claimed": False,
        "external_distribution_claimed": False,
        "payments_claimed": False,
        "device_acceptance_claimed": False,
        "truth_mode": True,
        "human_authority_final": True,
    }
