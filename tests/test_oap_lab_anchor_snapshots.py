"""Synthetic verification of two LAB recovery read-back snapshots."""
import json
from hashlib import sha256
from uuid import UUID

import pytest

from mission_control.oap_lab_claim_edge import ClaimEdgeBlocked
from mission_control.oap_lab_recovery_readback import (
    verify_separate_readback_snapshots,
)

OWNER = str(UUID(int=1))
OTHER = str(UUID(int=2))
CLAIM = str(UUID(int=3))
OTHER_CLAIM = str(UUID(int=4))


def snapshots():
    state = {
        "owner_id": OWNER,
        "claim_id": CLAIM,
        "scientific_truth_established": False,
        "canonical_promotion_authorised": False,
        "publication_authorised": False,
        "execution_authorised": False,
    }
    record = {"version": 1, "previous_hash": "GENESIS", "state": state}
    anchor = sha256(
        json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    history = {
        "owner_id": OWNER, "claim_id": CLAIM, "storage_namespace": "history-store",
        "retrieval_id": "history-read-1",
        "records": ({**record, "receipt_hash": anchor},),
    }
    anchor_record = {
        "owner_id": OWNER, "claim_id": CLAIM, "storage_namespace": "anchor-store",
        "retrieval_id": "anchor-read-2", "last_hash": anchor,
    }
    return history, anchor_record


def test_distinct_snapshots_prove_only_supplied_metadata():
    history, anchor = snapshots()
    result = verify_separate_readback_snapshots(
        history, anchor, authenticated_owner_id=OWNER,
    )
    assert result["distinct_declared_namespaces"] is True
    assert result["distinct_retrieval_references"] is True
    assert result["history_integrity_verified"] is True
    assert result["external_store_readback_verified"] is False
    assert result["namespace_independence_authenticated"] is False
    assert result["durable_persistence_verified"] is False
    assert result["execution_authorised"] is False


@pytest.mark.parametrize("which,key,value", [
    ("history", "owner_id", OTHER),
    ("anchor", "owner_id", OTHER),
    ("anchor", "claim_id", OTHER_CLAIM),
    ("anchor", "storage_namespace", "history-store"),
    ("anchor", "retrieval_id", "history-read-1"),
    ("anchor", "last_hash", "0" * 64),
    ("anchor", "last_hash", None),
    ("history", "records", ()),
])
def test_scope_separation_and_anchor_fail_closed(which, key, value):
    history, anchor = snapshots()
    target = history if which == "history" else anchor
    target[key] = value
    with pytest.raises(ClaimEdgeBlocked):
        verify_separate_readback_snapshots(
            history, anchor, authenticated_owner_id=OWNER,
        )


def test_stop_and_missing_snapshots_fail_closed():
    history, anchor = snapshots()
    with pytest.raises(ClaimEdgeBlocked, match="stop_asserted"):
        verify_separate_readback_snapshots(
            history, anchor, authenticated_owner_id=OWNER, stopped=True,
        )
    for left, right in ((None, anchor), (history, None)):
        with pytest.raises(ClaimEdgeBlocked):
            verify_separate_readback_snapshots(
                left, right, authenticated_owner_id=OWNER,
            )


def test_rehashed_restored_authority_still_rejected():
    history, anchor = snapshots()
    state = {**history["records"][0]["state"], "execution_authorised": True}
    record = {"version": 1, "previous_hash": "GENESIS", "state": state}
    digest = sha256(
        json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    history["records"] = ({**record, "receipt_hash": digest},)
    anchor["last_hash"] = digest
    with pytest.raises(ClaimEdgeBlocked, match="recovery_cannot_restore_authority"):
        verify_separate_readback_snapshots(
            history, anchor, authenticated_owner_id=OWNER,
        )


@pytest.mark.parametrize("which,key,value", [
    ("anchor", "storage_namespace", " history-store "),
    ("anchor", "retrieval_id", " history-read-1 "),
])
def test_cosmetic_whitespace_cannot_prove_snapshot_separation(which, key, value):
    history, anchor = snapshots()
    target = history if which == "history" else anchor
    target[key] = value
    with pytest.raises(ClaimEdgeBlocked):
        verify_separate_readback_snapshots(
            history, anchor, authenticated_owner_id=OWNER,
        )


@pytest.mark.parametrize("invalid_stop", [0, None, "false", "true"])
def test_soul_snapshot_readback_requires_explicit_stop_state(invalid_stop):
    history, anchor = snapshots()
    with pytest.raises(ClaimEdgeBlocked, match="explicit_stop_state_required"):
        verify_separate_readback_snapshots(
            history, anchor, authenticated_owner_id=OWNER, stopped=invalid_stop,
        )


@pytest.mark.parametrize("claimed_flag", [
    "external_store_readback_verified",
    "namespace_independence_authenticated",
    "anchor_authenticity_verified",
    "independent_recovery_verified",
    "release_ready",
])
def test_supplied_provenance_claim_cannot_green_recovery_or_release(claimed_flag):
    history, anchor = snapshots()
    history[claimed_flag] = True
    anchor[claimed_flag] = True
    outcome = verify_separate_readback_snapshots(
        history, anchor, authenticated_owner_id=OWNER,
    )
    assert outcome["history_integrity_verified"] is True
    for key in (
        "external_store_readback_verified",
        "namespace_independence_authenticated",
        "anchor_authenticity_verified",
        "independent_recovery_verified",
        "release_ready",
    ):
        assert outcome[key] is False
    assert outcome["resume_mode"] == "review_only"
    assert outcome["scientific_truth_established"] is False
    assert outcome["execution_authorised"] is False
