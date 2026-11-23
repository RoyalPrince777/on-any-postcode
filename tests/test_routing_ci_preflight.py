from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import routing_ci_preflight, routing_live_green_gate

@pytest.fixture(autouse=True)
def configure_origin(monkeypatch):
    monkeypatch.setattr(routing_live_green_gate, "BASE", "https://routing.example.test")
    monkeypatch.setenv("OAP_OSRM_ALLOWED_HOSTS", "routing.example.test")
    monkeypatch.setenv("OAP_ROUTING_OWNED_HOSTS", "routing.example.test")


def test_no_origin_is_reported_unknown_not_live_green(monkeypatch):
    monkeypatch.setattr(routing_live_green_gate, "BASE", "")
    receipt = routing_ci_preflight.readiness()
    assert receipt["configured_for_live_probe"] is False
    assert receipt["proof_state"] == "UNKNOWN_LOCKED"
    assert receipt["failure_type"] == "missing_https_origin"
    assert receipt["live_probe_executed"] is False
    assert receipt["production_routing_ready"] is False


def test_unapproved_origin_does_not_trigger_live_probe(monkeypatch):
    monkeypatch.setenv("OAP_ROUTING_OWNED_HOSTS", "")
    receipt = routing_ci_preflight.readiness()
    assert receipt["configured_for_live_probe"] is False
    assert receipt["failure_type"] == "invalid_or_unapproved_oap_owned_https_origin"
    assert receipt["live_geometry_proven"] is False
    assert receipt["bounded_capacity_proven"] is False


def test_approved_origin_only_authorises_observation_not_green():
    receipt = routing_ci_preflight.readiness()
    assert receipt["configured_for_live_probe"] is True
    assert receipt["proof_state"] == "NOT_RUN"
    assert receipt["live_probe_executed"] is False
    assert receipt["live_geometry_proven"] is False
    assert receipt["production_routing_ready"] is False


def test_preflight_does_not_fetch_network_or_store_sensitive_data(monkeypatch):
    def no_network(*_args, **_kwargs):
        raise AssertionError("network access attempted")

    monkeypatch.setattr(routing_live_green_gate.request, "urlopen", no_network)
    receipt = routing_ci_preflight.readiness()
    assert receipt["configured_for_live_probe"] is True
    assert "routing.example.test" not in str(receipt)
    assert receipt["tracking_performed"] is False
    assert receipt["payment_performed"] is False
    assert receipt["dispatch_performed"] is False


def test_ci_workflow_requires_preflight_and_publishes_truth_evidence():
    source = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "python -m scripts.routing_ci_preflight" in source
    assert "if: steps.routing_live_preflight.outputs.configured == 'true'" in source
    assert "python -m scripts.routing_live_green_gate" in source
    assert "name: routing-external-proof" in source
    assert "OAP_ROUTING_OWNED_HOSTS:" in source
    assert "OAP_OSRM_ALLOWED_HOSTS:" in source


def test_ci_receipt_prints_unknown_and_not_green(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(routing_live_green_gate, "BASE", "")
    out = tmp_path / "output.txt"
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_OUTPUT", str(out))
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    monkeypatch.setattr(routing_ci_preflight, "Path", lambda *_args: tmp_path / "proof.json")
    routing_ci_preflight.main()
    receipt = json.loads(capsys.readouterr().out)
    assert receipt["proof_state"] == "UNKNOWN_LOCKED"
    assert receipt["production_routing_ready"] is False
    assert out.read_text(encoding="utf-8") == "configured=false\n"
    assert "NOT VERIFIED" in summary.read_text(encoding="utf-8")
    assert json.loads((tmp_path / "proof.json").read_text(encoding="utf-8")) == receipt
