"""Bounded contract tests: no global plan may mint operational proof."""
from uuid import uuid4

import pytest

from mission_control.global_shipment import draft_global_shipment


def _leg(n=1, mode="ROAD", origin="GB", destination="GH"):
    return {
        "sequence": n, "mode": mode,
        "origin_country": origin, "destination_country": destination,
    }


def _draft(legs):
    return draft_global_shipment(
        parcel_id=uuid4(), owner_identity_id=uuid4(), legs=legs
    )


def test_draft_multimodal_corridor_is_not_operational_evidence():
    plan = _draft([_leg(destination="GB"), _leg(2, "SEA", "GB", "GH"),
                   _leg(3, "ROAD", "GH", "GH")])
    assert plan["cross_border"] is True
    assert [leg["state"] for leg in plan["legs"]] == ["DRAFT"] * 3
    assert all(plan[key] is False for key in (
        "parcel_ownership_verified", "carrier_eligibility_verified",
        "customs_ready", "capacity_verified", "external_action_performed",
        "carrier_handoff_performed", "dispatch_performed",
        "payment_performed", "tracking_enabled", "persisted",
    ))


@pytest.mark.parametrize("legs", [[], [_leg()] * 17, "not legs", None])
def test_rejects_invalid_leg_collection(legs):
    with pytest.raises((ValueError, TypeError)):
        _draft(legs)


@pytest.mark.parametrize("legs", [
    [_leg(2)],
    [_leg(), _leg(2, origin="US")],
    [_leg(mode="DRONE")],
    [_leg(origin="United Kingdom")],
    [{**_leg(), "carrier_id": "unverified"}],
    [{**_leg(), "dispatch": True}],
    [{**_leg(), "customs_cleared": True}],
    [{**_leg(), "tracking": True}],
    [{**_leg(), "payment": True}],
    [{**_leg(), "approved": True}],
    [{**_leg(), "executed": True}],
    [{**_leg(), "operator_certified": True}],
    [{**_leg(), "delivered": True}],
    [{**_leg(), "unexpected": True}],
    [{**_leg(), "sequence": True}],
])
def test_rejects_untrusted_or_disconnected_legs(legs):
    with pytest.raises(ValueError):
        _draft(legs)


def test_owner_and_parcel_identifiers_must_be_uuid():
    with pytest.raises(ValueError, match="invalid_parcel_id"):
        draft_global_shipment(parcel_id="not-id", owner_identity_id=uuid4(),
                              legs=[_leg()])
    with pytest.raises(ValueError, match="invalid_owner_identity_id"):
        draft_global_shipment(parcel_id=uuid4(), owner_identity_id="not-id",
                              legs=[_leg()])
