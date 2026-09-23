from __future__ import annotations

import json
from urllib import error

import pytest

from scripts import routing_live_green_gate as gate


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

    monkeypatch.setattr(gate.request, "urlopen", fail_request)
    result = gate.run_one(0)
    assert result["ok"] is False
    assert result["failure_type"] == expected_type
    assert result["route_id"] == "mitcham_london_bridge"
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

    with pytest.raises(SystemExit, match="live routing probe had failed requests"):
        gate.main()
    receipt = json.loads(capsys.readouterr().out)
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
    with pytest.raises(SystemExit, match="p95 exceeded 6.0s"):
        gate.main()
    receipt = json.loads(capsys.readouterr().out)
    assert receipt["successes"] == 2
    assert receipt["failures"] == 0
    assert receipt["bounded_capacity_proven"] is False
