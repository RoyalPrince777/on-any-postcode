from __future__ import annotations

from contextlib import contextmanager

from mission_control import founder_activation, neon_auth, postgres_db


class _Rows:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class _Connection:
    def __init__(self, user_snapshots):
        self.user_snapshots = list(user_snapshots)
        self.statements = []

    def execute(self, statement, parameters=None):
        self.statements.append((statement, parameters))
        if "SELECT email" in statement:
            return _Rows(self.user_snapshots.pop(0))
        return _Rows([])


def _ready(monkeypatch):
    monkeypatch.setenv(
        founder_activation.ACTIVATION_TOKEN_ENV,
        "one-time-founder-activation-code-value-123456",
    )
    monkeypatch.setenv("OAP_HUMAN_AUTHORITY_EMAIL", "founder@example.test")
    monkeypatch.setenv(
        "NEON_AUTH_BASE_URL", "https://example.neonauth.test/neondb/auth"
    )
    monkeypatch.setattr(postgres_db, "configured", lambda: True)


def test_activation_state_requires_live_zero_user_proof(monkeypatch):
    _ready(monkeypatch)
    connection = _Connection([[]])

    @contextmanager
    def fake_connect(*, readonly=False):
        assert readonly is True
        yield connection

    monkeypatch.setattr(postgres_db, "connect", fake_connect)

    assert founder_activation.state() == "available"

    connection.user_snapshots = [[("someone@example.test",)]]
    assert founder_activation.state() == "complete"


def test_activation_serialises_and_confirms_the_server_selected_user(monkeypatch):
    _ready(monkeypatch)
    connection = _Connection([[], [("founder@example.test",)]])
    observed = {}

    @contextmanager
    def fake_connect(*, readonly=False):
        assert readonly is False
        yield connection

    def fake_sign_up(password, name):
        observed["credentials"] = (password, name)
        return neon_auth.AuthResult(status_code=200, payload={"user": {}})

    monkeypatch.setattr(postgres_db, "connect", fake_connect)
    monkeypatch.setattr(neon_auth, "sign_up_founder", fake_sign_up)

    result = founder_activation.activate("a private passphrase")

    assert result == "activated"
    assert observed == {
        "credentials": ("a private passphrase", "OAP Founder")
    }
    assert "pg_advisory_xact_lock" in connection.statements[0][0]


def test_activation_never_calls_provider_when_any_user_exists(monkeypatch):
    _ready(monkeypatch)
    connection = _Connection([[("existing@example.test",)]])

    @contextmanager
    def fake_connect(*, readonly=False):
        assert readonly is False
        yield connection

    def unexpected_sign_up(_password, _name):
        raise AssertionError("provider must not be called")

    monkeypatch.setattr(postgres_db, "connect", fake_connect)
    monkeypatch.setattr(neon_auth, "sign_up_founder", unexpected_sign_up)

    assert founder_activation.activate("a private passphrase") == "complete"


def test_activation_state_fails_closed_when_database_is_uncertain(monkeypatch):
    _ready(monkeypatch)

    @contextmanager
    def broken_connect(*, readonly=False):
        del readonly
        raise RuntimeError("database unavailable")
        yield  # pragma: no cover

    monkeypatch.setattr(postgres_db, "connect", broken_connect)

    assert founder_activation.state() == "unavailable"
