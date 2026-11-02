"""Boundary checks for SMI GitHub intake integration in the existing worker."""
from pathlib import Path


WORKER = Path("mission_control/organism_worker.py").read_text()


def test_github_intake_reuses_existing_health_probe_no_new_scheduler():
    assert 'smi_github_failure_evidence.discover_recent_failed_runs(' in WORKER
    assert 'smi_github_failure_evidence.inspect_failed_run(' in WORKER
    assert '"RUNTIME_HEALTH_PROBE": _health_probe' in WORKER
    assert '"GITHUB_REPAIR"' not in WORKER


def test_github_intake_requires_dedicated_read_token_and_stays_read_only():
    assert 'os.environ.get("OAP_SMI_GITHUB_READ_TOKEN", "")' in WORKER
    assert 'if github_token:' in WORKER
    assert '"error": "not_configured"' in WORKER
    assert '"github_failure_evidence": github_evidence' in WORKER
    assert '"independent_execution": False' in WORKER
    assert '"human_authority_final": True' in WORKER
