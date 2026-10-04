import pytest

from mission_control import sika_payment_orchestrator


class _Result:
    def __init__(self, row=None):
        self._row = row

    def fetchone(self):
        return self._row


class _Connection:
    def __init__(self):
        self.hold_update = None
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=()):
        if "UPDATE oap_sika_payment_intents" in sql:
            return _Result(
                (
                    "pay-1",
                    "idem-1",
                    "acct-1",
                    "merchant-1",
                    "10.00",
                    "GBP",
                    "United Kingdom",
                    params[0],
                    "provider-1",
                )
            )
        if "to_regclass" in sql:
            return _Result(("oap_sika_payment_holds",))
        if "UPDATE oap_sika_payment_holds" in sql:
            self.hold_update = params
            return _Result()
        raise AssertionError(sql)

    def commit(self):
        self.committed = True


@pytest.mark.parametrize(
    ("target", "expected_hold"),
    (
        ("SETTLED", "CONSUMED"),
        ("FAILED", "RELEASED"),
    ),
)
def test_terminal_payment_state_updates_active_hold_atomically(
    monkeypatch,
    target,
    expected_hold,
):
    current = sika_payment_orchestrator.PaymentIntent(
        payment_id="pay-1",
        idempotency_key="idem-1",
        payer_account_id="acct-1",
        payee_reference="merchant-1",
        amount=sika_payment_orchestrator.Decimal("10.00"),
        currency="GBP",
        jurisdiction="United Kingdom",
        status="SUBMITTED",
        provider_reference="provider-1",
    )
    connection = _Connection()
    monkeypatch.setattr(
        sika_payment_orchestrator,
        "read_intent",
        lambda payment_id: current,
    )
    monkeypatch.setattr(
        sika_payment_orchestrator.postgres_db,
        "connect",
        lambda: connection,
    )

    result = sika_payment_orchestrator.transition(
        payment_id="pay-1",
        target_status=target,
    )

    assert result.status == target
    assert connection.hold_update == (expected_hold, "pay-1")
    assert connection.committed is True


def test_orchestrator_status_exposes_terminal_hold_lifecycle():
    assert (
        sika_payment_orchestrator.status()["terminal_hold_lifecycle_sync"]
        is True
    )
