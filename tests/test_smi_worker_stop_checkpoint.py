"""Exact-source safety contract for the existing durable SMI worker."""
from pathlib import Path

from mission_control import organism_worker

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "mission_control" / "organism_worker.py").read_text(encoding="utf-8")


def test_existing_maintenance_worker_only_runs_allowlisted_read_only_handlers():
    assert set(organism_worker.HANDLERS) == {
        "RUNTIME_HEARTBEAT",
        "RUNTIME_HEALTH_PROBE",
    }
    assert "independent_execution" in SOURCE
    assert '"consequential_action": False' in SOURCE


def test_worker_checks_stop_and_isolation_before_and_after_handler():
    checkpoint = 'if stop_event.is_set() or store.worker_state(worker_id) != "ACTIVE":'
    assert SOURCE.count(checkpoint) == 2
    before = SOURCE.index('error_code="worker_stop_before_handler"')
    handler = SOURCE.index("result = handler(job)")
    after = SOURCE.index('error_code="worker_stop_after_handler"')
    complete = SOURCE.index("store.complete(job, worker_id, result)")
    assert before < handler < after < complete
    assert '"LEASE_ALREADY_RELEASED"' in SOURCE
    assert 'stop_event.set()' in SOURCE


def test_stop_checkpoint_reuses_durable_retry_and_does_not_claim_green():
    assert "store.fail(" in SOURCE
    assert '"runtime_job_interrupted"' in SOURCE
    assert 'phase="before_handler"' in SOURCE
    assert 'phase="after_handler"' in SOURCE
    assert "execution_granted = True" not in SOURCE
    assert "approval_granted = True" not in SOURCE
