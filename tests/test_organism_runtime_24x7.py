from __future__ import annotations

from pathlib import Path

import pytest

from mission_control import organism_runtime, organism_worker
from mission_control.organism_runtime import RuntimeJob


def test_runtime_job_allowlist_cannot_be_used_as_execution_bypass():
    assert organism_runtime.ALLOWED_JOB_TYPES == {
        "RUNTIME_HEARTBEAT",
        "RUNTIME_HEALTH_PROBE",
    }
    with pytest.raises(PermissionError, match="not allow-listed"):
        organism_runtime._job_type("promote_evolution_candidate")
    with pytest.raises(PermissionError, match="not allow-listed"):
        organism_runtime._job_type("deploy")


def test_retry_backoff_is_exponential_and_bounded():
    assert organism_runtime.retry_delay_seconds(1) == 5
    assert organism_runtime.retry_delay_seconds(2) == 10
    assert organism_runtime.retry_delay_seconds(3) == 20
    assert organism_runtime.retry_delay_seconds(8) == 640
    assert organism_runtime.retry_delay_seconds(20) == 640


def test_payload_digest_is_stable_and_payload_validation_fails_closed():
    left = organism_runtime.payload_digest({"b": 2, "a": 1})
    right = organism_runtime.payload_digest({"a": 1, "b": 2})
    assert left == right
    assert len(left) == 64
    with pytest.raises(ValueError, match="valid JSON"):
        organism_runtime._payload({"bad": float("nan")})
    with pytest.raises(ValueError, match="too large"):
        organism_runtime._payload({"blob": "x" * 17000})


def test_runtime_schema_requires_explicit_human_invocation(monkeypatch):
    monkeypatch.setattr(
        organism_runtime.postgres_db,
        "postgres_status",
        lambda: {"initialized": True},
    )
    with pytest.raises(RuntimeError, match="Explicit human approval"):
        organism_runtime.init_runtime_schema()


def test_runtime_status_fails_closed_when_base_database_is_not_ready(monkeypatch):
    monkeypatch.setattr(
        organism_runtime.postgres_db,
        "postgres_status",
        lambda: {"initialized": False},
    )
    status = organism_runtime.runtime_status()
    assert status["ready"] is False
    assert status["schema_ready"] is False
    assert status["worker_fresh"] is False
    assert status["error"] == "base_postgres_not_ready"
    assert status["consequential_execution"] is False


def test_worker_refuses_to_start_without_verified_runtime_schema(monkeypatch):
    monkeypatch.setattr(
        organism_worker,
        "runtime_status",
        lambda: {"schema_ready": False, "error": "runtime_schema_pending"},
    )
    assert organism_worker.run() == 2


def test_worker_handlers_are_bounded_nonconsequential(monkeypatch):
    job = RuntimeJob(
        job_id="00000000-0000-0000-0000-000000000001",
        job_type="RUNTIME_HEARTBEAT",
        payload={},
        attempts=1,
        max_attempts=5,
        idempotency_key="test",
    )
    heartbeat = organism_worker._heartbeat_job(job)
    assert heartbeat["consequential_action"] is False

    monkeypatch.setattr(
        organism_worker.postgres_db,
        "postgres_status",
        lambda: {"initialized": False},
    )
    health = organism_worker._health_probe(job)
    assert health["consequential_action"] is False
    assert health["database_ready"] is False
    assert health["human_authority_present"] is False


def test_runtime_migration_contains_durable_queue_recovery_and_receipts():
    sql = "\n".join(organism_runtime.RUNTIME_SCHEMA_STATEMENTS)
    assert "oap_runtime_jobs" in sql
    assert "oap_runtime_workers" in sql
    assert "oap_runtime_schedules" in sql
    assert "oap_runtime_dead_letters" in sql
    assert "oap_runtime_receipts" in sql
    assert "DEAD_LETTER" in sql
    assert len(organism_runtime.RUNTIME_MIGRATION_CHECKSUM) == 64


def test_free_mode_does_not_provision_a_paid_background_worker():
    content = Path("render.yaml").read_text()
    assert "type: worker" not in content
    assert "name: oap-organism-runtime" not in content
    assert "name: oap-smi" in content
    assert "plan: free" in content
    assert "runtime: image" in content
    assert 'value: "smi_gateway:app"' in content


