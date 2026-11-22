"""Founder-triggered, bounded self-healing for the existing OAP runtime queue.

This is not an autonomous code patcher, production deployment service, or
approval engine. It reuses the canonical PostgreSQL job store and its audited
stale-lease and due-schedule recovery operations. Missing proof fails closed.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from .organism_runtime import PostgresRuntimeStore, runtime_status

# A single Founder action cannot start an unbounded worker or flood the queue.
MAX_STALE_RECOVERY = 10
MAX_DUE_SCHEDULES = 5
_SAFE_KEYS = ("schema_ready", "worker_fresh", "queued", "running",
              "retry", "dead_letter", "ready", "error", "migration")
_ALLOWED_ERRORS = frozenset((
    None, "base_postgres_not_ready", "runtime_schema_pending",
    "runtime_migration_not_verified", "runtime_store_unavailable",
))


def _safe_status(raw: object) -> dict[str, Any]:
    """Never expose private worker, database, or authentication details."""
    source = raw if isinstance(raw, Mapping) else {}
    safe = {name: source.get(name) for name in _SAFE_KEYS}
    if safe["error"] not in _ALLOWED_ERRORS:
        safe["error"] = "runtime_status_unknown"
    return safe


def repair_runtime(
    *,
    observe: Callable[[], object] = runtime_status,
    store_factory: Callable[[], Any] = PostgresRuntimeStore,
) -> dict[str, Any]:
    """Repair ONLY expired job leases and due internal schedules.

    Every queue mutation is handled by the existing transactional store, which
    records its normal receipts. The returned snapshot is not an independent
    receipt check and may never be treated as production Green.
    """
    result: dict[str, Any] = {
        "component": "SMI Bounded Auto Repair",
        "scope": "runtime_queue_only",
        "state": "UNKNOWN",
        "error": None,
        "recovered_stale_leases": 0,
        "enqueued_due_schedules": 0,
        "before": None,
        "after": None,
        "readback_available": False,
        "execution_performed": False,
        "safe_runtime_mutation_only": True,
        "consequential_action": False,
        "independent_approval": False,
        "code_patch_performed": False,
        "deployment_performed": False,
        "payment_performed": False,
        "permission_change_performed": False,
        "guardian_hrm_bypassed": False,
        "production_green": False,
        "founder_final": True,
        "remaining": (),
    }
    try:
        before = _safe_status(observe())
        result["before"] = before
        if before["schema_ready"] is not True:
            return {
                **result, "state": "BLOCKED", "error": "runtime_schema_unverified",
                "remaining": ("verify_database_and_runtime_schema",),
            }
        if before["worker_fresh"] is not True or before["ready"] is not True:
            return {
                **result, "state": "BLOCKED", "error": "worker_not_live",
                "remaining": ("activate_existing_authorised_worker",),
            }

        store = store_factory()
        # Expired leases are safe to reclaim transactionally; jobs that have
        # exhausted retries are dead-lettered by the canonical store.
        recovered = store.recover_stale(limit=MAX_STALE_RECOVERY)
        result["recovered_stale_leases"] = int(recovered)
        result["execution_performed"] = result["recovered_stale_leases"] > 0
        # The existing scheduler enqueues only allow-listed internal job types
        # and uses transaction/locking plus idempotency keys.
        scheduled = store.tick_scheduler(limit=MAX_DUE_SCHEDULES)
        result["enqueued_due_schedules"] = int(scheduled)
        result["execution_performed"] |= result["enqueued_due_schedules"] > 0

        after = _safe_status(observe())
        result["after"] = after
        result["readback_available"] = (
            after["schema_ready"] is True and after["worker_fresh"] is True
        )
        remaining = []
        if not result["readback_available"]:
            remaining.append("worker_or_schema_readback_missing")
        if isinstance(after["dead_letter"], int) and after["dead_letter"] > 0:
            remaining.append("dead_letter_requires_review")
        result["remaining"] = tuple(remaining)
        result["state"] = (
            "RECOVERY_APPLIED_PENDING_JOB_PROOF"
            if result["execution_performed"]
            else "REVIEW_REQUIRED" if remaining
            else "NO_SAFE_REPAIR_NEEDED"
        )
        return result
    except (Exception,):  # noqa: BLE001 - never leak internal store details
        return {
            **result, "state": "UNKNOWN", "error": "runtime_repair_unavailable",
            "remaining": ("inspect_runtime_worker_and_database",),
        }
