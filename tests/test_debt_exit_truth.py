"""Synthetic only: Debt Truth never acts on real financial records."""
from __future__ import annotations

from dataclasses import fields

import pytest

from mission_control.debt_exit_truth import (
    Action, CasePhase, DebtCase, TransitionDenied, new_case, transition,
)

OWNER = "owner_0001"
CASE = "case_00001"
REF = "record_0001"


def apply(case, action, *, principal=OWNER, version=None, ref=REF):
    return transition(
        case, action, authenticated_identity_id=principal,
        expected_version=case.version if version is None else version,
        evidence_ref=ref,
    )


def test_document_is_not_verification():
    c, receipt = apply(new_case(CASE, OWNER), Action.RECORD_DOCUMENT)
    assert c.documented and not c.outcome_verified and not c.debt_discharged
    assert {f.name for f in fields(receipt)} == {"case_id", "version", "event"}


def test_dispute_survives_outcome_and_closure():
    c, _ = apply(new_case(CASE, OWNER), Action.DISPUTE)
    c, _ = apply(c, Action.RECORD_OUTCOME)
    c, _ = apply(c, Action.CLOSE)
    assert c.disputed and c.outcome_recorded and not c.debt_discharged
    assert c.phase is CasePhase.CLOSED


@pytest.mark.parametrize("action", [
    Action.VERIFY_OUTCOME, Action.MAKE_PAYMENT, Action.SETTLE_DEBT,
    Action.CONTACT_CREDITOR, Action.ERASE_OBLIGATION,
])
def test_no_financial_or_unverified_claim(action):
    with pytest.raises(TransitionDenied, match="action_not_supported"):
        apply(new_case(CASE, OWNER), action)


@pytest.mark.parametrize("field", ["outcome_verified", "debt_discharged"])
def test_forged_financial_state_rejected(field):
    with pytest.raises(TransitionDenied, match="unsupported_financial_claim"):
        DebtCase(CASE, OWNER, **{field: True})


def test_stop_blocks_evidence_and_reopen_preserves_dispute():
    c, _ = apply(new_case(CASE, OWNER), Action.DISPUTE)
    c, _ = apply(c, Action.STOP)
    with pytest.raises(TransitionDenied, match="invalid_phase"):
        apply(c, Action.RECORD_DOCUMENT)
    c, _ = apply(c, Action.REOPEN)
    assert c.disputed and not c.debt_discharged


def test_unknown_owner_and_stale_version_rejected():
    case = new_case(CASE, OWNER)
    with pytest.raises(TransitionDenied, match="access_denied"):
        apply(case, Action.DISPUTE, principal="owner_0002")
    with pytest.raises(TransitionDenied, match="stale_case_version"):
        apply(case, Action.DISPUTE, version=12)


def test_mutated_forged_state_is_rechecked():
    c = new_case(CASE, OWNER)
    object.__setattr__(c, "outcome_verified", True)
    with pytest.raises(TransitionDenied, match="unsupported_financial_claim"):
        apply(c, Action.STOP)


@pytest.mark.parametrize("bad", [-1, True, "1"])
def test_invalid_versions_fail_closed(bad):
    with pytest.raises(TransitionDenied, match="invalid_case"):
        DebtCase(CASE, OWNER, version=bad)


def test_initial_case_cannot_claim_history():
    with pytest.raises(TransitionDenied, match="invalid_case"):
        DebtCase(CASE, OWNER, documented=True)
