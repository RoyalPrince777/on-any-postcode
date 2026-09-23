"""Raffles domain tests; Matrix, canonical audit and authority tested in their own suites."""
import pytest

from oap.raffles_control import REQUIRED, RafflesControl, State


def make_control():
    events = []
    def audit(campaign, action, actor, outcome):
        events.append((campaign, action, actor, outcome))
        return len(events)
    c = RafflesControl("p1", audit_writer=audit,
                       authority_checker=lambda actor: actor == "verified-founder-uuid")
    return c, events


def test_default_closed():
    c, events = make_control()
    assert c.state == State.DRAFT
    for action in ("open_entries", "take_payment", "select_winner", "publish", "deliver_prize"):
        assert c.control(action, "system")["outcome"] == "BLOCKED_RELEASE_SCOPE"
    assert len(events) == 5


def test_stop_and_recovery_authority_adapter():
    c, _ = make_control()
    assert c.control("STOP", "operator")["outcome"] == "STOPPED"
    assert c.control("ADD_EVIDENCE", "operator", proof={"fulfilment": "doc"})["outcome"] == "BLOCKED_STOP"
    assert c.control("RECOVER", "founder")["outcome"] == "BLOCKED_FOUNDER_REQUIRED"
    assert c.control("RECOVER", "verified-founder-uuid")["outcome"] == "RECOVERED_TO_REVIEW"
    assert c.state == State.REVIEW


def test_evidence_does_not_authorise_release():
    c, _ = make_control()
    assert c.control("APPROVE_FOR_REVIEW", "verified-founder-uuid")["outcome"] == "BLOCKED_MISSING_EVIDENCE_OR_FOUNDER"
    assert c.control("ADD_EVIDENCE", "operator", proof={k: "unverified" for k in REQUIRED})["outcome"] == "RECORDED_UNVERIFIED_EVIDENCE"
    assert c.control("REVIEW", "operator")["outcome"] == "ESCALATE_TO_CANONICAL_MATRIX_REVIEW"
    assert c.control("APPROVE_FOR_REVIEW", "founder")["outcome"] == "BLOCKED_MISSING_EVIDENCE_OR_FOUNDER"
    assert c.control("APPROVE_FOR_REVIEW", "verified-founder-uuid")["outcome"] == "APPROVED_FOR_REVIEW_NOT_RELEASE"
    assert c.control("open_entries", "verified-founder-uuid")["outcome"] == "BLOCKED_RELEASE_SCOPE"


def test_canonical_audit_absent_fails_closed():
    c = RafflesControl("p1", authority_checker=lambda _: True)
    with pytest.raises(RuntimeError, match="canonical_audit_required"):
        c.control("STOP", "operator")
    assert c.state == State.DRAFT and not c.stopped


def test_invalid_and_unknown_actions_blocked():
    c, _ = make_control()
    assert c.control("ADD_EVIDENCE", "operator", proof={"unknown": "doc"})["outcome"] == "BLOCKED_INVALID_PROOF"
    assert c.control("MAGIC_APPROVE", "operator")["outcome"] == "BLOCKED_UNKNOWN_ACTION"


def test_stop_is_idempotent_and_blocks_all_execution():
    c, _ = make_control()
    assert c.control("STOP", "operator")["outcome"] == "STOPPED"
    assert c.control("STOP", "operator")["outcome"] == "STOPPED"
    for action in ("open_entries", "take_payment", "select_winner", "publish", "deliver_prize"):
        assert c.control(action, "verified-founder-uuid")["outcome"] == "BLOCKED_STOP"
    assert c.state == State.STOPPED


def test_audit_failure_prevents_mutation():
    def failed_audit(*_):
        raise RuntimeError("audit_unavailable")
    c = RafflesControl("p1", audit_writer=failed_audit,
                       authority_checker=lambda _: True)
    with pytest.raises(RuntimeError, match="audit_unavailable"):
        c.control("STOP", "operator")
    assert not c.stopped and c.state == State.DRAFT
    with pytest.raises(RuntimeError, match="audit_unavailable"):
        c.control("ADD_EVIDENCE", "operator", proof={"fulfilment": "doc"})
    assert c.evidence == {}


def test_unconfirmed_audit_and_missing_authority_fail_closed():
    c = RafflesControl("p1", audit_writer=lambda *_: None)
    with pytest.raises(RuntimeError, match="canonical_audit_unconfirmed"):
        c.control("STOP", "operator")
    assert not c.stopped
    c.audit_writer = lambda *_: 1
    c.control("STOP", "operator")
    assert c.control("RECOVER", "founder")["outcome"] == "BLOCKED_FOUNDER_REQUIRED"
    assert c.stopped
