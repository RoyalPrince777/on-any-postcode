"""Regression tests: a supplied Founder cookie must never fall through to managed Auth."""
from __future__ import annotations

import pytest

from mission_control import founder_local_auth, neon_auth


def _provider_must_not_run(*_args, **_kwargs):
    raise AssertionError("A supplied local Founder cookie must not fall back to managed Auth")


def test_invalid_founder_cookie_cannot_fall_back_to_managed_auth(monkeypatch):
    monkeypatch.setattr(neon_auth, "_request", _provider_must_not_run)
    monkeypatch.setattr(founder_local_auth, "session_user", lambda _header: None)

    result = neon_auth.get_session(
        "oap_founder_session=invalid; better-auth.session_token=other-identity"
    )
    assert result.status_code == 401
    assert neon_auth.safe_error_code(result) == "INVALID_FOUNDER_SESSION"


def test_founder_auth_store_outage_cannot_fall_back(monkeypatch):
    monkeypatch.setattr(neon_auth, "_request", _provider_must_not_run)

    def unavailable(_header):
        raise founder_local_auth.FounderLocalAuthUnavailable("store_unavailable")

    monkeypatch.setattr(founder_local_auth, "session_user", unavailable)
    with pytest.raises(neon_auth.AuthUnavailable, match="founder_local_auth_unavailable"):
        neon_auth.get_session("oap_founder_session=opaque")


def test_managed_auth_still_works_without_founder_cookie(monkeypatch):
    expected = neon_auth.AuthResult(
        status_code=200,
        payload={"session": {"id": "managed"}, "user": {"id": "ordinary-member"}},
    )
    monkeypatch.setattr(neon_auth, "_request", lambda *_args, **_kwargs: expected)
    assert neon_auth.get_session("better-auth.session_token=ordinary") is expected


def test_valid_founder_cookie_remains_local(monkeypatch):
    monkeypatch.setattr(neon_auth, "_request", _provider_must_not_run)
    monkeypatch.setattr(
        founder_local_auth,
        "session_user",
        lambda _header: {"id": "founder", "name": "OAP Founder"},
    )
    result = neon_auth.get_session("oap_founder_session=valid")
    assert result.status_code == 200
    assert result.payload["user"]["id"] == "founder"


def test_empty_founder_cookie_cannot_fall_back_to_managed_auth(monkeypatch):
    monkeypatch.setattr(neon_auth, "_request", _provider_must_not_run)
    monkeypatch.setattr(founder_local_auth, "session_user", lambda _header: None)
    result = neon_auth.get_session(
        "oap_founder_session=; better-auth.session_token=other-identity"
    )
    assert result.status_code == 401
    assert neon_auth.safe_error_code(result) == "INVALID_FOUNDER_SESSION"
