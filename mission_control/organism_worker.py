"""Always-on OAP organism worker with graceful shutdown and bounded handlers."""
from __future__ import annotations

import json
import os
import signal
import socket
import threading
import time
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from . import (
    oap_core_autonomy,
    organism_autonomy,
    postgres_db,
    smi_runtime_autonomy,
)
from .organism_runtime import PostgresRuntimeStore, RuntimeJob, runtime_status

Handler = Callable[[RuntimeJob], dict[str, Any]]


def _heartbeat_job(job: RuntimeJob) -> dict[str, Any]:
    del job
    return {
        "kind": "organism_heartbeat",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "oap_core_autonomy": oap_core_autonomy.status(),
        "smi_autonomy": smi_runtime_autonomy.status(),
        "organism_autonomy": organism_autonomy.status(),
        "human_authority_final": True,
        "independent_execution": False,
        "consequential_action": False,
    }


def _health_probe(job: RuntimeJob) -> dict[str, Any]:
    del job
    database = postgres_db.postgres_status()
    human_authority_present = False
    if database.get("initialized"):
        with postgres_db.connect(readonly=True) as connection:
            human_authority_present = (
                connection.execute(
                    """SELECT 1 FROM oap_identities i
                       JOIN oap_identity_roles ir ON ir.identity_id=i.identity_id
                       JOIN oap_roles r ON r.role_id=ir.role_id
                       JOIN oap_role_permissions rp ON rp.role_id=r.role_id
                       WHERE i.status='ACTIVE'
                         AND i.identity_type='HUMAN_AUTHORITY'
                         AND r.authority_level=0
                         AND rp.permission_id='APPROVE_RECOMMENDATION'
                       LIMIT 1"""
                ).fetchone()
                is not None
            )
    oap_core_cycle = oap_core_autonomy.run_cycle()
    smi_cycle = smi_runtime_autonomy.run_cycle()
    organism_cycle = organism_autonomy.run_cycle()
    return {
        "kind": "runtime_health_probe",
        "database_ready": bool(database.get("initialized")),
        "human_authority_present": human_authority_present,
        "oap_core_autonomy": oap_core_cycle,
        "smi_autonomy": smi_cycle,
        "organism_autonomy": organism_cycle,
        "human_authority_final": True,
        "independent_execution": False,
        "consequential_action": False,
    }


HANDLERS: dict[str, Handler] = {
    "RUNTIME_HEARTBEAT": _heartbeat_job,
    "RUNTIME_HEALTH_PROBE": _health_probe,
}


def _log(event: str, **values: object) -> None:
    payload = {"event": event, **values}
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")), flush=True)


def _worker_id() -> str:
    configured = os.environ.get("OAP_WORKER_ID", "").strip()
    if configured:
        return configured[:120]
    return f"{socket.gethostname()}:{os.getpid()}"[:120]


def _positive_seconds(name: str, default: float, minimum: float, maximum: float) -> float:
    try:
        value = float(os.environ.get(name, str(default)))
    except ValueError:
        value = default
    return min(maximum, max(minimum, value))


def run() -> int:
    """Run until SIGTERM/SIGINT; finish the current bounded job before exit."""
    status = runtime_status()
    if not status.get("schema_ready"):
        _log("runtime_worker_refused", reason=status.get("error", "runtime_schema_not_ready"))
        return 2

    store = PostgresRuntimeStore()
    worker_id = _worker_id()
    revision = os.environ.get(
        "RENDER_GIT_COMMIT", os.environ.get("OAP_ENV_REVISION", "unknown")
    )[:120]
    poll_seconds = _positive_seconds("OAP_WORKER_POLL_SECONDS", 2.0, 0.5, 30.0)
    heartbeat_seconds = _positive_seconds(
        "OAP_WORKER_HEARTBEAT_SECONDS", 15.0, 5.0, 60.0
    )
    scheduler_seconds = _positive_seconds(
        "OAP_WORKER_SCHEDULER_SECONDS", 5.0, 1.0, 60.0
    )
    recovery_seconds = _positive_seconds(
        "OAP_WORKER_RECOVERY_SECONDS", 30.0, 10.0, 300.0
    )
    lease_seconds = int(
        _positive_seconds("OAP_WORKER_LEASE_SECONDS", 60.0, 30.0, 300.0)
    )
    stop_event = threading.Event()

    def request_stop(signum: int, frame: object) -> None:
        del frame
        _log("runtime_worker_draining", worker_id=worker_id, signal=signum)
        stop_event.set()
        try:
            store.heartbeat(worker_id, status="DRAINING", revision=revision)
        except Exception:  # noqa: BLE001 - signal path must remain bounded.
            _log("runtime_worker_drain_heartbeat_failed", worker_id=worker_id)

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)

    last_heartbeat = 0.0
    last_scheduler = 0.0
    last_recovery = 0.0
    last_job_id: str | None = None
    store.heartbeat(worker_id, status="ACTIVE", revision=revision)
    _log(
        "runtime_worker_started",
        worker_id=worker_id,
        revision=revision,
        independent_authority=False,
        allowed_job_types=sorted(HANDLERS),
        oap_core_autonomy=oap_core_autonomy.status(),
        smi_autonomy=smi_runtime_autonomy.status(),
        organism_autonomy=organism_autonomy.status(),
    )

    try:
        while not stop_event.is_set():
            now = time.monotonic()
            if now - last_heartbeat >= heartbeat_seconds:
                store.heartbeat(
                    worker_id,
                    status="ACTIVE",
                    revision=revision,
                    last_job_id=last_job_id,
                )
                last_heartbeat = now
            if now - last_recovery >= recovery_seconds:
                recovered = store.recover_stale()
                if recovered:
                    _log("runtime_stale_leases_recovered", count=recovered)
                last_recovery = now
            if now - last_scheduler >= scheduler_seconds:
                scheduled = store.tick_scheduler()
                if scheduled:
                    _log("runtime_jobs_scheduled", count=scheduled)
                last_scheduler = now

            job = store.claim(worker_id, lease_seconds=lease_seconds)
            if job is None:
                stop_event.wait(poll_seconds)
                continue
            last_job_id = job.job_id
            handler = HANDLERS.get(job.job_type)
            if handler is None:
                state = store.fail(job, worker_id, error_code="handler_not_allowlisted")
                _log(
                    "runtime_job_failed",
                    job_id=job.job_id,
                    job_type=job.job_type,
                    state=state,
                )
                continue
            try:
                result = handler(job)
                if result.get("consequential_action") is not False:
                    raise PermissionError("runtime handler crossed authority boundary")
                store.complete(job, worker_id, result)
                _log(
                    "runtime_job_succeeded",
                    job_id=job.job_id,
                    job_type=job.job_type,
                )
            except Exception as exc:  # noqa: BLE001 - failure becomes retry/DLQ receipt.
                error_code = f"{type(exc).__name__.casefold()}"[:120]
                state = store.fail(job, worker_id, error_code=error_code)
                _log(
                    "runtime_job_failed",
                    job_id=job.job_id,
                    job_type=job.job_type,
                    state=state,
                    error_code=error_code,
                )
    finally:
        try:
            store.heartbeat(
                worker_id,
                status="STOPPED",
                revision=revision,
                last_job_id=last_job_id,
            )
        finally:
            _log("runtime_worker_stopped", worker_id=worker_id)
    return 0


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
