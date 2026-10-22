"""Read-only, evidence-linked War Room mission review projection.

This does not run agents, award Green, write receipts or grant execution authority.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from .smi_deep_dive_protocol import SEVEN_STAR_GATE
from .smi_judge_rotation import CANONICAL_JUDGE_NAMES, rotation_plan

_SHA = re.compile(r"^[a-fA-F0-9]{40}$")
_ALLOWED = {"passed", "failed", "pending", "unknown"}


def unverified_review() -> dict[str, Any]:
    """Default for surfaces without authenticated, revision-bound proof ingestion."""
    return {
        "revision": None,
        "vpi_percent": None,
        "acceptance_inventory_verified": False,
        "proof_dimensions": [
            {"name": name, "status": "not_verified", "star_awarded": False}
            for name in SEVEN_STAR_GATE
        ],
        "judge_votes": None,
        "agent_execution_verified": False,
        "external_checks_authenticated": False,
        "green_gate": "not_verified",
        "founder_final": "required",
        "full_green": False,
        "live_booking_verified": False,
        "dispatch_verified": False,
        "payment_verified": False,
        "mode": "read_only_untrusted_evidence_projection",
    }


def project_mission_evidence(
    *,
    mission: str,
    revision: str,
    checks: Mapping[str, Mapping[str, object]],
    required_checks: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Project supplied exact-revision check receipts without fabricating votes."""
    if not isinstance(mission, str) or not mission.strip() or len(mission) > 160:
        raise ValueError("bounded mission name required")
    if not isinstance(revision, str) or not _SHA.fullmatch(revision):
        raise ValueError("exact 40-character commit SHA required")
    if not isinstance(checks, Mapping):
        raise TypeError("invalid check receipts")
    if len(checks) > 100:
        raise ValueError("too many check receipts")
    if (
        not isinstance(required_checks, tuple)
        or len(required_checks) > 100
        or any(not isinstance(name, str) or not name.strip() or len(name) > 120
               for name in required_checks)
        or len(set(required_checks)) != len(required_checks)
    ):
        raise ValueError("bounded unique required check names required")
    normalized: list[dict[str, str]] = []
    for name, raw in checks.items():
        if not isinstance(name, str) or not name.strip() or len(name) > 120:
            raise ValueError("invalid check name")
        if not isinstance(raw, Mapping):
            raise TypeError("invalid check receipt")
        status = raw.get("status")
        check_revision = raw.get("revision")
        if not isinstance(status, str) or status not in _ALLOWED or check_revision != revision:
            raise ValueError("check status or revision mismatch")
        normalized.append({"check": name, "status": status, "revision": revision})
    normalized.sort(key=lambda row: row["check"])
    missing = sorted(set(required_checks) - checks.keys())
    blocking = sorted({row["check"] for row in normalized if row["status"] != "passed"} | set(missing))
    return {
        **unverified_review(),
        "mission": mission,
        "revision": revision,
        "checks": normalized,
        "checks_total": len(normalized),
        "checks_passed": sum(row["status"] == "passed" for row in normalized),
        "blocking_checks": blocking,
        "required_checks": sorted(required_checks),
        "missing_checks": missing,
        "required_check_inventory_supplied": bool(required_checks),
        "review_order": rotation_plan(mission, "evidence_review")["review_order"],
        "canonical_judges": CANONICAL_JUDGE_NAMES,
    }
