"""A6 rollback assurance must not treat a dry-run rehearsal as runtime proof."""
from unittest.mock import MagicMock

from mission_control import a7_certification


def test_a6_proof_query_requires_operational_rollback_metadata(monkeypatch):
    from mission_control import postgres_db

    monkeypatch.setattr(postgres_db, "configured", lambda: True)
    connection = MagicMock()
    connection.execute.return_value.fetchone.return_value = (0,) * 10
    ctx = MagicMock()
    ctx.__enter__.return_value = connection
    monkeypatch.setattr(postgres_db, "connect", lambda *, readonly=False: ctx)

    result = a7_certification._production_counts()

    assert result["store_reachable"] is True
    sql = connection.execute.call_args.args[0]
    assert "A6_OPERATION_ROLLBACK_PROOF" in sql
    assert "operational_rollback_verified" in sql
    assert "metadata->>'operational_rollback_verified'='true'" in sql
    assert result["a6_operation_rollback"] == 0
