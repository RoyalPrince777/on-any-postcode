from __future__ import annotations

import itertools

import pytest

from mission_control import music_market_purchase as purchase
LISTING_PRICES = (100, 101, 125, 199, 500, 999, 5000)

ORDER_MODES = (
    ("listing-default", lambda listing: None, True, True),
    ("listing-exact", lambda listing: listing, True, True),
    ("pay-more-1", lambda listing: listing + 1, True, True),
    ("pay-more-50", lambda listing: listing + 50, True, True),
    ("pay-more-disabled-1", lambda listing: listing + 1, False, False),
    ("below-pound-floor", lambda _listing: 99, True, False),
    ("below-listing", lambda listing: listing - 1, True, False),
    ("zero-price", lambda _listing: 0, True, False),
    ("negative-price", lambda _listing: -100, True, False),
    ("pay-more-disabled-500", lambda listing: listing + 500, False, False),
)

FINALIZE_MODES = (
    ("captured-ready", "GBP", 1, "READY", "CAPTURED", "valid"),
    ("provider-required", "GBP", 1, "READY", "PROVIDER_REQUIRED", "payment"),
    ("created", "GBP", 1, "READY", "CREATED", "payment"),
    ("authorized", "GBP", 1, "READY", "AUTHORIZED", "payment"),
    ("cancelled", "GBP", 1, "READY", "CANCELLED", "payment"),
    ("failed", "GBP", 1, "READY", "FAILED", "payment"),
    ("product-stopped", "GBP", 1, "STOPPED", "CAPTURED", "product"),
    ("wrong-currency", "USD", 1, "READY", "CAPTURED", "currency"),
    ("wrong-quantity", "GBP", 2, "READY", "CAPTURED", "quantity"),
    ("bad-subtotal", "GBP", 1, "READY", "CAPTURED", "subtotal"),
)

CASES = tuple(itertools.product(LISTING_PRICES, ORDER_MODES, FINALIZE_MODES))
assert len(CASES) == 700


@pytest.mark.parametrize(
    ("listing", "order_mode", "finalize_mode"),
    CASES,
    ids=lambda value: str(value[0]) if isinstance(value, tuple) else str(value),
)
def test_music_market_700_way_non_live_gate(
    listing: int,
    order_mode,
    finalize_mode,
):
    """700 deterministic combinations across price, pay-more, payment and ownership gates."""
    order_name, requested_fn, optional_pay_more, order_should_pass = order_mode
    del order_name
    requested = requested_fn(listing)

    if not order_should_pass:
        with pytest.raises(ValueError):
            purchase.validate_order_terms(
                listing_price_minor=listing,
                requested_price_minor=requested,
                minimum_price_minor=100,
                optional_pay_more=optional_pay_more,
                quantity=1,
            )
        return

    effective = purchase.validate_order_terms(
        listing_price_minor=listing,
        requested_price_minor=requested,
        minimum_price_minor=100,
        optional_pay_more=optional_pay_more,
        quantity=1,
    )
    assert effective >= listing
    assert effective >= 100

    (
        _finalize_name,
        currency,
        quantity,
        link_state,
        payment_state,
        expected_failure,
    ) = finalize_mode
    subtotal = effective - 1 if expected_failure == "subtotal" else effective

    kwargs = {
        "currency": currency,
        "unit_price_minor": effective,
        "subtotal_minor": subtotal,
        "minimum_price_minor": 100,
        "quantity": quantity,
        "link_state": link_state,
        "payment_state": payment_state,
    }

    if expected_failure == "valid":
        purchase.validate_finalize_terms(**kwargs)
    else:
        with pytest.raises(ValueError):
            purchase.validate_finalize_terms(**kwargs)


def test_700_way_matrix_is_exactly_700_not_700_stages():
    assert len(LISTING_PRICES) == 7
    assert len(ORDER_MODES) == 10
    assert len(FINALIZE_MODES) == 10
    assert len(CASES) == 700


def test_non_live_completion_boundary_remains_explicit():
    state = purchase.MusicMarketPurchaseStore.finalize_captured_order
    module_source = purchase.__doc__ or ""

    assert "never captures payment or moves money" in module_source
    assert "payouts remain provider-required" in module_source
    assert callable(state)


def test_split_allocation_preserves_every_penny_across_700_amounts():
    plan = purchase._split_plan(
        (
            {
                "beneficiary_identity_id": "11111111-1111-1111-1111-111111111111",
                "split_kind": "ARTIST",
                "basis_points": 7000,
            },
            {
                "beneficiary_identity_id": "22222222-2222-2222-2222-222222222222",
                "split_kind": "COLLABORATOR",
                "basis_points": 1500,
            },
            {
                "beneficiary_identity_id": "33333333-3333-3333-3333-333333333333",
                "split_kind": "OAP",
                "basis_points": 1500,
            },
        )
    )
    for amount in range(100, 800):
        allocation = purchase._allocate(amount, plan)
        assert sum(row["amount_minor"] for row in allocation) == amount
        assert all(row["amount_minor"] >= 0 for row in allocation)
