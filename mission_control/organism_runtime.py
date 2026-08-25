"""Durable 24/7 OAP organism runtime backed by production PostgreSQL.

The runtime may schedule, lease, retry, recover and record bounded maintenance
work. It does not grant approval or execution authority. Consequential actions
remain outside this worker and must use the governed Living Kernel path.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import uuid4

from . import postgres_db

RUNTIME_MIGRATION_VERSION = "0004_organism_runtime"
ALLOWED_JOB_TYPES = frozenset({"RUNTIME_HEARTBEAT", "RUNTIME_HEALTH_PROBE"})
RUNTIME_TABLES = frozenset(
    {
        "oap_runtime_jobs",
        "oap_runtime_workers",
        "oap_runtime_schedules",
        "oap_runtime_dead_letters",
        "oap_runtime_receipts",
    }
)
RUNTIME_SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_runtime_jobs (
        job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        job_type TEXT NOT NULL,
        payload JSONB NOT NULL DEFAULT '{}'::jsonb,
        state TEXT NOT NULL DEFAULT 'QUEUED'
            CHECK (state IN ('QUEUED','RUNNING','RETRY','SUCCEEDED','DEAD_LETTER')),
        priority SMALLINT NOT NULL DEFAULT 100,
        attempts SMALLINT NOT NULL DEFAULT 0 CHECK (attempts >= 0),
        max_attempts SMALLINT NOT NULL DEFAULT 5 CHECK (max_attempts BETWEEN 1 AND 20),
        available_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        lease_owner TEXT,
        lease_expires_at TIMESTAMPTZ,
        idempotency_key TEXT NOT NULL UNIQUE,
        last_error_code TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMPTZ)""",
    """CREATE INDEX IF NOT EXISTS ix_runtime_jobs_claim
        ON oap_runtime_jobs(state, available_at, priority, created_at)""",
    """CREATE TABLE IF NOT EXISTS oap_runtime_workers (
        worker_id TEXT PRIMARY KEY,
        status TEXT NOT NULL CHECK (status IN ('ACTIVE','DRAINING','STOPPED')),
        revision TEXT NOT NULL DEFAULT 'unknown',
        started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        heartbeat_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        last_job_id UUID,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE INDEX IF NOT EXISTS ix_runtime_workers_heartbeat
        ON oap_runtime_workers(heartbeat_at DESC)""",
    """CREATE TABLE IF NOT EXISTS oap_runtime_schedules (
        schedule_id TEXT PRIMARY KEY,
        job_type TEXT NOT NULL,
        payload JSONB NOT NULL DEFAULT '{}'::jsonb,
        interval_seconds INTEGER NOT NULL CHECK (interval_seconds BETWEEN 30 AND 86400),
        enabled BOOLEAN NOT NULL DEFAULT TRUE,
        next_run_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        last_enqueued_at TIMESTAMPTZ,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE TABLE IF NOT EXISTS oap_runtime_dead_letters (
        dead_letter_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        job_id UUID NOT NULL UNIQUE REFERENCES oap_runtime_jobs(job_id),
        job_type TEXT NOT NULL,
        attempts SMALLINT NOT NULL,
        error_code TEXT NOT NULL,
        payload_digest TEXT NOT NULL,
        dead_lettered_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE TABLE IF NOT EXISTS oap_runtime_receipts (
        receipt_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        job_id UUID REFERENCES oap_runtime_jobs(job_id),
        worker_id TEXT NOT NULL,
        event_type TEXT NOT NULL,
        state TEXT NOT NULL,
        detail JSONB NOT NULL DEFAULT '{}'::jsonb,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE INDEX IF NOT EXISTS ix_runtime_receipts_created
        ON oap_runtime_receipts(created_at DESC)""",
    """INSERT INTO oap_runtime_schedules
        (schedule_id,job_type,payload,interval_seconds,enabled,next_run_at)
        VALUES
          ('organism-heartbeat','RUNTIME_HEARTBEAT','{}'::jsonb,60,TRUE,CURRENT_TIMESTAMP),
          ('organism-health','RUNTIME_HEALTH_PROBE','{}'::jsonb,300,TRUE,CURRENT_TIMESTAMP)
        ON CONFLICT (schedule_id) DO NOTHING""",
)
RUNTIME_MIGRATION_CHECKSUM = hashlib.sha256(
    "\n".join(RUNTIME_SCHEMA_STATEMENTS).encode("utf-8")
).hexdigest()


@dataclass(frozen=True, slots=True)
class RuntimeJob:
    job_id: str
    job_type: str
    payload: dict[str, Any]
    attempts: int
    max_attempts: int
    idempotency_key: str


