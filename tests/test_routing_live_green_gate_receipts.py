from __future__ import annotations

import json
from pathlib import Path
from urllib import error

import pytest

from scripts import routing_live_green_gate as gate


@pytest.fixture(autouse=True)
def _configured_routing_origin(monkeypatch):
    monkeypatch.setenv("OAP_ROUTING_BASE_URL", "https://routing.oap.invalid")


@pytest.mark.parametrize(
    ("failure", "expected_type"),
    [
        (TimeoutError("read timed out"), "timeout"),
        (error.URLError("unreachable"), "request_or_response_error"),
    ],
)
def test_failed_routing_request_returns_bounded_failure(monkeypatch, failure, expected_type):
    def fail_request(*args, **kwargs):
        raise failure

    monkeypatch.setattr(gate._OPENER, "open", fail_request)
    result = gate.run_one(0)
    assert result["ok"] is False
    assert result["failure_type"] == expected_type
    assert result["route_id"] == "mitcham_london_bridge"
    assert result["distance_m"] == 0.0
    assert result["duration_s"] == 0.0


def test_non_object_json_is_bounded_failure(monkeypatch):
    class FakeResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b"[]"

    monkeypatch.setattr(gate._OPENER, "open", lambda *args, **kwargs: FakeResponse())
    result = gate.run_one(0)
    assert result["ok"] is False
    assert result["failure_type"] == "request_or_response_error"
    assert result["distance_m"] == 0.0
    assert result["duration_s"] == 0.0


def test_probe_prints_failure_receipt_before_failing(monkeypatch, capsys):
    monkeypatch.setattr(gate, "TOTAL_REQUESTS", 2)
    monkeypatch.setattr(gate, "WORKERS", 1)
    samples = (
        {"route_id": "a", "ok": True, "elapsed_s": 0.2},
        {"route_id": "b", "ok": False, "elapsed_s": 10.0, "failure_type": "timeout"},
    )
    monkeypatch.setattr(gate, "run_one", lambda index: samples[index])
    monkeypatch.setattr(gate, "wait_until_ready", lambda: {"ready": True, "attempts": 1, "elapsed_s": 0.0})

    with pytest.raises(SystemExit, match="live routing probe had failed requests"):
        gate.main()
    receipts = [json.loads(line) for line in capsys.readouterr().out.splitlines() if line.strip()]
    assert receipts[0]["event"] == "oap_routing_bounded_external_warmup"
    receipt = receipts[-1]
    assert receipt["event"] == "oap_routing_bounded_external_probe"
    assert receipt["requests"] == 2
    assert receipt["successes"] == 1
    assert receipt["failures"] == 1
    assert receipt["timeouts"] == 1
    assert receipt["geometry_proven"] is False
    assert receipt["bounded_capacity_proven"] is False
    assert receipt["dispatch_performed"] is False
    assert receipt["payment_performed"] is False
    assert receipt["tracking_performed"] is False


def test_probe_preserves_p95_limit(monkeypatch, capsys):
    monkeypatch.setattr(gate, "TOTAL_REQUESTS", 2)
    monkeypatch.setattr(gate, "WORKERS", 1)
    monkeypatch.setattr(
        gate,
        "run_one",
        lambda index: {"route_id": str(index), "ok": True, "elapsed_s": 7.0},
    )
    monkeypatch.setattr(gate, "wait_until_ready", lambda: {"ready": True, "attempts": 1, "elapsed_s": 0.0})
    with pytest.raises(SystemExit, match="p95 exceeded 6.0s"):
        gate.main()
    receipts = [json.loads(line) for line in capsys.readouterr().out.splitlines() if line.strip()]
    assert receipts[0]["event"] == "oap_routing_bounded_external_warmup"
    receipt = receipts[-1]
    assert receipt["event"] == "oap_routing_bounded_external_probe"
    assert receipt["successes"] == 2
    assert receipt["failures"] == 0
    assert receipt["bounded_capacity_proven"] is False


def test_live_green_gate_warms_before_capacity_probe():
    source = Path("scripts/routing_live_green_gate.py").read_text(encoding="utf-8")

    assert "def wait_until_ready()" in source
    assert '"event": "oap_routing_bounded_external_warmup"' in source
    assert 'if not warmup.get("ready")' in source
    assert "TOTAL_REQUESTS = 20" in source
    assert "WORKERS = 4" in source
    assert "P95_LIMIT_SECONDS = 6.0" in source


def test_routing_endpoint_is_configurable_and_https_only():
    import os
    import subprocess
    import sys

    snippet = (
        "from scripts import routing_live_green_gate as gate; "
        "print(gate._route_url(0))"
    )
    env = dict(os.environ)
    env["OAP_ROUTING_BASE_URL"] = "https://routing.example.org/"
    valid = subprocess.run(
        [sys.executable, "-c", snippet], env=env, capture_output=True, text=True, check=False
    )
    assert valid.returncode == 0, valid.stderr
    assert valid.stdout.startswith("https://routing.example.org/route/v1/driving/")

    for invalid in (
        "http://routing.example.org",
        "https://user:password@routing.example.org",
        "https://routing.example.org/prefix",
        "https://routing.example.org?x=1",
        "https://routing.example.org#fragment",
        "https://routing.example.org?",
        "https://routing.example.org#",
        "https://routing.example.org:",
        "https://routing.example.org:abc",
        "https://routing.example.org:65536",
        "https://routing.example.org:0",
        "https://routing.example.org:8443",
        "https://oap-routing.onrender.com",
        "https://OAP-ROUTING.ONRENDER.COM./",
        "https://onrender.com",
        "https://routing.example.org\\\\@evil.example",
        "https://routing.example.org%2f.evil.example",
        "https://routing.example.org/route/",
        "https://routing.example.org/\\n",
        " https://routing.example.org",
        "https://routing.example.org ",
        "https://",
    ):
        env["OAP_ROUTING_BASE_URL"] = invalid
        result = subprocess.run(
            [sys.executable, "-c", snippet], env=env, capture_output=True, text=True, check=False
        )
        assert result.returncode != 0, invalid
        assert "ValueError" in result.stderr


def test_routing_endpoint_accepts_explicit_https_port():
    import os
    import subprocess
    import sys

    env = dict(os.environ)
    env["OAP_ROUTING_BASE_URL"] = "https://routing.example.org:443/"
    result = subprocess.run(
        [sys.executable, "-c", "from scripts import routing_live_green_gate as g; print(g.routing_base())"],
        env=env, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "https://routing.example.org:443"
