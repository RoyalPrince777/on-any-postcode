"""External routing failures must leave a negative, auditable receipt."""
from __future__ import annotations

import json
from urllib.error import URLError

import pytest

from scripts import routing_live_green_gate as gate


def test_reset_and_timeout_are_negative_not_missing(monkeypatch):
    for error in (TimeoutError("timed out"), URLError("reset by peer")):
        def fail(_req, timeout):
            assert timeout == gate.TIMEOUT_SECONDS
            raise error

        monkeypatch.setattr(gate.request, "urlopen", fail)
        result = gate.run_one(0)
        assert result["ok"] is False
        assert result["elapsed_s"] >= 0
        assert result["failure_type"] == type(error).__name__
        assert result["distance_m"] == 0


def test_mixed_external_failure_emits_receipt_then_fails(monkeypatch, capsys):
    def run(index):
        return {
            "route_id": gate.ROUTES[index % 2][4],
            "ok": index != 0,
            "elapsed_s": 0.01,
            **({"failure_type": "TimeoutError"} if index == 0 else {}),
        }

    monkeypatch.setattr(gate, "run_one", run)
    with pytest.raises(SystemExit, match="live routing probe had failed requests"):
        gate.main()
    receipt = json.loads(capsys.readouterr().out)
    assert receipt["successes"] == gate.TOTAL_REQUESTS - 1
    assert receipt["failures"] == 1
    assert receipt["failure_types"] == ["TimeoutError"]
    assert receipt["geometry_proven"] is False
    assert receipt["bounded_capacity_proven"] is False
    assert receipt["dispatch_performed"] is False
