"""Only real, manually authorised routing receipt runs; no availability bypass."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "oap-routing-live-recovery.yml"
ROUTE_GATE = ROOT / "scripts" / "routing_live_green_gate.py"


def test_live_recovery_is_one_manual_proof_not_scheduled_retries():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "\non:\n  workflow_dispatch:\n" in workflow
    triggers = workflow.split("\non:\n", 1)[1].split("\npermissions:", 1)[0]
    assert "push:" not in triggers
    assert "pull_request:" not in triggers
    assert "schedule:" not in triggers
    assert "concurrency:" in workflow
    assert "cancel-in-progress: false" in workflow
    assert "contents: read" in workflow
    assert "timeout-minutes: 5" in workflow
    assert "ref: ${{ github.sha }}" in workflow


def test_real_gate_is_mandatory_and_failure_receipts_preserved():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    source = ROUTE_GATE.read_text(encoding="utf-8")
    assert "python3 -u scripts/routing_live_green_gate.py" in workflow
    assert "set -euo pipefail" in workflow
    assert "continue-on-error:" not in workflow
    assert "if: always()" in workflow
    assert "receipt.jsonl" in workflow
    assert "source.sha" in workflow
    assert "uses: actions/upload-artifact@v4" in workflow
    assert "trigger_deploy" not in workflow
    assert "deploy/render" not in workflow
    assert "TOTAL_REQUESTS = 20" in source
    assert "WORKERS = 4" in source
    assert "P95_LIMIT_SECONDS = 6.0" in source
    assert 'OAP_OSRM_BASE_URL: ${{ vars.OAP_OSRM_BASE_URL }}' in workflow
    assert 'OAP_OSRM_ALLOWED_HOSTS: ${{ vars.OAP_OSRM_ALLOWED_HOSTS }}' in workflow
    assert 'OAP_ROUTING_OWNED_HOSTS: ${{ vars.OAP_ROUTING_OWNED_HOSTS }}' in workflow
    assert '_ROUTING_BASE_VAR = "OAP_OSRM_BASE_URL"' in source
    assert 'def _configured_base()' in source
    assert 'if host not in allowed or host not in owned:' in source
    assert 'BASE = "https://' not in source
    assert 'if not warmup.get("ready")' in source
