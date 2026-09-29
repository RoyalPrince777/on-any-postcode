from mission_control import music_accounting, music_purchases


class _Result:
    def __init__(self, row):
        self._row = row

    def fetchone(self):
        return self._row

    def fetchall(self):
        return self._row or []


class _Connection:
    def __init__(self, scripted):
        self.scripted = list(scripted)
        self.calls = []
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=()):
        self.calls.append((sql, params))
        value = self.scripted.pop(0) if self.scripted else None
        return _Result(value)

    def commit(self):
        self.committed = True


def test_music_accounting_schema_is_evidence_only():
    schema = "\n".join(music_accounting.SCHEMA_STATEMENTS)
    assert music_accounting.MUSIC_ACCOUNTING_MIGRATION_VERSION == "0018_oap_music_accounting"
    assert "PENDING_RECONCILIATION" in schema
    assert "RECONCILED" in schema
    assert "REVERSED" in schema
    assert "refund_reference" in schema


def test_refund_revokes_ownership_and_reverses_allocation(monkeypatch):
    connection = _Connection([
        ("11111111-1111-4111-8111-111111111111", "RELEASE", "22222222-2222-4222-8222-222222222222"),
        None,
        None,
    ])
    monkeypatch.setattr(music_purchases.postgres_db, "connect", lambda **kwargs: connection)
    result = music_purchases.MusicPurchaseStore().record_refund(
        purchase_id="33333333-3333-4333-8333-333333333333",
        refund_reference="refund-proof-001",
    )
    assert result["state"] == "REFUNDED"
    assert result["ownership_active"] is False
    assert result["creator_allocation_state"] == "REVERSED"
    assert result["refund_execution_performed_by_this_module"] is False
    assert result["money_transfer_performed"] is False
    assert result["sika_execution_performed"] is False
    sql = "\n".join(call[0] for call in connection.calls)
    assert "SET active=FALSE" in sql
    assert "SET state='REVERSED'" in sql
    assert connection.committed is True


def test_creator_reconciliation_records_reference_without_money_movement(monkeypatch):
    connection = _Connection([
        ("11111111-1111-4111-8111-111111111111", 500, "GBP"),
    ])
    monkeypatch.setattr(music_purchases.postgres_db, "connect", lambda **kwargs: connection)
    result = music_purchases.MusicPurchaseStore().creator_reconciliation(
        purchase_id="33333333-3333-4333-8333-333333333333",
        reconciliation_reference="reconcile-proof-001",
    )
    assert result["state"] == "RECONCILED"
    assert result["gross_amount_minor"] == 500
    assert result["currency"] == "GBP"
    assert result["reconciliation_reference_recorded"] is True
    assert result["money_transfer_performed"] is False
    assert result["sika_execution_performed"] is False
