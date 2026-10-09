"""Bounded real-signature Founder-session to private-gate integration proof.

Only Founder session cryptography is exercised end-to-end. Asset/rights/entitlement/
storage evidence remains caller-supplied and is NOT certified by this test.
No endpoint, storage read, or media response is created.
"""
from unittest.mock import patch

import pytest

from mission_control import founder_local_auth
from mission_control.tv_founder_session import verified_founder_identity
from mission_control.tv_private_playback_gate import authorize_private_playback


def _allow_contract():
    return {
        "decision": "ALLOW",
        "decision_hash": "e" * 64,
        "evidence_hashes": ["a" * 64],
        "authority_receipt_hashes": ["b" * 64],
        "human_approval_receipt_hashes": ["c" * 64],
        "public_distribution_authorized": False,
    }


def _gate(cookie, *, trusted=False, owner=True, rights=None, entitlement=True, integrity=True):
    founder = verified_founder_identity(cookie) is not None
    return authorize_private_playback(
        founder_authenticated=founder,
        owner_identity_matches=owner,
        rights_decision=_allow_contract() if rights is None else rights,
        entitlement_proven=entitlement,
        storage_integrity_proven=integrity,
        server_evidence_verified=trusted,
    )


@pytest.fixture
def founder_session():
    # Test-only deterministic identity and signing key; no real Founder secret.
    with (
        patch.object(founder_local_auth, "_identity", return_value="founder-test-uuid"),
        patch.object(founder_local_auth, "_session_secret", return_value=b"test-secret-not-for-production-123456789"),
    ):
        cookie = founder_local_auth.issue_session_cookie(now=1000).split(";", 1)[0]
        yield cookie


def test_real_signed_session_still_cannot_bypass_missing_server_evidence(founder_session):
    with patch("mission_control.founder_local_auth.time.time", return_value=1001):
        result = _gate(founder_session)
    assert result["allowed"] is False
    assert "trusted_server_evidence_required" in result["blockers"]


def test_real_signed_session_reaches_pure_decision_when_all_claims_are_supplied(founder_session):
    # Contract success is NOT evidence that supplied rights/ownership/etc are authentic.
    with patch("mission_control.founder_local_auth.time.time", return_value=1001):
        result = _gate(founder_session, trusted=True)
    assert result == {
        "allowed": True,
        "blockers": [],
        "public_playback_enabled": False,
        "media_bytes_served": False,
    }


@pytest.mark.parametrize("change", ["tamper", "expire", "mismatch"])
def test_invalid_signed_session_denies_even_with_other_claims(founder_session, change):
    cookie = founder_session
    if change == "tamper":
        cookie = cookie[:-1] + ("0" if cookie[-1] != "0" else "1")
    with patch("mission_control.founder_local_auth.time.time", return_value=200000 if change == "expire" else 1001):
        if change == "mismatch":
            with patch.object(founder_local_auth, "_identity", return_value="different-founder"):
                result = _gate(cookie, trusted=True)
        else:
            result = _gate(cookie, trusted=True)
    assert result["allowed"] is False
    assert "founder_authentication_required" in result["blockers"]


@pytest.mark.parametrize("field", ["owner", "entitlement", "integrity", "rights"])
def test_signed_session_does_not_override_missing_independent_claim(founder_session, field):
    kwargs = {"trusted": True}
    kwargs[field] = {} if field == "rights" else False
    with patch("mission_control.founder_local_auth.time.time", return_value=1001):
        result = _gate(founder_session, **kwargs)
    assert result["allowed"] is False


def test_no_endpoint_or_media_is_exercised(founder_session):
    with patch("mission_control.founder_local_auth.time.time", return_value=1001):
        result = _gate(founder_session)
    assert result["public_playback_enabled"] is False
    assert result["media_bytes_served"] is False
