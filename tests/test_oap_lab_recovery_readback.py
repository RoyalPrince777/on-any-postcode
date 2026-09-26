"""Synthetic read-back: no database, migrations or authority restoration."""
import json
from hashlib import sha256
from uuid import UUID

import pytest

from mission_control.oap_lab_claim_edge import ClaimEdgeBlocked
from mission_control.oap_lab_recovery_readback import verify_lab_readback

OWNER = str(UUID(int=1))
OTHER = str(UUID(int=2))
CLAIM = str(UUID(int=3))
OTHER_CLAIM = str(UUID(int=4))


def history():
    previous = "GENESIS"
    records = []
    for number in (1, 2):
        state = {
            "owner_id": OWNER, "claim_id": CLAIM,
            "version_state": f"review-{number}",
            "scientific_truth_established": False,
            "canonical_promotion_authorised": False,
            "publication_authorised": False,
            "execution_authorised": False,
        }
        payload = {"version": number, "previous_hash": previous, "state": state}
        digest = sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        records.append({**payload, "receipt_hash": digest})
        previous = digest
    return tuple(records), previous


def verify(records=None, anchor=None, **changes):
    standard, last_hash = history()
    values = {
        "expected_last_hash": last_hash if anchor is None else anchor,
        "authenticated_owner_id": OWNER,
        "stored_owner_id": OWNER,
        "stored_claim_id": CLAIM,
        "anchor_owner_id": OWNER,
        "anchor_claim_id": CLAIM,
        "anchor_retained_separately": True,
    }
    values.update(changes)
    return verify_lab_readback(standard if records is None else records, **values)


def test_review_only_readback_never_claims_persistence():
    result = verify()
    assert result["history_integrity_verified"] is True
    assert result["readback_matches_supplied_anchor"] is True
    assert result["durable_persistence_verified"] is False
    assert result["independent_anchor_authenticity_verified"] is False
    assert result["execution_authorised"] is False


@pytest.mark.parametrize("changes", [
    {"authenticated_owner_id": OTHER},
    {"stored_owner_id": OTHER},
    {"anchor_owner_id": OTHER},
    {"anchor_claim_id": OTHER_CLAIM},
    {"anchor_retained_separately": False},
    {"stopped": True},
])
def test_stop_owner_and_anchor_scope_fail_closed(changes):
    with pytest.raises(ClaimEdgeBlocked):
        verify(**changes)


def test_tampered_truncated_reordered_and_missing_history_fail_closed():
    records, anchor = history()
    forged = ({**records[0], "state": {**records[0]["state"], "version_state": "approved"}}, records[1])
    for candidate in (forged, records[:1], records[::-1], ()):
        with pytest.raises(ClaimEdgeBlocked):
            verify(records=candidate, anchor=anchor)


def test_wrong_or_missing_anchor_rejected():
    for anchor in ("0" * 64, "bad"):
        with pytest.raises(ClaimEdgeBlocked):
            verify(anchor=anchor)


def test_recovery_cannot_restore_execution_even_after_rehash():
    records, anchor = history()
    state = {**records[0]["state"], "execution_authorised": True}
    payload = {"version": 1, "previous_hash": "GENESIS", "state": state}
    digest = sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    forged = ({**payload, "receipt_hash": digest}, records[1])
    with pytest.raises(ClaimEdgeBlocked, match="recovery_cannot_restore_authority"):
        verify(records=forged, anchor=anchor)


def test_cross_claim_history_rejected():
    records, anchor = history()
    altered = ({**records[0], "state": {**records[0]["state"], "claim_id": OTHER_CLAIM}}, records[1])
    with pytest.raises(ClaimEdgeBlocked, match="recovery_record_scope_mismatch"):
        verify(records=altered, anchor=anchor)


@pytest.mark.parametrize("invalid_stop", [0, None, "false", "true"])
def test_soul_direct_readback_requires_explicit_stop_state(invalid_stop):
    with pytest.raises(ClaimEdgeBlocked, match="explicit_stop_state_required"):
        verify(stopped=invalid_stop)


def test_direct_readback_cannot_claim_independent_recovery_or_release():
    result = verify()
    assert result["history_integrity_verified"] is True
    assert result["independent_recovery_verified"] is False
    assert result["release_ready"] is False
    assert result["resume_mode"] == "review_only"
    assert result["scientific_truth_established"] is False
    assert result["execution_authorised"] is False


@pytest.mark.parametrize("key,value", [
    ("storage_authenticity_verified", True),
    ("independent_anchor_authenticity_verified", True),
    ("durable_persistence_verified", True),
    ("external_store_readback_verified", True),
    ("namespace_independence_authenticated", True),
    ("anchor_authenticity_verified", True),
    ("independent_recovery_verified", True),
    ("release_ready", True),
    ("release_ready", "false"),
    ("resume_mode", "execute"),
])
def test_rehashed_history_cannot_restore_store_proof_or_release(key, value):
    records, _ = history()
    state = {**records[0]["state"], key: value}
    payload = {"version": 1, "previous_hash": "GENESIS", "state": state}
    digest = sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    second = {
        "version": 2, "previous_hash": digest, "state": records[1]["state"],
    }
    second_digest = sha256(
        json.dumps(second, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    with pytest.raises(ClaimEdgeBlocked, match="recovery_cannot_restore_authority"):
        verify(records=({**payload, "receipt_hash": digest},
                        {**second, "receipt_hash": second_digest}), anchor=second_digest)
