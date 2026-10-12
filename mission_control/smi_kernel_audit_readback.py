"""Read-only, request-bound verification of existing Founder Living Kernel audit events.

This verifies the canonical audit row, not an independent HRM receipt.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from . import authority, postgres_db


@dataclass(frozen=True)
class KernelAuditReadback:
    request_id: str
    verified: bool
    executed: bool
    reason: str
    event_id: str | None = None
    durable_hrm_receipt_proven: bool = False


def readback_kernel_audit(*, identity_id: str, request_id: str) -> KernelAuditReadback:
    """Read the authoritative PostgreSQL audit, fail closed on ambiguous outcomes."""
    try:
        request = str(uuid.UUID(request_id))
        identity = str(uuid.UUID(identity_id))
    except (TypeError, ValueError, AttributeError):
        return KernelAuditReadback(str(request_id), False, False, "INVALID_ID")
    try:
        with postgres_db.connect(readonly=True) as connection:
            authority.require_human_authority(connection, identity)
            rows = connection.execute(
                """SELECT event_id, action, actor_id, target, metadata
                   FROM audit_events
                   WHERE correlation_id=%s
                     AND action IN (
                       'FOUNDER_TOOL_KERNEL_EXECUTED',
                       'FOUNDER_TOOL_KERNEL_BLOCKED'
                     )
                   ORDER BY event_seq DESC LIMIT 2""",
                (request,),
            ).fetchall()
    except PermissionError:
        raise
    except Exception:  # noqa: BLE001 - unavailable evidence is never Green.
        return KernelAuditReadback(request, False, False, "AUDIT_READBACK_UNAVAILABLE")
    if len(rows) != 1:
        return KernelAuditReadback(request, False, False, "MISSING_OR_AMBIGUOUS_AUDIT")
    event_id, action, actor_id, target, metadata = rows[0]
    if not isinstance(metadata, dict):
        return KernelAuditReadback(request, False, False, "INVALID_AUDIT_METADATA")
    executed = action == "FOUNDER_TOOL_KERNEL_EXECUTED"
    if (
        str(actor_id) != identity
        or str(target) != request
        or str(metadata.get("request_id")) != request
        or metadata.get("executed") is not executed
        or not metadata.get("receipt_id")
        or not metadata.get("sovereign_policy_fingerprint")
    ):
        return KernelAuditReadback(request, False, False, "AUDIT_PROVENANCE_MISMATCH")
    return KernelAuditReadback(
        request, True, executed, "CANONICAL_AUDIT_ROW_READ_BACK", str(event_id)
    )
