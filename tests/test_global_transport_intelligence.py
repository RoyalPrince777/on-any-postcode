"""Global Transport reviews are never operational attestations."""
from uuid import uuid4

import pytest

from mission_control.global_shipment import draft_global_shipment
from mission_control.global_transport_intelligence import (
    assess_cross_border,
    assess_global_transport,
    assess_operator,
    review_custody,
)


def _legs():
    return [
        {"sequence": 1, "mode": "ROAD", "origin_country": "GB", "destination_country": "GB"},
        {"sequence": 2, "mode": "SEA", "origin_country": "GB", "destination_country": "GH"},
        {"sequence": 3, "mode": "ROAD", "origin_country": "GH", "destination_country": "GH"},
    ]


def _operator():
    return {
        "operator_id": str(uuid4()), "country": "GB",
        "modes": ["ROAD", "SEA"], "capabilities": ["CARGO"],
        "certification_state": "REVIEWED",
        "insurance_state": "REVIEWED", "capacity_state": "REVIEWED",
    }


def _reviews():
    return {
        "document_review": "REVIEWED", "jurisdiction_review": "REVIEWED",
        "operator_review": "REVIEWED", "restricted_goods_review": "REVIEWED",
        "recipient_review": "REVIEWED",
    }


def _plan():
    return draft_global_shipment(
        parcel_id=uuid4(), owner_identity_id=uuid4(), legs=_legs()
    )


def _event():
    return {
        "sequence": 1, "leg_sequence": 1, "kind": "DELIVERY_REPORTED",
        "evidence_ref": "receipt-1234",
        "occurred_at": "2026-09-23T08:00:00+00:00",
    }


def test_full_review_never_grants_operational_authority():
    result = assess_global_transport(
        parcel_id=uuid4(), owner_identity_id=uuid4(), legs=_legs(),
        operator=_operator(), reviews=_reviews(), events=[_event()],
    )
    assert result["shipment"]["cross_border"] is True
    assert result["operator_review"]["in_declared_scope"] is True
    assert result["operator_review"]["certified_for_assignment"] is False
    assert result["cross_border_review"]["review_complete"] is True
    assert result["cross_border_review"]["customs_cleared"] is False
    assert result["custody_review"]["delivered"] is False
    assert result["custody_review"]["persisted"] is False
    assert result["execution_authorised"] is False


@pytest.mark.parametrize("change", [
    {"country": "GH"}, {"modes": ["AIR"]}, {"capabilities": ["PASSENGER"]},
])
def test_operator_scope_is_not_capacity_or_certification(change):
    op = {**_operator(), **change}
    result = assess_operator(record=op, mode="ROAD", country="GB")
    assert result["in_declared_scope"] is False
    assert result["certified_for_assignment"] is False


@pytest.mark.parametrize("change", [
    {"dispatch": True}, {"carrier_id": str(uuid4())},
    {"certification_state": "CERTIFIED"},
    {"modes": ["ROAD", "ROAD"]}, {"capabilities": ["CARGO", "CARGO"]},
])
def test_operator_untrusted_proof_fails_closed(change):
    with pytest.raises((ValueError, TypeError)):
        assess_operator(record={**_operator(), **change}, mode="ROAD", country="GB")


def test_cross_border_review_does_not_grant_customs():
    result = assess_cross_border(plan=_plan(), reviews=_reviews())
    assert result["review_complete"] is True
    assert result["customs_cleared"] is False
    assert result["import_export_authorised"] is False


@pytest.mark.parametrize("change", [
    {"customs_cleared": True}, {"document_review": "APPROVED"},
])
def test_customs_untrusted_authority_fails_closed(change):
    with pytest.raises(ValueError):
        assess_cross_border(plan=_plan(), reviews={**_reviews(), **change})


def test_delivery_report_is_not_verified_delivery():
    result = review_custody(plan=_plan(), events=[_event()])
    assert result["evidence_count"] == 1
    assert result["reviewed_events"][0]["verified"] is False
    assert result["delivered"] is False
    assert result["claim_settled"] is False


@pytest.mark.parametrize("change", [
    {"kind": "CUSTOMS_CLEARED"}, {"kind": "PAYMENT_CAPTURED"},
    {"kind": "DISPATCHED"}, {"verified": True},
    {"sequence": 2}, {"leg_sequence": 7},
    {"evidence_ref": "bad"}, {"occurred_at": "not-a-timestamp"},
])
def test_custody_untrusted_inputs_fail_closed(change):
    with pytest.raises((ValueError, TypeError)):
        review_custody(plan=_plan(), events=[{**_event(), **change}])


def test_custody_timestamp_and_sequence_bounded():
    earlier = {**_event(), "sequence": 2, "occurred_at": "2026-09-23T07:00:00Z"}
    with pytest.raises(ValueError, match="out_of_order_event_time"):
        review_custody(plan=_plan(), events=[_event(), earlier])
    with pytest.raises(ValueError, match="too_many_events"):
        review_custody(plan=_plan(), events=[_event()] * 65)
