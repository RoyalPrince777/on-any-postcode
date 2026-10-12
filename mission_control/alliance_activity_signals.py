"""Read-only 21-check projection for SMI Performance & Activity Intelligence.

Separate the operational 21-check vocabulary from the existing 73-signal
Mission Field. No automatic authority, invented telemetry, or false Green.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

CHECKS_21 = (
    "checking", "mode", "proof_needed", "locked", "blocked",
    "next_before_green", "hrm_memory", "source_proof", "route_api_proof",
    "data_proof", "consent_proof", "install_proof", "monitoring_proof",
    "rollback_proof", "founder_approval", "guardian_pass",
    "green_gate_result", "public_private_boundary", "tool_plugin_proof",
    "neon_receipt", "real_green_decision",
)
VALID_STATES = frozenset(("proven", "pending", "blocked", "unknown", "not_applicable"))


def project_agent_signals(
    agent_id: str,
    observations: Mapping[str, Mapping[str, object]] | None = None,
    *,
    applicable: set[str] | None = None,
) -> dict[str, Any]:
    """Project supplied evidence; absent signals remain unknown, never Green.

    Applicability must be explicitly supplied by a governed caller; by default
    every check is applicable. Not-applicable is not counted as proven.
    """
    observations = observations or {}
    eligible = set(CHECKS_21) if applicable is None else set(applicable)
    if eligible - set(CHECKS_21):
        raise ValueError("unknown applicable signal")
    results: dict[str, dict[str, str]] = {}
    for key in CHECKS_21:
        if key not in eligible:
            results[key] = {"state": "not_applicable", "receipt": ""}
            continue
        raw = observations.get(key) or {}
        state = str(raw.get("state") or "unknown").casefold()
        receipt = str(raw.get("receipt") or "").strip()
        if state not in VALID_STATES or state == "not_applicable":
            state = "unknown"
        if state == "proven" and not receipt:
            state = "unknown"
        results[key] = {"state": state, "receipt": receipt}
    required = [results[k]["state"] for k in CHECKS_21 if k in eligible]
    return {
        "agent_id": agent_id,
        "component": "SMI Performance & Activity Intelligence",
        "signal_count": len(CHECKS_21),
        "signals": results,
        "green": bool(required) and all(s == "proven" for s in required),
        "authority_effect": "none",
        "receipt_authenticity_verified": False,
        "integration_status": "read_only_projection",
    }
