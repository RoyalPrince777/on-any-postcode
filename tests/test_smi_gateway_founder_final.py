from __future__ import annotations

import importlib
from pathlib import Path

import smi_gateway


def test_gateway_founder_final_waits_for_fresh_health_observability():
    source = Path("smi_gateway.py").read_text(encoding="utf-8")
    assert 'OAP_FOUNDER_FINAL_100_ON_HEALTH' in source
    assert '_complete_founder_final_if_requested(trigger="boot")' not in source
    health = source.split('@app.get("/healthz")', 1)[1].split(
        '@app.route("/<path:path>"', 1
    )[0]
    telemetry_at = health.index('telemetry.record_http_request(path="/healthz"')
    founder_at = health.index('_complete_founder_final_if_requested(trigger="health")')
    assert telemetry_at < founder_at
    assert "smi_proof_gate.complete_founder_final_protocol(identity_id)" in source


def test_founder_final_disabled_does_nothing(monkeypatch):
    module = importlib.reload(smi_gateway)
    monkeypatch.delenv("OAP_FOUNDER_FINAL_100_ON_HEALTH", raising=False)
    called = {"count": 0}
    monkeypatch.setattr(
        module.smi_proof_gate,
        "complete_founder_final_protocol",
        lambda identity: called.__setitem__("count", called["count"] + 1),
    )
    module._complete_founder_final_if_requested(trigger="health")
    assert called["count"] == 0


def test_founder_final_runs_once_per_revision(monkeypatch):
    module = importlib.reload(smi_gateway)
    monkeypatch.setenv("OAP_FOUNDER_FINAL_100_ON_HEALTH", "1")
    monkeypatch.setattr(module, "_revision", lambda: "proof-rev")
    monkeypatch.setattr(module, "_resolve_a6_human_authority", lambda: "00000000-0000-0000-0000-000000000001")
    calls = []

    def complete(identity):
        calls.append(identity)
        return {
            "passed": True,
            "green_gate": True,
            "founder_final": True,
            "audit_recorded": True,
        }

    monkeypatch.setattr(module.smi_proof_gate, "complete_founder_final_protocol", complete)
    module._FOUNDER_FINAL_ATTEMPTED.clear()
    module._complete_founder_final_if_requested(trigger="health")
    module._complete_founder_final_if_requested(trigger="health")
    assert calls == ["00000000-0000-0000-0000-000000000001"]


def test_founder_final_failure_is_fail_closed(monkeypatch):
    module = importlib.reload(smi_gateway)
    monkeypatch.setenv("OAP_FOUNDER_FINAL_100_ON_HEALTH", "1")
    monkeypatch.setattr(module, "_revision", lambda: "failed-rev")
    monkeypatch.setattr(module, "_resolve_a6_human_authority", lambda: "00000000-0000-0000-0000-000000000001")

    def blocked(identity):
        raise RuntimeError("green_gate_incomplete:observability")

    monkeypatch.setattr(module.smi_proof_gate, "complete_founder_final_protocol", blocked)
    module._FOUNDER_FINAL_ATTEMPTED.clear()
    module._complete_founder_final_if_requested(trigger="health")
    assert "founder-final:failed-rev" in module._FOUNDER_FINAL_ATTEMPTED
