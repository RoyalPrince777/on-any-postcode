"""Operational SMI Green Gate rollback proof must not accept rehearsals."""
from unittest.mock import MagicMock

from mission_control import smi_proof_gate


def test_green_gate_rollback_query_requires_operational_receipt(monkeypatch):
    from mission_control import postgres_db

    monkeypatch.setattr(postgres_db, "configured", lambda: True)
    connection = MagicMock()
    connection.execute.return_value.fetchone.side_effect = [
        (0, 0, 0, 0, 0, 0, 0),
        (None,),
    ]
    ctx = MagicMock()
    ctx.__enter__.return_value = connection
    monkeypatch.setattr(postgres_db, "connect", lambda *, readonly=False: ctx)

    result = smi_proof_gate._production_counts()
    assert result["store_reachable"] is True
    assert result["rollback_recovery_receipts"] == 0
    statement = connection.execute.call_args_list[0].args[0]
    assert "metadata->>'operational_rollback_verified'='true'" in statement
    assert statement.count("operational_rollback_verified") == 1