def retry_delay_seconds(attempts: int) -> int:
    """Return bounded exponential retry delay for a completed failed attempt."""
    count = max(1, int(attempts))
    return min(900, 5 * (2 ** min(count - 1, 7)))


def payload_digest(payload: object) -> str:
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def runtime_status(*, stale_after_seconds: int = 90) -> dict[str, object]:
    """Return a read-only runtime readiness snapshot."""
    result: dict[str, object] = {
        "component": "24/7 Organism Runtime",
        "schema_ready": False,
        "worker_fresh": False,
        "queued": 0,
        "running": 0,
        "retry": 0,
        "dead_letter": 0,
        "migration": RUNTIME_MIGRATION_VERSION,
        "error": None,
        "ready": False,
        "consequential_execution": False,
    }
    base = postgres_db.postgres_status()
    if not base.get("initialized"):
        result["error"] = "base_postgres_not_ready"
        return result
    try:
        with postgres_db.connect(readonly=True) as connection:
            tables = {
                str(row[0])
                for row in connection.execute(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema='public'"
                ).fetchall()
            }
            if not RUNTIME_TABLES <= tables:
                result["error"] = "runtime_schema_pending"
                return result
            row = connection.execute(
                "SELECT checksum FROM oap_schema_migrations WHERE version=%s",
                (RUNTIME_MIGRATION_VERSION,),
            ).fetchone()
            if row is None or str(row[0]) != RUNTIME_MIGRATION_CHECKSUM:
                result["error"] = "runtime_migration_not_verified"
                return result
            result["schema_ready"] = True
            counts = dict(
                connection.execute(
                    "SELECT state,COUNT(*) FROM oap_runtime_jobs GROUP BY state"
                ).fetchall()
            )
            result["queued"] = int(counts.get("QUEUED", 0))
            result["running"] = int(counts.get("RUNNING", 0))
            result["retry"] = int(counts.get("RETRY", 0))
            result["dead_letter"] = int(counts.get("DEAD_LETTER", 0))
            fresh = connection.execute(
                """SELECT 1 FROM oap_runtime_workers
                   WHERE status='ACTIVE'
                     AND heartbeat_at >= CURRENT_TIMESTAMP - (%s * INTERVAL '1 second')
                   LIMIT 1""",
                (max(30, int(stale_after_seconds)),),
            ).fetchone()
            result["worker_fresh"] = fresh is not None
            result["ready"] = bool(result["schema_ready"] and result["worker_fresh"])
            return result
    except Exception:  # noqa: BLE001 - readiness degrades without exposing DB details.
        result["error"] = "runtime_store_unavailable"
        return result


def init_runtime_schema(*, assume_yes: bool = False, dry_run: bool = False) -> dict[str, object]:
    """Apply the runtime schema only after explicit Human Authority invocation."""
    if not assume_yes:
        raise RuntimeError("Explicit human approval required: pass --yes")
    base = postgres_db.postgres_status()
    if not base.get("initialized"):
        raise RuntimeError("Base PostgreSQL schema must be ready first")
    if dry_run:
        return {
            "dry_run": True,
            "migration": RUNTIME_MIGRATION_VERSION,
            "checksum": RUNTIME_MIGRATION_CHECKSUM,
        }
    with postgres_db.connect() as connection:
        connection.execute("SELECT pg_advisory_xact_lock(%s)", (24680261,))
        row = connection.execute(
            "SELECT checksum FROM oap_schema_migrations WHERE version=%s",
            (RUNTIME_MIGRATION_VERSION,),
        ).fetchone()
        if row is not None and str(row[0]) != RUNTIME_MIGRATION_CHECKSUM:
            raise RuntimeError("Applied runtime migration checksum mismatch")
        if row is None:
            for statement in RUNTIME_SCHEMA_STATEMENTS:
                connection.execute(statement)
            connection.execute(
                "INSERT INTO oap_schema_migrations(version,checksum) VALUES (%s,%s)",
                (RUNTIME_MIGRATION_VERSION, RUNTIME_MIGRATION_CHECKSUM),
            )
        connection.commit()
    return runtime_status()


