"""Negative, side-effect-free checks for the bounded handoff review."""
from uuid import uuid4

import pytest

from mission_control.distribution_market_handoff_review import (
    HandoffReviewDenied,
    review_handoff,
)


def records():
    owner, order, booking, parcel = (str(uuid4()) for _ in range(4))
    return owner, (
        {"buyer_identity_id": owner, "order_id": order},
        {"member_identity_id": owner, "booking_id": booking, "order_id": order},
        {"owner_identity_id": owner, "parcel_id": parcel,
         "order_id": order, "booking_id": booking},
    )


def test_read_only_consistency_never_claims_execution():
    owner, (order, booking, parcel) = records()
    first = review_handoff(
        owner_identity_id=owner, order=order, booking=booking, parcel=parcel
    )
    assert first == review_handoff(
        owner_identity_id=owner, order=order, booking=booking, parcel=parcel
    )
    assert first["review_state"] == "REFERENCES_CONSISTENT_ONLY"
    for field in (
        "merchant_certified", "payment_capture_performed", "dispatch_performed",
        "parcel_handoff_performed", "release_approved",
    ):
        assert first[field] is False


@pytest.mark.parametrize("record,field", [
    ("order", "buyer_identity_id"),
    ("booking", "member_identity_id"),
    ("parcel", "owner_identity_id"),
    ("booking", "order_id"),
    ("parcel", "order_id"),
    ("parcel", "booking_id"),
])
def test_owner_and_link_drift_are_denied(record, field):
    owner, (order, booking, parcel) = records()
    by_name = {"order": order, "booking": booking, "parcel": parcel}
    by_name[record][field] = str(uuid4())
    with pytest.raises(HandoffReviewDenied):
        review_handoff(
            owner_identity_id=owner, order=order, booking=booking, parcel=parcel
        )


@pytest.mark.parametrize("record,field", [
    ("order", "order_id"),
    ("booking", "booking_id"),
    ("parcel", "parcel_id"),
    ("parcel", "order_id"),
])
def test_missing_or_invalid_reference_denied(record, field):
    owner, (order, booking, parcel) = records()
    by_name = {"order": order, "booking": booking, "parcel": parcel}
    by_name[record].pop(field)
    with pytest.raises(HandoffReviewDenied):
        review_handoff(
            owner_identity_id=owner, order=order, booking=booking, parcel=parcel
        )


def test_stop_and_cross_owner_denied():
    owner, (order, booking, parcel) = records()
    with pytest.raises(HandoffReviewDenied, match="stopped"):
        review_handoff(
            owner_identity_id=owner, order=order, booking=booking,
            parcel=parcel, stopped=True,
        )
    with pytest.raises(HandoffReviewDenied, match="owner_mismatch"):
        review_handoff(
            owner_identity_id=str(uuid4()),
            order=order, booking=booking, parcel=parcel,
        )
