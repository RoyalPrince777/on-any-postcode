from __future__ import annotations

import pytest

from mission_control import recursive_self_improvement as rsi
from mission_control import smi_receipt_backend


class ReadOnlyReviewStore:
    def __init__(self, row):
        self.row = row
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def cursor(self):
        return self

    def execute(self, query, parameters=None):
        self.calls.append((query, parameters))

    def fetchone(self):
        return self.row


def review_row(proposal_id="RSI-123", signal_id="MATRIX-SIGNAL-123"):
    return {
        "receipt_id": "review-123",
        "receipt_kind": "war_room_live_proof_receipt",
        "brain_part": "matrix",
        "command": "matrix_review_outcome",
        "payload_json": {
            "proposal_id": proposal_id,
            "signal_id": signal_id,
            "review_mode": "first_party_matrix_review",
            "evidence_verified": True,
            "reviewed": True,
            "founder_approved": True,
            "guardian_pass": True,
            "green_gate_pass": True,
            "execution_granted": False,
        },
    }


def test_missing_independent_hrm_configuration_blocks_review(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(smi_receipt_backend, "_hrm_database_url", lambda: "")
    result = smi_receipt_backend.verify_matrix_review_outcome(
        "review-123", proposal_id="RSI-123", signal_id="MATRIX-SIGNAL-123"
    )
    assert result["verified"] is False
    assert result["authority_granted"] is False


@pytest.mark.parametrize(
    "mutation",
    [
        {"receipt_kind": "matrix_learning_receipt"},
        {"brain_part": "recursive_self_improvement"},
        {"command": "war_room"},
        {"receipt_id": "another-review"},
        {"payload_json": {"proposal_id": "RSI-other"}},
        {"payload_json": {"signal_id": "MATRIX-SIGNAL-other"}},
        {"payload_json": {"review_mode": "canonical_seven_bounded_rule_lenses"}},
        {"payload_json": {"evidence_verified": False}},
        {"payload_json": {"founder_approved": False}},
        {"payload_json": {"guardian_pass": False}},
        {"payload_json": {"green_gate_pass": False}},
        {"payload_json": {"execution_granted": True}},
    ],
)
def test_unsupported_or_mismatched_review_is_never_verified(
    monkeypatch: pytest.MonkeyPatch, mutation: dict
) -> None:
    row = review_row()
    for key, value in mutation.items():
        if key == "payload_json":
            row[key].update(value)
        else:
            row[key] = value
    store = ReadOnlyReviewStore(row)
    monkeypatch.setattr(smi_receipt_backend, "_hrm_database_url", lambda: "configured")
    monkeypatch.setattr(smi_receipt_backend, "_connect_postgres", lambda: store)
    result = smi_receipt_backend.verify_matrix_review_outcome(
        "review-123", proposal_id="RSI-123", signal_id="MATRIX-SIGNAL-123"
    )
    assert result["verified"] is False
    assert result["authority_granted"] is False
    assert store.calls[0][0] == "SET TRANSACTION READ ONLY"


def test_matching_stored_review_is_not_an_agent_vote_or_authority(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = ReadOnlyReviewStore(review_row())
    monkeypatch.setattr(smi_receipt_backend, "_hrm_database_url", lambda: "configured")
    monkeypatch.setattr(smi_receipt_backend, "_connect_postgres", lambda: store)
    result = smi_receipt_backend.verify_matrix_review_outcome(
        "review-123", proposal_id="RSI-123", signal_id="MATRIX-SIGNAL-123"
    )
    assert result["verified"] is False
    assert result["status"] == "matched_legacy_fields_producer_unattested"
    assert result["actual_votes_proven"] is False
    assert result["authority_granted"] is False
    assert store.calls[1][1] == ("review-123",)


def test_unverified_review_never_writes_learning_receipt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected_write(*_args, **_kwargs):
        raise AssertionError("unverified review must not write learning")

    monkeypatch.setattr(smi_receipt_backend, "write_receipt", unexpected_write)
    monkeypatch.setattr(
        smi_receipt_backend,
        "verify_matrix_review_outcome",
        lambda *args, **kwargs: {"verified": False, "status": "review_unverified"},
    )
    proposal = {
        "proposal_id": "RSI-123",
        "matrix_signal": {"signal_id": "MATRIX-SIGNAL-123"},
    }
    result = rsi.record_learning(
        proposal,
        outcome="reviewed",
        before_state="before",
        after_state="after",
        lesson="do not trust supplied receipt IDs",
        tests_passed=True,
        rollback_available=True,
        reviewed_outcome_ref="review-123",
    )
    assert result["state"] == "reviewed_outcome_unverified"
    assert result["receipt"] is None
    assert result["matrix_update_allowed"] is False
    assert result["execution_granted"] is False
    assert result["full_green"] is False


def test_matching_legacy_review_cannot_create_learning_receipt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A pre-reservation matching row is not independent producer proof."""
    store = ReadOnlyReviewStore(review_row())
    monkeypatch.setattr(smi_receipt_backend, "_hrm_database_url", lambda: "configured")
    monkeypatch.setattr(smi_receipt_backend, "_connect_postgres", lambda: store)

    def unexpected_write(*_args, **_kwargs):
        raise AssertionError("Unattested legacy review cannot write HRM learning")

    monkeypatch.setattr(smi_receipt_backend, "write_receipt", unexpected_write)
    proposal = {
        "proposal_id": "RSI-123",
        "matrix_signal": {"signal_id": "MATRIX-SIGNAL-123"},
    }
    result = rsi.record_learning(
        proposal,
        outcome="historical row claims approval",
        before_state="before",
        after_state="after",
        lesson="self-declared fields are not independent provenance",
        tests_passed=True,
        rollback_available=True,
        reviewed_outcome_ref="review-123",
    )
    assert result["state"] == "reviewed_outcome_unverified"
    assert result["review_proof"]["status"] == (
        "matched_legacy_fields_producer_unattested"
    )
    assert result["receipt"] is None
    assert result["matrix_update_allowed"] is False
    assert result["full_green"] is False
