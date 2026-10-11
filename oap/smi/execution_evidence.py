"""Fail-closed SMI evidence classification for existing Living Kernel outcomes.

This is a pure projection, not an HRM receipt writer or execution authority.
Only an authoritative readback from the existing audit store can prove durability.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class ExecutionEvidence:
    request_id: str
    stage: str
    executed: bool
    audit_event_id: str | None
    evidence_verified: bool
    durable_receipt_proven: bool
    reason: str


def classify_kernel_outcome(
    outcome: Mapping[str, Any],
    *,
    audit_readback_verified: bool = False,
) -> ExecutionEvidence:
    """Classify an existing Kernel result without inventing proof or writing receipts.

    audit_readback_verified must only come from a trusted readback path. A caller's
    assertion alone is not cryptographic or independent evidence.
    """
    request_id = str(outcome.get("request_id") or "").strip()
    executed = outcome.get("executed") is True
    kernel = outcome.get("living_kernel") is True
    human = outcome.get("human_authority_final") is True
    audit = str(outcome.get("audit_event_id") or "").strip() or None
    state = str(outcome.get("state") or "").strip()
    if not request_id or not kernel or not human:
        return ExecutionEvidence(request_id, "UNVERIFIED", False, audit, False, False, "MISSING_KERNEL_PROVENANCE")
    if not executed:
        return ExecutionEvidence(request_id, "BLOCKED", False, audit, False, False, "NOT_EXECUTED")
    if not audit:
        return ExecutionEvidence(request_id, "EXECUTED_UNVERIFIED", True, None, False, False, "MISSING_AUDIT_REFERENCE")
    if not audit_readback_verified:
        return ExecutionEvidence(request_id, "EXECUTED_UNVERIFIED", True, audit, False, False, "AUDIT_READBACK_REQUIRED")
    return ExecutionEvidence(request_id, "AUDIT_READBACK_CONFIRMED", True, audit, True, True, "AUDIT_READBACK_CONFIRMED")
