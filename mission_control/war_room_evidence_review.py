"""Read-only, evidence-linked War Room mission review projection.

This does not run agents, award Green, write receipts or grant execution authority.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from .smi_judge_rotation import CANONICAL_JUDGE_NAMES, rotation_plan

_SHA = re.compile(r"^[a-fA-F0-9]{40}$")
_ALLOWED = {"passed", "failed", "pending", "unknown"}


def project_mission_evidence(
    *,
    mission: str,
    revision: str,
    checks: Mapping[str, Mapping[str, object]],
) -> dict[str, Any]:
    """Project supplied exact-revision check receipts without fabricating votes."""
    if not mission.strip() or len(mission) > 160:
        raise ValueError("bounded mission name required")
    if not _SHA.fullmatch(revision):
        raise ValueError("exact 40-character commit SHA required")
    if len(checks) > 100:
        raise ValueError("too many check receipts")
    normalized: list[dict[str, str]] = []
    for name, raw in sorted(checks.items()):
        if not isinstance(name, str) or not name or len(name) > 120:
            raise ValueError("invalid check name")
        if not isinstance(raw, Mapping):
            raise ValueError("invalid check receipt")
        status = raw.get("status")
        check_revision = raw.get("revision")
        if status not in _ALLOWED or check_revision != revision:
            raise ValueError("check status or revision mismatch")
        normalized.append({"check": name, "status": status, "revision": revision})
    blocking = [row["check"] for row in normalized if row["status"] != "passed"]
    return {
        "mission": mission,
        "revision": revision,
        "checks": normalized,
        "checks_total": len(normalized),
        "checks_passed": sum(row["status"] == "passed" for row in normalized),
        "blocking_checks": blocking,
        "review_order": rotation_plan(mission, "evidence_review")["review_order"],
        "canonical_judges": CANONICAL_JUDGE_NAMES,
        "judge_votes": None,
        "agent_execution_verified": False,
        "external_checks_authenticated": False,
        "green_gate": "not_verified",
        "founder_final": "required",
        "full_green": False,
        "mode": "read_only_untrusted_evidence_projection",
    }
