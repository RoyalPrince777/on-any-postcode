"""Founder verifier DB isolation: no platform-writer promotion or mutation."""
from unittest.mock import MagicMock

from mission_control import founder_local_auth, postgres_db


def test_legacy_verifier_still_uses_primary_readonly(monkeypatch):
    monkeypatch.delenv("OAP_FOUNDER_VERIFIER_DATABASE_URL", raising=False)
    connection = MagicMock()
    context = MagicMock()
    context.__enter__.return_value = connection
    monkeypatch.setattr(postgres_db, "connect", lambda *, readonly: context if readonly else None)

    with founder_local_auth._verifier_readonly() as opened:
        assert opened is connection


def test_separate_verifier_connection_is_explicit_and_readonly(monkeypatch):
    monkeypatch.setenv("OAP_FOUNDER_VERIFIER_DATABASE_URL", "postgresql://readonly-verifier.invalid/db")
    connection = MagicMock()
    context = MagicMock()
    context.__enter__.return_value = connection
    driver = MagicMock()
    driver.connect.return_value = context
    monkeypatch.setattr(postgres_db, "_driver", lambda: driver)
    monkeypatch.setattr(
        postgres_db, "connect",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("platform database used")),
    )

    with founder_local_auth._verifier_readonly() as opened:
        assert opened is connection

    driver.connect.assert_called_once_with(
        "postgresql://readonly-verifier.invalid/db",
        connect_timeout=5,
        application_name="oap-founder-verifier-readonly",
        autocommit=False,
    )
    connection.execute.assert_called_once_with("SET TRANSACTION READ ONLY")


def test_separate_verifier_never_rebinds_password(monkeypatch):
    import pytest

    monkeypatch.setenv("OAP_FOUNDER_VERIFIER_DATABASE_URL", "postgresql://readonly-verifier.invalid/db")
    with pytest.raises(founder_local_auth.FounderLocalAuthUnavailable, match="separate_verifier_store_read_only"):
        founder_local_auth.bind_existing_password("not-a-real-founder-password")
