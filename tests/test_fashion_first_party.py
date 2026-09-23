"""Regression tests for the isolated OAP-owned Fashion core."""
import pytest

from mission_control.fashion_first_party import (
    FashionDraft, FashionError, FashionState, FashionVariant,
)

OWNER = "11111111-1111-4111-8111-111111111111"
OTHER = "22222222-2222-4222-8222-222222222222"
PRODUCT = "33333333-3333-4333-8333-333333333333"


def draft(*, certified=True, rights=True):
    return FashionDraft(
        OWNER, PRODUCT, "OAP Original Hoodie", "hoodie", "oap:art/hoodie-001",
        rights, certified, (
            FashionVariant("OAP-HOODIE-001", "XL", "Black", 3500),
            FashionVariant("OAP-HOODIE-002", "L", "Gold", 3500),
        ),
    )


def test_first_party_review_to_market_projection_has_no_external_actions():
    p = draft()
    p.submit_review(OWNER, "review:original-artwork")
    p.approve(OWNER, "human-approved:001", human_approval=True)
    projected = p.market_projection(OWNER)
    assert p.state == FashionState.APPROVED
    assert len(projected["variants"]) == 2
    assert projected["publication_performed"] is False
    assert projected["stock_confirmed"] is False
    assert projected["manufacturing_order_performed"] is False
    assert projected["payment_performed"] is False
    assert projected["external_supplier_required"] is False
    assert len(p.events) == 2


@pytest.mark.parametrize("certified,rights,error", [
    (False, True, "certified_merchant_required"),
    (True, False, "artwork_rights_required"),
])
def test_review_fails_closed(certified, rights, error):
    p = draft(certified=certified, rights=rights)
    with pytest.raises(FashionError, match=error):
        p.submit_review(OWNER, "review")
    assert p.state == FashionState.DRAFT


def test_owner_scope_applies_to_review_approval_stop_and_projection():
    p = draft()
    with pytest.raises(FashionError, match="not_product_owner"):
        p.submit_review(OTHER, "review")
    p.submit_review(OWNER, "review")
    with pytest.raises(FashionError, match="not_product_owner"):
        p.approve(OTHER, "approval", human_approval=True)
    with pytest.raises(FashionError, match="not_product_owner"):
        p.stop(OTHER, "stop")
    p.approve(OWNER, "approval", human_approval=True)
    with pytest.raises(FashionError, match="not_product_owner"):
        p.market_projection(OTHER)


def test_no_auto_approval_or_fake_publication():
    p = draft()
    with pytest.raises(FashionError, match="product_not_approved"):
        p.market_projection(OWNER)
    p.submit_review(OWNER, "review")
    with pytest.raises(FashionError, match="human_approval_required"):
        p.approve(OWNER, "approval", human_approval=False)
    assert p.state == FashionState.READY_FOR_REVIEW


def test_stop_is_terminal_and_has_evidence():
    p = draft()
    p.stop(OWNER, "owner-stopped")
    assert p.state == FashionState.STOPPED
    with pytest.raises(FashionError, match="invalid_state"):
        p.submit_review(OWNER, "review")
    with pytest.raises(FashionError, match="product_not_approved"):
        p.market_projection(OWNER)


def test_empty_evidence_does_not_advance_state():
    p = draft()
    with pytest.raises(FashionError, match="review_evidence_required"):
        p.submit_review(OWNER, "")
    assert p.state == FashionState.DRAFT
    p.submit_review(OWNER, "review")
    with pytest.raises(FashionError, match="approval_evidence_required"):
        p.approve(OWNER, "", human_approval=True)
    assert p.state == FashionState.READY_FOR_REVIEW


@pytest.mark.parametrize("value", [-1, True, "NaN", "Infinity", "1.1"])
def test_invalid_price(value):
    with pytest.raises(FashionError, match="invalid_price"):
        FashionVariant("OAP-HOODIE-001", "XL", "Black", value)


def test_duplicate_variant_sku_rejected():
    v = FashionVariant("OAP-HOODIE-001", "XL", "Black", 3500)
    with pytest.raises(FashionError, match="variants_required_or_duplicate_sku"):
        FashionDraft(OWNER, PRODUCT, "Hoodie", "hoodie", "oap:art/1", True, True, (v, v))