class PostgresRuntimeStore:
    """Durable queue/scheduler store using row leases and SKIP LOCKED claims."""

    def enqueue(
        self,
        job_type: str,
        payload: dict[str, Any] | None = None,
        *,
        idempotency_key: str | None = None,
        priority: int = 100,
        max_attempts: int = 5,
    ) -> str:
        normalized = _job_type(job_type)
        body = _payload(payload or {})
        key = str(idempotency_key or uuid4()).strip()
        if not key:
            raise ValueError("idempotency_key is required")
        attempts = min(20, max(1, int(max_attempts)))
        rank = min(32767, max(-32768, int(priority)))
        with postgres_db.connect() as connection:
            job_id = self._enqueue_in_connection(
                connection,
                normalized,
                body,
                key,
                rank,
                attempts,
            )
            connection.commit()
            return job_id

    def heartbeat(
        self,
        worker_id: str,
        *,
        status: str = "ACTIVE",
        revision: str = "unknown",
        last_job_id: str | None = None,
    ) -> None:
        worker = _worker_id(worker_id)
        state = str(status).upper()
        if state not in {"ACTIVE", "DRAINING", "STOPPED"}:
            raise ValueError("invalid worker status")
        with postgres_db.connect() as connection:
            connection.execute(
                """INSERT INTO oap_runtime_workers
                   (worker_id,status,revision,heartbeat_at,last_job_id)
                   VALUES (%s,%s,%s,CURRENT_TIMESTAMP,%s)
                   ON CONFLICT (worker_id) DO UPDATE SET
                     status=EXCLUDED.status,
                     revision=EXCLUDED.revision,
                     heartbeat_at=CURRENT_TIMESTAMP,
                     last_job_id=EXCLUDED.last_job_id,
                     updated_at=CURRENT_TIMESTAMP""",
                (worker, state, str(revision or "unknown")[:120], last_job_id),
            )
            connection.commit()

    def tick_scheduler(self, *, limit: int = 20) -> int:
        """Enqueue at most one occurrence for each currently due schedule."""
        created = 0
        with postgres_db.connect() as connection:
            rows = connection.execute(
                """SELECT schedule_id,job_type,payload,interval_seconds,next_run_at
                   FROM oap_runtime_schedules
                   WHERE enabled=TRUE AND next_run_at <= CURRENT_TIMESTAMP
                   ORDER BY next_run_at
                   FOR UPDATE SKIP LOCKED LIMIT %s""",
                (min(100, max(1, int(limit))),),
            ).fetchall()
            for row in rows:
                schedule_id = str(row[0])
                job_type = _job_type(str(row[1]))
                payload = _json_object(row[2])
                interval = int(row[3])
                scheduled_for: datetime = row[4]
                key = f"schedule:{schedule_id}:{scheduled_for.isoformat()}"
                self._enqueue_in_connection(
                    connection,
                    job_type,
                    payload,
                    key,
                    100,
                    5,
                )
                connection.execute(
                    """UPDATE oap_runtime_schedules
                       SET last_enqueued_at=CURRENT_TIMESTAMP,
                           next_run_at=CURRENT_TIMESTAMP + (%s * INTERVAL '1 second'),
                           updated_at=CURRENT_TIMESTAMP
                       WHERE schedule_id=%s""",
                    (interval, schedule_id),
                )
                created += 1
            connection.commit()
        return created

    def claim(self, worker_id: str, *, lease_seconds: int = 60) -> RuntimeJob | None:
        worker = _worker_id(worker_id)
        lease = min(300, max(30, int(lease_seconds)))
        with postgres_db.connect() as connection:
            row = connection.execute(
                """WITH candidate AS (
                     SELECT job_id FROM oap_runtime_jobs
                     WHERE state IN ('QUEUED','RETRY')
                       AND available_at <= CURRENT_TIMESTAMP
                     ORDER BY priority,created_at
                     FOR UPDATE SKIP LOCKED LIMIT 1
                   )
                   UPDATE oap_runtime_jobs j SET
                     state='RUNNING', lease_owner=%s,
                     lease_expires_at=CURRENT_TIMESTAMP + (%s * INTERVAL '1 second'),
                     attempts=j.attempts+1, updated_at=CURRENT_TIMESTAMP
                   FROM candidate c WHERE j.job_id=c.job_id
                   RETURNING j.job_id,j.job_type,j.payload,j.attempts,
                             j.max_attempts,j.idempotency_key""",
                (worker, lease),
            ).fetchone()
            connection.commit()
        if row is None:
            return None
        return RuntimeJob(
            job_id=str(row[0]),
            job_type=str(row[1]),
            payload=_json_object(row[2]),
            attempts=int(row[3]),
            max_attempts=int(row[4]),
            idempotency_key=str(row[5]),
        )

    def complete(self, job: RuntimeJob, worker_id: str, detail: dict[str, Any]) -> None:
        worker = _worker_id(worker_id)
        safe_detail = _payload(detail)
        with postgres_db.connect() as connection:
            row = connection.execute(
                """UPDATE oap_runtime_jobs SET
                     state='SUCCEEDED',lease_owner=NULL,lease_expires_at=NULL,
                     completed_at=CURRENT_TIMESTAMP,updated_at=CURRENT_TIMESTAMP
                   WHERE job_id=%s AND state='RUNNING' AND lease_owner=%s
                   RETURNING job_id""",
                (job.job_id, worker),
            ).fetchone()
            if row is None:
                raise RuntimeError("job lease lost before completion")
            self._receipt(connection, job.job_id, worker, "JOB_SUCCEEDED", "SUCCEEDED", safe_detail)
            _append_runtime_audit(
                connection,
                worker_id=worker,
                action="RUNTIME_JOB_SUCCEEDED",
                job_id=job.job_id,
                metadata={"job_type": job.job_type, "attempts": job.attempts, **safe_detail},
            )
            connection.commit()

    def fail(self, job: RuntimeJob, worker_id: str, *, error_code: str) -> str:
        worker = _worker_id(worker_id)
        error = _error_code(error_code)
        with postgres_db.connect() as connection:
            row = connection.execute(
                """SELECT attempts,max_attempts,payload,job_type
                   FROM oap_runtime_jobs
                   WHERE job_id=%s AND state='RUNNING' AND lease_owner=%s
                   FOR UPDATE""",
                (job.job_id, worker),
            ).fetchone()
            if row is None:
                raise RuntimeError("job lease lost before failure recording")
            attempts = int(row[0])
            max_attempts = int(row[1])
            body = _json_object(row[2])
            job_type = str(row[3])
            if attempts >= max_attempts:
                state = "DEAD_LETTER"
                connection.execute(
                    """UPDATE oap_runtime_jobs SET state='DEAD_LETTER',
                       lease_owner=NULL,lease_expires_at=NULL,last_error_code=%s,
                       completed_at=CURRENT_TIMESTAMP,updated_at=CURRENT_TIMESTAMP
                       WHERE job_id=%s""",
                    (error, job.job_id),
                )
                connection.execute(
                    """INSERT INTO oap_runtime_dead_letters
                       (job_id,job_type,attempts,error_code,payload_digest)
                       VALUES (%s,%s,%s,%s,%s) ON CONFLICT (job_id) DO NOTHING""",
                    (job.job_id, job_type, attempts, error, payload_digest(body)),
                )
            else:
                state = "RETRY"
                delay = retry_delay_seconds(attempts)
                connection.execute(
                    """UPDATE oap_runtime_jobs SET state='RETRY',
                       lease_owner=NULL,lease_expires_at=NULL,last_error_code=%s,
                       available_at=CURRENT_TIMESTAMP + (%s * INTERVAL '1 second'),
                       updated_at=CURRENT_TIMESTAMP WHERE job_id=%s""",
                    (error, delay, job.job_id),
                )
            self._receipt(
                connection,
                job.job_id,
                worker,
                "JOB_FAILED",
                state,
                {"error_code": error, "attempts": attempts},
            )
            _append_runtime_audit(
                connection,
                worker_id=worker,
                action="RUNTIME_JOB_DEAD_LETTERED" if state == "DEAD_LETTER" else "RUNTIME_JOB_RETRY",
                job_id=job.job_id,
                metadata={"job_type": job_type, "attempts": attempts, "error_code": error},
            )
            connection.commit()
            return state

    def recover_stale(self, *, limit: int = 50) -> int:
        """Release expired leases so crashed-worker jobs can be retried or dead-lettered."""
        recovered = 0
        with postgres_db.connect() as connection:
            rows = connection.execute(
                """SELECT job_id,job_type,payload,attempts,max_attempts
                   FROM oap_runtime_jobs
                   WHERE state='RUNNING' AND lease_expires_at < CURRENT_TIMESTAMP
                   ORDER BY lease_expires_at FOR UPDATE SKIP LOCKED LIMIT %s""",
                (min(200, max(1, int(limit))),),
            ).fetchall()
            for row in rows:
                job_id = str(row[0])
                job_type = str(row[1])
                body = _json_object(row[2])
                attempts = int(row[3])
                max_attempts = int(row[4])
                if attempts >= max_attempts:
                    state = "DEAD_LETTER"
                    connection.execute(
                        """UPDATE oap_runtime_jobs SET state='DEAD_LETTER',
                           lease_owner=NULL,lease_expires_at=NULL,
                           last_error_code='lease_expired',completed_at=CURRENT_TIMESTAMP,
                           updated_at=CURRENT_TIMESTAMP WHERE job_id=%s""",
                        (job_id,),
                    )
                    connection.execute(
                        """INSERT INTO oap_runtime_dead_letters
                           (job_id,job_type,attempts,error_code,payload_digest)
                           VALUES (%s,%s,%s,'lease_expired',%s)
                           ON CONFLICT (job_id) DO NOTHING""",
                        (job_id, job_type, attempts, payload_digest(body)),
                    )
                else:
                    state = "RETRY"
                    connection.execute(
                        """UPDATE oap_runtime_jobs SET state='RETRY',
                           lease_owner=NULL,lease_expires_at=NULL,
                           last_error_code='lease_expired',available_at=CURRENT_TIMESTAMP,
                           updated_at=CURRENT_TIMESTAMP WHERE job_id=%s""",
                        (job_id,),
                    )
                self._receipt(
                    connection,
                    job_id,
                    "runtime-recovery",
                    "LEASE_RECOVERED",
                    state,
                    {"attempts": attempts},
                )
                recovered += 1
            connection.commit()
        return recovered

    @staticmethod
    def _enqueue_in_connection(
        connection: Any,
        job_type: str,
        payload: dict[str, Any],
        idempotency_key: str,
        priority: int,
        max_attempts: int,
    ) -> str:
        row = connection.execute(
            """INSERT INTO oap_runtime_jobs
               (job_type,payload,idempotency_key,priority,max_attempts)
               VALUES (%s,%s::jsonb,%s,%s,%s)
               ON CONFLICT (idempotency_key) DO UPDATE SET
                 idempotency_key=EXCLUDED.idempotency_key
               RETURNING job_id""",
            (job_type, json.dumps(payload), idempotency_key, priority, max_attempts),
        ).fetchone()
        return str(row[0])

    @staticmethod
    def _receipt(
        connection: Any,
        job_id: str,
        worker_id: str,
        event_type: str,
        state: str,
        detail: dict[str, Any],
    ) -> None:
        connection.execute(
            """INSERT INTO oap_runtime_receipts
               (job_id,worker_id,event_type,state,detail)
               VALUES (%s,%s,%s,%s,%s::jsonb)""",
            (job_id, worker_id, event_type, state, json.dumps(detail)),
        )


