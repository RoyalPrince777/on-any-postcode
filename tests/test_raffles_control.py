"""Offline tests for isolated Raffles controls; no prize or payment activity."""
from oap.raffles_control import RafflesControl, State, REQUIRED

def test_default_closed():
    c = RafflesControl("p1")
    assert c.state == State.DRAFT
    for action in ("open_entries", "take_payment", "select_winner", "publish", "deliver_prize"):
        assert c.control(action, "system")["outcome"] == "BLOCKED_RELEASE_SCOPE"
    assert c.verify_receipts()

def test_stop_and_recovery_founder_only():
    c = RafflesControl("p1")
    assert c.control("STOP", "operator")["outcome"] == "STOPPED"
    assert c.control("ADD_EVIDENCE", "operator", proof={"fulfilment": "doc"})["outcome"] == "BLOCKED_STOP"
    assert c.control("RECOVER", "operator")["outcome"] == "BLOCKED_FOUNDER_REQUIRED"
    assert c.control("RECOVER", "founder")["outcome"] == "RECOVERED_TO_REVIEW"
    assert c.state == State.REVIEW
    assert c.verify_receipts()

def test_evidence_does_not_authorise_release():
    c = RafflesControl("p1")
    assert c.control("APPROVE_FOR_REVIEW", "founder")["outcome"] == "BLOCKED_MISSING_EVIDENCE_OR_FOUNDER"
    assert c.control("ADD_EVIDENCE", "operator", proof={k: "unverified" for k in REQUIRED})["outcome"] == "RECORDED_UNVERIFIED_EVIDENCE"
    assert c.control("REVIEW", "operator")["outcome"] == "ESCALATE_INDEPENDENT_REVIEW"
    assert c.control("APPROVE_FOR_REVIEW", "operator")["outcome"] == "BLOCKED_MISSING_EVIDENCE_OR_FOUNDER"
    assert c.control("APPROVE_FOR_REVIEW", "founder")["outcome"] == "APPROVED_FOR_REVIEW_NOT_RELEASE"
    assert c.control("open_entries", "founder")["outcome"] == "BLOCKED_RELEASE_SCOPE"
    assert c.verify_receipts()

def test_tamper_detected():
    c = RafflesControl("p1")
    c.control("STOP", "operator")
    c.receipts[0]["outcome"] = "OPEN"
    assert not c.verify_receipts()

def test_invalid_and_unknown_actions_blocked():
    c = RafflesControl("p1")
    assert c.control("ADD_EVIDENCE", "operator", proof={"unknown": "doc"})["outcome"] == "BLOCKED_INVALID_PROOF"
    assert c.control("MAGIC_APPROVE", "operator")["outcome"] == "BLOCKED_UNKNOWN_ACTION"

def test_stop_is_idempotent_and_blocks_all_execution():
    c = RafflesControl("p1")
    assert c.control("STOP", "operator")["outcome"] == "STOPPED"
    assert c.control("STOP", "operator")["outcome"] == "STOPPED"
    for action in ("open_entries", "take_payment", "select_winner", "publish", "deliver_prize"):
        assert c.control(action, "founder")["outcome"] == "BLOCKED_STOP"
    assert c.state == State.STOPPED
    assert c.verify_receipts()

def test_audit_chain_detects_missing_middle_receipt():
    c = RafflesControl("p1")
    c.control("REVIEW", "operator")
    c.control("STOP", "operator")
    c.control("RECOVER", "founder")
    assert c.verify_receipts()
    c.receipts.pop(1)
    assert not c.verify_receipts()
