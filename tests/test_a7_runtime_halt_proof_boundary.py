"""A7 runtime emergency halt cannot be proven by a memory-only rehearsal."""
from unittest.mock import MagicMock

from mission_control import a7_certification


def test_a7_emergency_halt_requires_runtime_receipt(monkeypatch):
    from mission_control import postgres_db

    monkeypatch.setattr(postgres_db, "configured", lambda: True)
    conn = MagicMock()
    conn.execute.return_value.fetchone.return_value = (0,) * 10
    ctx = MagicMock()
    ctx.__enter__.return_value = conn
    monkeypatch.setattr(postgres_db, "connect", lambda *, readonly=False: ctx)

    counts = a7_certification._production_counts()
    sql = conn.execute.call_args.args[0]

    assert counts["store_reachable"] is True
    assert counts["a7_emergency_halt"] == 0
    assert "metadata->>'runtime_halt_verified'='true'" in sql
    assert sql.count("runtime_halt_verified") == 1


def test_in_memory_halt_is_only_rehearsal():
    result = a7_certification._emergency_halt_exercise()
    assert result["production_state_mutated"] is False
    assert result["execution_authority_expanded"] is False
