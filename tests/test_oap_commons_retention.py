"""OAP Commons retention operator: no fake schedule, no member data in logs."""
from __future__ import annotations

import json

from mission_control import oap_commons_retention as operator


def test_apply_requires_explicit_operator_enablement(monkeypatch, capsys):
    monkeypatch.delenv("OAP_COMMONS_RETENTION_ENABLED", raising=False)
    called = []
    monkeypatch.setattr(operator.postgres_db, "configured", lambda:
                        called.append(True) or True)
    assert operator.main(["--apply"]) == 2
    response = json.loads(capsys.readouterr().out)
    assert response["status"] == "DENIED"
    assert not called


def test_nonconfigured_postgres_fails_closed(monkeypatch, capsys):
    monkeypatch.setattr(operator.postgres_db, "configured", lambda: False)
    assert operator.main(["--dry-run"]) == 3
    assert json.loads(capsys.readouterr().out)["status"] == "UNAVAILABLE"


def test_dry_run_does_not_erase(monkeypatch, capsys):
    monkeypatch.setattr(operator.postgres_db, "configured", lambda: True)
    monkeypatch.setattr(operator.oap_commons_governance, "expired_count", lambda: 7)
    monkeypatch.setattr(operator.oap_commons_governance, "erase_expired_system",
                        lambda **kwargs: (_ for _ in ()).throw(
                            AssertionError("must never erase in dry run")))
    assert operator.main(["--dry-run"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["expired_count"] == 7
    assert result["content_erased"] == 0
    assert result["scheduler_installed"] is False


def test_apply_runs_bounded_batches_and_audit_actor(monkeypatch, capsys):
    monkeypatch.setenv("OAP_COMMONS_RETENTION_ENABLED", "1")
    monkeypatch.setattr(operator.postgres_db, "configured", lambda: True)
    counts = iter((170, 0))
    monkeypatch.setattr(operator.oap_commons_governance, "expired_count",
                        lambda: next(counts))
    calls = []
    def sweep(*, limit):
        calls.append(limit)
        return {"redacted_count": 100 if len(calls) == 1 else 70}
    monkeypatch.setattr(operator.oap_commons_governance, "erase_expired_system", sweep)
    assert operator.main(["--apply", "--batch-size", "100"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert calls == [100, 100]
    assert result["redacted_count"] == 170
    assert result["audit_actor"] == "OAP_COMMONS_RETENTION_SERVICE"
    assert result["scheduler_installed"] is False


def test_backlog_returns_nonzero_for_alerts(monkeypatch, capsys):
    monkeypatch.setenv("OAP_COMMONS_RETENTION_ENABLED", "1")
    monkeypatch.setattr(operator.postgres_db, "configured", lambda: True)
    counts = iter((140, 40))
    monkeypatch.setattr(operator.oap_commons_governance, "expired_count",
                        lambda: next(counts))
    monkeypatch.setattr(
        operator.oap_commons_governance, "erase_expired_system",
        lambda *, limit: {"redacted_count": 100},
    )
    assert operator.main(["--apply", "--max-batches", "1"]) == 4
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "BACKLOG_REMAINS"
    assert result["expired_remaining"] == 40


def test_batch_bounds_fail_before_reading_db():
    import pytest

    with pytest.raises(SystemExit):
        operator.main(["--dry-run", "--batch-size", "101"])
    with pytest.raises(SystemExit):
        operator.main(["--apply", "--max-batches", "21"])
