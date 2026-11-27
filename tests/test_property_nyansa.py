"""NYANSA observation cannot turn schema visibility into deal certification."""
from contextlib import contextmanager

from mission_control import property_authority


def test_nyansa_schema_observation(monkeypatch):
    class Connection:
        def execute(self, sql):
            assert sql.startswith("SELECT ")
            assert "LIMIT 0" in sql

    @contextmanager
    def connect(*, readonly):
        assert readonly is True
        yield Connection()

    monkeypatch.setattr(property_authority.postgres_db, "connect", connect)
    result = property_authority.nyansa_readiness()
    assert result["schema_observed"] is True
    assert result["status"] == "incomplete"
    assert not result["transaction_verified"]
    assert not result["execution_granted"]
    assert not result["consequential_action"]


def test_nyansa_outage_stays_unknown(monkeypatch):
    def unavailable(*, readonly):
        assert readonly is True
        raise RuntimeError("unavailable")

    monkeypatch.setattr(property_authority.postgres_db, "connect", unavailable)
    result = property_authority.nyansa_readiness()
    assert result["status"] == "unknown"
    assert not result["schema_observed"]
    assert not result["transaction_verified"]
