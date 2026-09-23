"""BODY/SOUL bounded contract tests; shared Matrix has its own suite."""
from oap.raffles_body import dispatch
from oap.raffles_control import RafflesControl, State
from oap.raffles_mind import REQUIRED, assess
from oap.raffles_soul import PROTECTED, RELEASE_GATES, can_public_execute, review


def control():
    receipts = []
    def audit(*args):
        receipts.append(args)
        return len(receipts)
    return (RafflesControl("raffle-1", audit_writer=audit,
                           authority_checker=lambda actor: actor == "verified-authority"),
            receipts)


def test_body_blocks_live_execution_regardless_of_actor():
    c, events = control()
    for action in ("OPEN_ENTRIES", "TAKE_PAYMENT", "SELECT_WINNER", "PUBLISH",
                   "DELIVER_PRIZE", "SEND_MARKETING"):
        result = dispatch(c, action=action, actor="verified-authority")
        assert result.outcome == "BLOCKED_RELEASE_SCOPE"
        assert not result.execution_granted and not result.published
    assert not events and c.state == State.DRAFT


def test_body_stop_acknowledges_kernel_and_preserves_block():
    c, events = control()
    assert dispatch(c, action="STOP", actor="operator").outcome == "STOPPED"
    assert c.stopped and len(events) == 1
    assert dispatch(c, action="REVIEW", actor="operator").outcome == "BLOCKED_STOP"
    assert dispatch(c, action="RECOVER", actor="operator").outcome == "BLOCKED_FOUNDER_REQUIRED"
    assert dispatch(c, action="RECOVER", actor="verified-authority").outcome == "RECOVERED_TO_REVIEW"
    assert c.state == State.REVIEW and not c.stopped


def test_body_requires_mind_before_review_approval():
    c, _ = control()
    assert dispatch(c, action="APPROVE_FOR_REVIEW",
                    actor="verified-authority").outcome == "BLOCKED_MIND_NOT_READY"
    blocked = assess(territory="uk", kind="paid_skill", sponsor_funded=True,
                     evidence={key: "claim" for key in REQUIRED})
    assert dispatch(c, action="APPROVE_FOR_REVIEW", actor="verified-authority",
                    mind=blocked).outcome == "BLOCKED_MIND_NOT_READY"


def test_body_unknown_action_is_denied():
    c, _ = control()
    assert dispatch(c, action="MERGE_AND_DEPLOY", actor="verified-authority").outcome == "BLOCKED_UNKNOWN_ACTION"


def test_soul_minimises_sensitive_evidence_and_keeps_release_closed():
    submitted = {key: "private value" for key in PROTECTED}
    submitted["independent_legal_review"] = "unverified claim"
    result = review(evidence=submitted)
    assert not (PROTECTED & result.safe_evidence.keys())
    assert not result.release_allowed
    assert "verified_prize_fulfilment" in result.missing


def test_soul_all_claims_still_not_release_proof():
    result = review(evidence={key: "claim" for key in RELEASE_GATES},
                    territory="global")
    assert result.missing == ()
    assert not result.release_allowed
    assert not can_public_execute(founder_approved=True)


def test_soul_invalid_evidence_fails_closed():
    result = review(evidence={"identity_document": "secret",
                              "verified_prize_fulfilment": 123})
    assert "identity_document" not in result.safe_evidence
    assert "verified_prize_fulfilment" in result.missing
