"""Read-only, fail-closed review of an existing Market → Movement → Post handoff.

This is not a new booking, order, parcel or payment engine. Callers must load
owner-scoped canonical records from their authoritative stores first. No DB,
network, payment, dispatch, permission grant or carrier side effects occur.
"""
from __future__ import annotations

from collections.abc import Mapping
from uuid import UUID


class HandoffReviewDenied(ValueError):
    """The proposed association is incomplete, inconsistent or unauthorised."""


def _id(value: object) -> str:
    try:
        return str(UUID(str(value)))
    except (AttributeError, TypeError, ValueError) as exc:
        raise HandoffReviewDenied("invalid_reference") from exc


def review_handoff(
    *, owner_identity_id: object,
    order: Mapping[str, object],
    booking: Mapping[str, object],
    parcel: Mapping[str, object],
    stopped: bool = False,
) -> dict[str, object]:
    """Check canonical identities, never accept an asserted approval as proof.

    order is the existing Commerce order; booking is the existing Movement
    booking; parcel is the existing Post Core parcel. The caller must obtain
    all three under its own authenticated owner-scoped DB permissions.
    """
    if stopped:
        raise HandoffReviewDenied("stopped")
    if not all(isinstance(record, Mapping) for record in (order, booking, parcel)):
        raise HandoffReviewDenied("invalid_record")
    owner = _id(owner_identity_id)
    for record, field in (
        (order, "buyer_identity_id"),
        (booking, "member_identity_id"),
        (parcel, "owner_identity_id"),
    ):
        if _id(record.get(field)) != owner:
            raise HandoffReviewDenied("owner_mismatch")
    order_id = _id(order.get("order_id"))
    booking_id = _id(booking.get("booking_id"))
    parcel_id = _id(parcel.get("parcel_id"))
    # These links must be *stored by their canonical owners*, not provided as
    # unchecked request parameters. Missing or conflicting links fail closed.
    if _id(booking.get("order_id")) != order_id:
        raise HandoffReviewDenied("order_booking_mismatch")
    if _id(parcel.get("order_id")) != order_id:
        raise HandoffReviewDenied("order_parcel_mismatch")
    if _id(parcel.get("booking_id")) != booking_id:
        raise HandoffReviewDenied("booking_parcel_mismatch")
    return {
        "owner_identity_id": owner,
        "order_id": order_id,
        "booking_id": booking_id,
        "parcel_id": parcel_id,
        "review_state": "REFERENCES_CONSISTENT_ONLY",
        "merchant_certified": False,
        "payment_capture_performed": False,
        "dispatch_performed": False,
        "parcel_handoff_performed": False,
        "release_approved": False,
        "human_authority_final": True,
    }
