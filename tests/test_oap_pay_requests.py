from datetime import UTC, datetime, timedelta

import pytest

from mission_control import oap_pay_requests


class _Result:
    def __init__(self, row=None):
        self._row = row

    def fetchone(self):
        return self._row


class _Connection:
    def __init__(self, state):
        self.state = state

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, sql, params=None):
        if sql.lstrip().startswith("INSERT INTO oap_pay_requests"):
            self.state["insert"] = params
            return _Result()
        if "FROM oap_pay_requests" in sql and "WHERE token_hash=%s" in sql:
            return _Result(self.state.get("read_row"))
        if sql.lstrip().startswith("UPDATE oap_pay_requests"):
            return _Result(("req-1",) if self.state.get("cancel") else None)
        return _Result()

    def commit(self):
        self.state["committed"] = True


def _patch_db(monkeypatch, state):
    monkeypatch.setattr(
        oap_pay_requests.postgres_db,
        "connect",
        lambda **_kwargs: _Connection(state),
    )


def test_create_request_hashes_share_token_and_creates_no_debt(monkeypatch):
    state = {}
    _patch_db(monkeypatch, state)
    result = oap_pay_requests.create_request(
        request_id="req-1",
        payee_reference="merchant-1",
        amount="12.50",
        currency="gbp",
        jurisdiction="United Kingdom",
        surface="OAP Market",
        note="Order 44",
        expires_at=(datetime.now(UTC) + timedelta(days=1)).isoformat(),
    )
    assert result["share_path"].startswith("/pay/r/")
    assert result["share_token"] not in state["insert"]
    assert state["insert"][1] != result["share_token"]
    assert result["qr_ready"] is True
    assert result["recipient_approval_required"] is True
    assert result["creates_debt"] is False
    assert result["payment_authorised"] is False
    assert result["money_movement"] is False


def test_read_public_request_never_claims_authorisation(monkeypatch):
    state = {
        "read_row": (
            "req-1",
            "merchant-1",
            12.50,
            "GBP",
            "United Kingdom",
            "OAP Market",
            "Order 44",
            "OPEN",
            datetime.now(UTC) + timedelta(days=1),
        )
    }
    _patch_db(monkeypatch, state)
    result = oap_pay_requests.read_public_request("opaque-token")
    assert result["payable"] is True
    assert result["recipient_approval_required"] is True
    assert result["creates_debt"] is False
    assert result["payment_authorised"] is False
    assert result["money_movement"] is False


def test_read_public_request_marks_expired_non_payable(monkeypatch):
    state = {
        "read_row": (
            "req-1",
            "merchant-1",
            12.50,
            "GBP",
            "United Kingdom",
            "OAP Market",
            None,
            "OPEN",
            datetime.now(UTC) - timedelta(seconds=1),
        )
    }
    _patch_db(monkeypatch, state)
    result = oap_pay_requests.read_public_request("opaque-token")
    assert result["expired"] is True
    assert result["payable"] is False


def test_cancel_request_is_bounded(monkeypatch):
    state = {"cancel": True}
    _patch_db(monkeypatch, state)
    assert oap_pay_requests.cancel_request(request_id="req-1") is True
    assert state["committed"] is True


def test_schema_requires_human_approval():
    with pytest.raises(RuntimeError):
        oap_pay_requests.init_schema()


def test_status_truth_boundaries():
    status = oap_pay_requests.status()
    assert status["persistent_requests"] is True
    assert status["opaque_share_tokens"] is True
    assert status["share_tokens_stored_plaintext"] is False
    assert status["creates_debt"] is False
    assert status["payment_authorisation"] is False
    assert status["money_movement"] is False
