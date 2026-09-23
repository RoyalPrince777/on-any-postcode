"""Isolated Mind / Body / Soul tests: never invoke providers or databases."""
import pytest

from mission_control.pod_supplier_contract import (
    PODContractError, PODIntent, PODOrder, PODState, Quote, Supplier,
)

SELLER = "11111111-1111-4111-8111-111111111111"
BUYER = "22222222-2222-4222-8222-222222222222"
ORDER = "33333333-3333-4333-8333-333333333333"
PRODUCT = "44444444-4444-4444-8444-444444444444"
SUPPLIER = "55555555-5555-4555-8555-555555555555"
OTHER = "66666666-6666-4666-8666-666666666666"


def intent(*, merchant=True, rights=True, approved=True, multi=True, country="GB"):
    order = PODOrder(ORDER, SELLER, BUYER, PRODUCT, "hoodie", country, 2,
                     "oap-artwork:original/001", rights, merchant, True)
    supplier = Supplier(SUPPLIER, "Contracted print supplier", approved,
                        frozenset({"hoodie"}), frozenset({"GB"}), multi)
    quote = Quote(SUPPLIER, "hoodie-blue-xl", 3500, 400, "GBP",
                  "supplier-quote:001", country, "hoodie", 2)
    return PODIntent(order, supplier, quote, "oap-order:one-001")


def test_mind_body_soul_success_stays_isolated():
    p = intent()
    p.quote_ready(SELLER)
    assert p.state == PODState.QUOTED
    p.approve(SELLER, "founder-approved:001")
    payload = p.prepare_handoff(SELLER, "founder-approved:001")
    assert payload["external_execution_performed"] is False
    assert payload["payment_performed"] is False
    assert "buyer_id" not in payload
    assert p.state == PODState.APPROVED
    p.record_submission(SELLER, "supplier-submitted:001")
    p.record_receipt(SELLER, "supplier-submitted:001", "supplier-accepted:001")
    assert p.state == PODState.ACCEPTED
    assert p.safe_to_retry is False
    assert len(p.events) == 4


@pytest.mark.parametrize("changes,code", [
    ({"merchant": False}, "merchant_or_fulfilment_gate"),
    ({"rights": False}, "artwork_rights_unconfirmed"),
    ({"approved": False}, "supplier_not_authorised_for_platform"),
    ({"multi": False}, "supplier_not_authorised_for_platform"),
    ({"country": "GH"}, "supplier_cannot_fulfil_order"),
])
def test_mind_fails_closed(changes, code):
    with pytest.raises(PODContractError, match=code):
        intent(**changes).quote_ready(SELLER)


def test_unauthorised_actor_rejected_at_every_step():
    p = intent()
    with pytest.raises(PODContractError, match="seller_not_owned"):
        p.quote_ready(OTHER)
    p.quote_ready(SELLER)
    with pytest.raises(PODContractError, match="seller_not_owned"):
        p.approve(OTHER, "approval")
    p.approve(SELLER, "approval")
    with pytest.raises(PODContractError, match="approval_owner_mismatch"):
        p.prepare_handoff(OTHER, "approval")
    with pytest.raises(PODContractError, match="approval_receipt_mismatch"):
        p.prepare_handoff(SELLER, "wrong")
    with pytest.raises(PODContractError, match="seller_not_owned"):
        p.stop(OTHER, "stop")


def test_stop_before_submitting_blocks_handoff():
    p = intent()
    p.quote_ready(SELLER)
    p.approve(SELLER, "approval")
    p.stop(SELLER, "owner-stop")
    assert p.state == PODState.STOPPED
    assert p.safe_to_retry is False
    with pytest.raises(PODContractError, match="not_approved"):
        p.prepare_handoff(SELLER, "approval")


def test_post_submission_stop_requires_reconciliation():
    p = intent()
    p.quote_ready(SELLER)
    p.approve(SELLER, "approval")
    p.record_submission(SELLER, "remote-ref")
    p.stop(SELLER, "owner-stop")
    assert p.state == PODState.RECOVERY_REQUIRED
    assert p.safe_to_retry is False
    with pytest.raises(PODContractError, match="not_submitted"):
        p.record_receipt(SELLER, "remote-ref", "late-acceptance")


def test_receipt_must_match_submission_and_has_no_fake_green():
    p = intent()
    p.quote_ready(SELLER)
    p.approve(SELLER, "approval")
    with pytest.raises(PODContractError, match="not_submitted"):
        p.record_receipt(SELLER, "none", "accepted")
    p.record_submission(SELLER, "submitted")
    with pytest.raises(PODContractError, match="submission_receipt_mismatch"):
        p.record_receipt(SELLER, "different", "accepted")
    assert p.state == PODState.SUBMITTED
    p.fail("provider-timeout")
    assert p.state == PODState.RECOVERY_REQUIRED
    assert p.safe_to_retry is False


def test_supplier_and_quote_mismatch_fail_closed():
    p = intent()
    p.quote = Quote(OTHER, "hoodie-blue-xl", 3500, 400, "GBP",
                    "quote", "GB", "hoodie", 2)
    with pytest.raises(PODContractError, match="quote_order_mismatch"):
        p.quote_ready(SELLER)


def test_no_external_execution_switch_and_money_validation():
    with pytest.raises(PODContractError, match="external_execution_not_supported"):
        Supplier(SUPPLIER, "supplier", True, frozenset({"hoodie"}),
                 frozenset({"GB"}), True, True)
    with pytest.raises(PODContractError, match="invalid_amount_minor"):
        Quote(SUPPLIER, "variant", -1, 0, "GBP", "quote", "GB", "hoodie", 1)
    with pytest.raises(PODContractError, match="invalid_shipping_minor"):
        Quote(SUPPLIER, "variant", 100, True, "GBP", "quote", "GB", "hoodie", 1)


def test_missing_submission_evidence_leaves_approved_state_unchanged():
    p = intent()
    p.quote_ready(SELLER)
    p.approve(SELLER, "approval")
    with pytest.raises(PODContractError, match="submission_evidence_required"):
        p.record_submission(SELLER, "")
    assert p.state == PODState.APPROVED
    assert p.submission_reference is None


def test_missing_receipt_evidence_cannot_mark_accepted():
    p = intent()
    p.quote_ready(SELLER)
    p.approve(SELLER, "approval")
    p.record_submission(SELLER, "external-id")
    with pytest.raises(PODContractError, match="receipt_evidence_required"):
        p.record_receipt(SELLER, "external-id", "")
    assert p.state == PODState.SUBMITTED
    assert p.receipt_reference is None


def test_missing_approval_receipt_cannot_set_approver():
    p = intent()
    p.quote_ready(SELLER)
    with pytest.raises(PODContractError, match="evidence_required"):
        p.approve(SELLER, "")
    assert p.state == PODState.QUOTED
    assert p.approved_by is None
