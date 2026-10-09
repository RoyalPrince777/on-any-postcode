"""Security regression tests for the OAP TV private playback decision boundary."""
import pytest

from mission_control.tv_private_playback_gate import authorize_private_playback


def _rights_allow():
    return {
        "decision": "ALLOW",
        "decision_hash": "e" * 64,
        "evidence_hashes": ["a" * 64],
        "authority_receipt_hashes": ["b" * 64],
        "human_approval_receipt_hashes": ["c" * 64],
        "public_distribution_authorized": False,
    }


def _proofs():
    return dict(
        founder_authenticated=True,
        owner_identity_matches=True,
        rights_decision=_rights_allow(),
        entitlement_proven=True,
        storage_integrity_proven=True,
    )


def test_all_independent_proofs_are_required():
    result = authorize_private_playback(**_proofs())
    assert result["allowed"] is True
    assert result["blockers"] == []
    assert result["public_playback_enabled"] is False
    assert result["media_bytes_served"] is False


@pytest.mark.parametrize("field,reason", [
    ("founder_authenticated", "founder_authentication_required"),
    ("owner_identity_matches", "asset_owner_mismatch"),
    ("entitlement_proven", "entitlement_not_proven"),
    ("storage_integrity_proven", "storage_integrity_not_proven"),
])
@pytest.mark.parametrize("missing", [False, None, 1, "true"])
def test_missing_or_non_boolean_proofs_fail_closed(field, reason, missing):
    proofs = _proofs()
    proofs[field] = missing
    result = authorize_private_playback(**proofs)
    assert result["allowed"] is False
    assert reason in result["blockers"]


@pytest.mark.parametrize("rights", [
    None, {}, {"decision": "ALLOW"}, {"decision": "BLOCK"},
    {"decision": "ALLOW", "decision_hash": "e" * 64},
])
def test_missing_or_self_asserted_rights_never_unlock_playback(rights):
    proofs = _proofs()
    proofs["rights_decision"] = rights
    result = authorize_private_playback(**proofs)
    assert result["allowed"] is False
    assert "canonical_rights_allow_not_proven" in result["blockers"]
