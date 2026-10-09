"""Negative proof for OAP TV's existing Founder-session adapter."""
from unittest.mock import patch

import pytest

from mission_control.tv_founder_session import verified_founder_identity


@pytest.mark.parametrize("cookie", [None, "", 1, {}, "untrusted"])
def test_invalid_cookie_denied(cookie):
    assert verified_founder_identity(cookie) is None


def test_missing_or_expired_session_denied():
    with patch("mission_control.tv_founder_session.founder_local_auth.session_user", return_value=None):
        assert verified_founder_identity("Cookie=expired") is None


def test_mismatched_identity_denied():
    with (
        patch("mission_control.tv_founder_session.founder_local_auth.session_user", return_value={"id": "other"}),
        patch("mission_control.tv_founder_session.founder_local_auth.resolved_identity", return_value="founder"),
    ):
        assert verified_founder_identity("Cookie=signed") is None


def test_verified_session_uses_canonical_identity():
    with (
        patch("mission_control.tv_founder_session.founder_local_auth.session_user", return_value={"id": "founder"}),
        patch("mission_control.tv_founder_session.founder_local_auth.resolved_identity", return_value="founder"),
    ):
        assert verified_founder_identity("Cookie=signed") == "founder"
