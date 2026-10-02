"""Fail-closed 700-cell evidence registry for OAP Company Intelligence.

The canonical 700 protocol is 7 review areas x 10 intelligence lenses x 10 evidence
tests. This registry assigns every cell a stable ID and explicit evidence state.
Cells remain UNKNOWN until a timestamped evidence receipt resolves them.

This module records review evidence only. It never grants execution, legal authority,
regulatory permission, deployment, payment authority, or Founder Final.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from typing import Any

from . import company_intelligence

CELL_STATES = ("PASS", "FAIL", "CONFLICTING", "UNKNOWN", "N/A")
_RESOLVED_STATES = {"PASS", "N/A"}


def _timestamp(value: object) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def cell_catalogue() -> tuple[dict[str, str], ...]:
    """Return all 700 canonical cells with stable deterministic IDs."""

    return tuple(
        {
            "check_id": f"CI-{index:03d}",
            "area": area,
            "lens": lens,
            "evidence_test": evidence_test,
        }
        for index, (area, lens, evidence_test) in enumerate(
            company_intelligence.protocol_cells(),
            start=1,
        )
    )


def _normalize_receipt(
    receipt: Mapping[str, object],
    known_ids: set[str],
) -> dict[str, Any] | None:
    check_id = str(receipt.get("check_id") or "").strip().upper()
    state = str(receipt.get("state") or "").strip().upper()
    evidence_reference = str(receipt.get("evidence_reference") or "").strip()[:500]
    failure_reason = str(receipt.get("failure_reason") or "").strip()[:500]
    recovery_requirement = str(
        receipt.get("recovery_requirement") or ""
    ).strip()[:500]
    observed_at = _timestamp(receipt.get("observed_at"))

    if (
        check_id not in known_ids
        or state not in CELL_STATES
        or not evidence_reference
        or observed_at is None
    ):
        return None

    return {
        "check_id": check_id,
        "state": state,
        "evidence_reference": evidence_reference,
        "observed_at": observed_at.isoformat(),
        "failure_reason": failure_reason,
        "recovery_requirement": recovery_requirement,
    }


def snapshot(
    receipts: Iterable[Mapping[str, object]] = (),
    *,
    founder_final_recorded: bool = False,
) -> dict[str, Any]:
    """Build the current 700-cell evidence state from timestamped receipts.

    The newest valid receipt wins per cell. Missing or invalid receipts do not
    advance a cell and therefore remain UNKNOWN.
    """

    catalogue = cell_catalogue()
    by_id = {cell["check_id"]: cell for cell in catalogue}
    known_ids = set(by_id)
    latest: dict[str, dict[str, Any]] = {}
    invalid_count = 0

    for raw in receipts:
        item = _normalize_receipt(raw, known_ids)
        if item is None:
            invalid_count += 1
            continue
        previous = latest.get(item["check_id"])
        if previous is None or item["observed_at"] > previous["observed_at"]:
            latest[item["check_id"]] = item

    cells: list[dict[str, Any]] = []
    for check_id, definition in by_id.items():
        receipt = latest.get(check_id)
        cells.append(
            {
                **definition,
                "state": receipt["state"] if receipt else "UNKNOWN",
                "evidence_reference": receipt["evidence_reference"] if receipt else "",
                "observed_at": receipt["observed_at"] if receipt else None,
                "failure_reason": receipt["failure_reason"] if receipt else "",
                "recovery_requirement": (
                    receipt["recovery_requirement"] if receipt else ""
                ),
            }
        )

    counts = {
        state: sum(cell["state"] == state for cell in cells)
        for state in CELL_STATES
    }
    resolved_count = counts["PASS"] + counts["N/A"]
    green_gate_passed = (
        resolved_count == len(cells)
        and counts["FAIL"] == 0
        and counts["CONFLICTING"] == 0
        and counts["UNKNOWN"] == 0
    )

    return {
        "registry": "OAP Company Intelligence 700 Evidence Registry",
        "protocol_check_count": len(cells),
        "cells": tuple(cells),
        "counts": counts,
        "valid_receipt_count": len(latest),
        "invalid_receipt_count": invalid_count,
        "proven_count": counts["PASS"],
        "resolved_count": resolved_count,
        "proven_percentage": round((counts["PASS"] / len(cells)) * 100, 1),
        "resolved_percentage": round((resolved_count / len(cells)) * 100, 1),
        "green_gate_passed": green_gate_passed,
        "founder_final_recorded": bool(founder_final_recorded),
        "full_green": green_gate_passed and bool(founder_final_recorded),
        "missing_defaults_to_unknown": True,
        "evidence_required_for_na": True,
        "votes_grant_execution": False,
        "execution_authority_granted": False,
        "human_authority_final": True,
    }


def status() -> dict[str, Any]:
    empty = snapshot()
    return {
        "name": empty["registry"],
        "protocol_check_count": empty["protocol_check_count"],
        "cell_states": CELL_STATES,
        "stable_ids": True,
        "latest_valid_receipt_wins": True,
        "missing_defaults_to_unknown": True,
        "founder_final_required": True,
        "full_green": False,
    }