def _append_runtime_audit(
    connection: Any,
    *,
    worker_id: str,
    action: str,
    job_id: str,
    metadata: dict[str, Any],
) -> None:
    """Append to the existing production hash chain using its canonical algorithm."""
    connection.execute("SELECT pg_advisory_xact_lock(%s)", (24680259,))
    previous = connection.execute(
        "SELECT curr_hash FROM audit_events ORDER BY event_seq DESC LIMIT 1"
    ).fetchone()
    prev_hash = str(previous[0]) if previous else "GENESIS"
    safe_metadata = {"runtime": True, "job_id": job_id, **_payload(metadata)}
    canonical = json.dumps(safe_metadata, sort_keys=True, separators=(",", ":"))
    curr_hash = hashlib.sha256((prev_hash + canonical).encode()).hexdigest()
    connection.execute(
        """INSERT INTO audit_events
           (prev_hash,curr_hash,actor_id,actor_type,authority_level,
            action,target,reason,correlation_id,metadata)
           VALUES (%s,%s,%s,'SYSTEM',NULL,%s,%s,%s,%s,%s::jsonb)""",
        (
            prev_hash,
            curr_hash,
            worker_id,
            action,
            job_id,
            "Bounded 24/7 organism runtime event",
            str(uuid4()),
            canonical,
        ),
    )


def _job_type(value: object) -> str:
    job_type = str(value or "").strip().upper()
    if job_type not in ALLOWED_JOB_TYPES:
        raise PermissionError("runtime job type is not allow-listed")
    return job_type


def _worker_id(value: object) -> str:
    worker = str(value or "").strip()[:120]
    if not worker:
        raise ValueError("worker_id is required")
    return worker


def _error_code(value: object) -> str:
    error = str(value or "runtime_error").strip().casefold()[:120]
    return error or "runtime_error"


def _payload(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError("runtime payload must be an object")
    try:
        encoded = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("runtime payload must be valid JSON") from exc
    if len(encoded) > 16000:
        raise ValueError("runtime payload is too large")
    return json.loads(encoded)


def _json_object(value: object) -> dict[str, Any]:
    if isinstance(value, dict):
        return _payload(value)
    if isinstance(value, str):
        parsed = json.loads(value)
        return _payload(parsed)
    raise ValueError("stored runtime payload is invalid")