@pytest.mark.parametrize(
    ("active", "fresh", "receipts", "expected_state", "expected_ready", "expected_execution"),
    [
        (1, 0, 0, "stale_active", False, False),
        (0, 0, 0, "not_running", False, False),
        (1, 1, 0, "fresh", True, False),
        (1, 1, 2, "fresh", True, True),
    ],
)
def test_worker_readiness_is_heartbeat_based_not_active_flag(
    monkeypatch, active, fresh, receipts, expected_state, expected_ready, expected_execution,
):
    from contextlib import contextmanager

    class Rows:
        def __init__(self, *, one=None, many=None):
            self.one, self.many = one, many

        def fetchone(self):
            return self.one

        def fetchall(self):
            return self.many

    class Connection:
        def execute(self, sql, params=()):
            if "information_schema.tables" in sql:
                return Rows(many=[(name,) for name in organism_runtime.RUNTIME_TABLES])
            if "SELECT checksum FROM oap_schema_migrations" in sql:
                return Rows(one=(organism_runtime.RUNTIME_MIGRATION_CHECKSUM,))
            if "GROUP BY state" in sql:
                return Rows(many=[("SUCCEEDED", 2)])
            if "COUNT(*) FILTER (WHERE status='ACTIVE')" in sql:
                assert params == (90, "%-inference")
                assert "WHERE worker_id NOT LIKE %s" in sql
                assert "heartbeat_at <= CURRENT_TIMESTAMP" in sql
                return Rows(one=(active, fresh))
            if "COUNT(DISTINCT j.job_id)" in sql:
                assert params == (90, "%-inference")
                assert "JOB_SUCCEEDED" in sql
                assert "INTERVAL '15 minutes'" in sql
                assert "w.status = 'ACTIVE'" in sql
                return Rows(one=(receipts,))
            raise AssertionError("Unexpected SQL in status check")

    @contextmanager
    def connect(*, readonly=False):
        assert readonly is True
        yield Connection()

    monkeypatch.setattr(
        organism_runtime.postgres_db, "postgres_status",
        lambda: {"initialized": True},
    )
    monkeypatch.setattr(organism_runtime.postgres_db, "connect", connect)
    result = organism_runtime.runtime_status()
    assert result["schema_ready"] is True
    assert result["worker_state"] == expected_state
    assert result["worker_fresh"] is expected_ready
    assert result["ready"] is expected_ready
    assert result["recent_successful_job_receipts"] == receipts
    assert result["native_job_execution_observed"] is expected_execution
    assert result["consequential_execution"] is False


def test_queue_duplicate_key_only_reuses_identical_job():
    class Connection:
        def __init__(self, row):
            self.row = row

        def execute(self, sql, params):
            assert "oap_runtime_jobs.job_type=EXCLUDED.job_type" in sql
            assert "oap_runtime_jobs.payload=EXCLUDED.payload" in sql
            assert "oap_runtime_jobs.priority=EXCLUDED.priority" in sql
            assert "oap_runtime_jobs.max_attempts=EXCLUDED.max_attempts" in sql
            assert params == ("RUNTIME_HEARTBEAT", "{}", "same-key", 100, 5)
            return self

        def fetchone(self):
            return self.row

    enqueue = organism_runtime.PostgresRuntimeStore._enqueue_in_connection
    assert enqueue(Connection(("job-id",)), "RUNTIME_HEARTBEAT", {}, "same-key", 100, 5) == "job-id"
    with pytest.raises(ValueError, match="idempotency_key_conflicts"):
        enqueue(Connection(None), "RUNTIME_HEARTBEAT", {}, "same-key", 100, 5)


def test_stale_attempt_cannot_complete_or_fail_reassigned_job(monkeypatch):
    from contextlib import contextmanager

    job = RuntimeJob(
        job_id="00000000-0000-0000-0000-000000000001",
        job_type="RUNTIME_HEARTBEAT", payload={}, attempts=1,
        max_attempts=5, idempotency_key="same-key",
    )

    class Connection:
        def execute(self, sql, params):
            assert "AND attempts=%s" in sql
            assert params == (job.job_id, "worker-one", job.attempts)
            return self

        def fetchone(self):
            return None

    @contextmanager
    def connect():
        yield Connection()

    monkeypatch.setattr(organism_runtime.postgres_db, "connect", connect)
    store = organism_runtime.PostgresRuntimeStore()
    with pytest.raises(RuntimeError, match="job lease lost"):
        store.complete(job, "worker-one", {})
    with pytest.raises(RuntimeError, match="job lease lost"):
        store.fail(job, "worker-one", error_code="test")


def test_worker_records_lost_lease_without_claiming_failure():
    job = RuntimeJob(
        job_id="00000000-0000-0000-0000-000000000001",
        job_type="RUNTIME_HEARTBEAT", payload={}, attempts=1,
        max_attempts=5, idempotency_key="test",
    )

    class Store:
        def fail(self, job, worker_id, *, error_code):
            raise organism_runtime.JobLeaseLost("job lease lost")

    assert organism_worker._record_failure(
        Store(), job, "worker-one", error_code="test",
    ) == "LEASE_LOST"


def test_worker_does_not_swallow_unrelated_database_failure():
    class Store:
        def fail(self, job, worker_id, *, error_code):
            raise RuntimeError("database unavailable")

    with pytest.raises(RuntimeError, match="database unavailable"):
        organism_worker._record_failure(
            Store(), None, "worker-one", error_code="test",
        )


@pytest.mark.parametrize(("attempts", "expected_state"), [(2, "RETRY"), (5, "DEAD_LETTER")])
def test_expired_lease_recovery_uses_bounded_backoff_or_dead_letter(
    monkeypatch, attempts, expected_state,
):
    from contextlib import contextmanager

    calls = []
    receipts = []

    class Connection:
        def execute(self, sql, params):
            calls.append((sql, params))
            return self

        def fetchall(self):
            return [("job-one", "RUNTIME_HEARTBEAT", {}, attempts, 5)]

        def commit(self):
            pass

    @contextmanager
    def connect():
        yield Connection()

    monkeypatch.setattr(organism_runtime.postgres_db, "connect", connect)
    store = organism_runtime.PostgresRuntimeStore()
    monkeypatch.setattr(store, "_receipt", lambda *args: receipts.append(args))
    assert store.recover_stale() == 1
    assert receipts[0][3:5] == ("LEASE_RECOVERED", expected_state)
    if expected_state == "RETRY":
        assert "INTERVAL '1 second'" in calls[1][0]
        assert calls[1][1] == (10, "job-one")
    else:
        assert "DEAD_LETTER" in calls[1][0]
        assert "oap_runtime_dead_letters" in calls[2][0]
