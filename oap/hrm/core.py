"""Local-first HRM storage for SMI recommendations and Kernel outcomes."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from uuid import uuid4

from oap.audit import append_event, audit_schema_ready, initialize_audit_schema
from oap.contracts import (
    ApprovalReceipt,
    BrainRequest,
    KernelResult,
    MemoryItem,
    Recommendation,
    utc_now,
)

from .schema import brain_schema_ready, initialize_brain_schema


class HRMNotInitialized(RuntimeError):
    """Raised when the SMI memory schema has not been explicitly initialized."""


class ApprovalReceiptReplay(PermissionError):
    """Raised when a receipt or request already has a recorded final decision."""


class HRMCore:
    """HRM adapter that never creates tables implicitly."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.connection.row_factory = sqlite3.Row

    @classmethod
    def in_memory(cls) -> HRMCore:
        """Build an explicit volatile store for tests or isolated local operation."""

        connection = sqlite3.connect(":memory:")
        initialize_audit_schema(connection)
        initialize_brain_schema(connection)
        connection.commit()
        return cls(connection)

    def is_ready(self) -> bool:
        return brain_schema_ready(self.connection)

    def audit_ready(self) -> bool:
        return audit_schema_ready(self.connection)

    def _require_ready(self) -> None:
        if not self.is_ready():
            raise HRMNotInitialized("SMI HRM schema is not initialized")

    def has_request(self, request_id: str) -> bool:
        self._require_ready()
        row = self.connection.execute(
            "SELECT 1 FROM smi_memory_records WHERE request_id = ? LIMIT 1",
            (request_id,),
        ).fetchone()
        return row is not None

    def retrieve_context(
        self,
        task_type: str,
        limit: int = 5,
    ) -> tuple[MemoryItem, ...]:
        self._require_ready()
        safe_limit = min(max(limit, 1), 21)
        rows = self.connection.execute(
            "SELECT memory_id, task_type, summary, output_state, created_at "
            "FROM smi_memory_records WHERE task_type = ? "
            "ORDER BY created_at DESC LIMIT ?",
            (task_type, safe_limit),
        ).fetchall()
        return tuple(
            MemoryItem(
                memory_id=str(row["memory_id"]),
                task_type=str(row["task_type"]),
                summary=str(row["summary"]),
                output_state=str(row["output_state"]),
                created_at=_parse_timestamp(str(row["created_at"])),
            )
            for row in rows
        )

    def record_recommendation(
        self,
        request: BrainRequest,
        recommendation: Recommendation,
    ) -> str:
        """Record input hash, reasoning trace and output without raw private input."""

        self._require_ready()
        memory_id = str(uuid4())
        content_hash = hashlib.sha256(request.content.encode("utf-8")).hexdigest()
        started_transaction = not self.connection.in_transaction
        if started_transaction:
            self.connection.execute("BEGIN IMMEDIATE")
        try:
            self.connection.execute(
                "INSERT INTO smi_memory_records ("
                "memory_id, request_id, identity_id, task_type, content_hash, "
                "summary, output_state, signal_level, rationale_json, "
                "processing_states_json, created_at"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    memory_id,
                    request.request_id,
                    request.identity_id,
                    request.task_type,
                    content_hash,
                    recommendation.summary,
                    recommendation.output_state.value,
                    recommendation.signal_level.value,
                    json.dumps(recommendation.rationale, ensure_ascii=False),
                    json.dumps(recommendation.processing_states),
                    recommendation.created_at.isoformat(),
                ),
            )
            append_event(
                self.connection,
                actor="SMI",
                actor_type="intelligence",
                authority_level=2,
                action="SMI_REVIEWED",
                target=request.request_id,
                reason=recommendation.output_state.value,
                metadata={
                    "memory_id": memory_id,
                    "signal_level": recommendation.signal_level.value,
                    "summary": recommendation.summary,
                },
                correlation_id=request.request_id,
            )
            if started_transaction:
                self.connection.execute("COMMIT")
        except Exception:
            if started_transaction:
                self.connection.execute("ROLLBACK")
            raise
        return memory_id

    def record_kernel_result(
        self,
        result: KernelResult,
        approval_receipt_id: str | None,
    ) -> str:
        self._require_ready()
        outcome_id = str(uuid4())
        started_transaction = not self.connection.in_transaction
        if started_transaction:
            self.connection.execute("BEGIN IMMEDIATE")
        try:
            self.connection.execute(
                "INSERT INTO smi_kernel_outcomes ("
                "outcome_id, request_id, state, executed, reason, "
                "approval_receipt_id, created_at"
                ") VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    outcome_id,
                    result.request_id,
                    result.state,
                    int(result.executed),
                    result.reason,
                    approval_receipt_id,
                    utc_now().isoformat(),
                ),
            )
            append_event(
                self.connection,
                actor="Living Kernel",
                actor_type="kernel",
                authority_level=1,
                action=result.state,
                target=result.request_id,
                reason=result.reason,
                metadata={
                    "outcome_id": outcome_id,
                    "executed": result.executed,
                    "approval_receipt_id": approval_receipt_id,
                },
                correlation_id=result.request_id,
            )
            if started_transaction:
                self.connection.execute("COMMIT")
        except Exception:
            if started_transaction:
                self.connection.execute("ROLLBACK")
            raise
        return outcome_id

    def record_approval(self, receipt: ApprovalReceipt) -> tuple[int, str]:
        """Atomically consume one final signed decision for one recommendation."""

        self._require_ready()
        started_transaction = not self.connection.in_transaction
        if started_transaction:
            self.connection.execute("BEGIN IMMEDIATE")
        try:
            self.connection.execute(
                "INSERT INTO smi_approval_receipts ("
                "receipt_id, request_id, identity_id, decision, issued_at, "
                "expires_at, action_digest, consumed_at"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    receipt.receipt_id,
                    receipt.request_id,
                    receipt.identity_id,
                    receipt.decision.value,
                    receipt.issued_at.isoformat(),
                    receipt.expires_at.isoformat(),
                    receipt.action_digest,
                    utc_now().isoformat(),
                ),
            )
            event = append_event(
                self.connection,
                actor=receipt.identity_id,
                actor_type="human_authority",
                authority_level=receipt.authority_level,
                action=f"HUMAN_{receipt.decision.value}",
                target=receipt.request_id,
                reason="Signed Human Authority decision",
                metadata={"approval_receipt_id": receipt.receipt_id},
                correlation_id=receipt.request_id,
            )
            if started_transaction:
                self.connection.execute("COMMIT")
            return event
        except sqlite3.IntegrityError as exc:
            if started_transaction:
                self.connection.execute("ROLLBACK")
            raise ApprovalReceiptReplay(
                "Human Authority receipt already consumed or request already decided"
            ) from exc
        except Exception:
            if started_transaction:
                self.connection.execute("ROLLBACK")
            raise

    def status(self) -> dict[str, object]:
        ready = self.is_ready()
        memories = 0
        approvals = 0
        outcomes = 0
        audit_events = 0
        if ready:
            memories = int(
                self.connection.execute(
                    "SELECT COUNT(*) FROM smi_memory_records"
                ).fetchone()[0]
            )
            approvals = int(
                self.connection.execute(
                    "SELECT COUNT(*) FROM smi_approval_receipts"
                ).fetchone()[0]
            )
            outcomes = int(
                self.connection.execute(
                    "SELECT COUNT(*) FROM smi_kernel_outcomes"
                ).fetchone()[0]
            )
        if self.audit_ready():
            audit_events = int(
                self.connection.execute("SELECT COUNT(*) FROM audit_events").fetchone()[
                    0
                ]
            )
        return {
            "component": "HRM and JOOG MEMORY",
            "ready": ready,
            "memory_records": memories,
            "approval_receipts": approvals,
            "kernel_outcomes": outcomes,
            "audit_ready": self.audit_ready(),
            "audit_events": audit_events,
        }


def _parse_timestamp(value: str):
    from datetime import datetime

    return datetime.fromisoformat(value)
