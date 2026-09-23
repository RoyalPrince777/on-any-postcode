"""Global transport capacity and recovery remain non-executing reviews."""
from uuid import uuid4

import pytest

from mission_control.global_shipment import draft_global_shipment
from mission_control.global_transport_recovery import review_capacity, review_exceptions


def _plan():
    return draft_global_shipment(
        parcel_id=uuid4(), owner_identity_id=uuid4(),
        legs=[
            {"sequence": 1, "mode": "ROAD", "origin_country": "GB",
             "destination_country": "GB"},
            {"sequence": 2, "mode": "SEA", "origin_country": "GB",
             "destination_country": "GH"},
        ],
    )


def _capacity(index, mode):
    return {
        "leg_sequence": index, "mode": mode, "available_units": 20,
        "reserved_units": 5, "source_state": "REVIEWED",
        "operator_reviewed": True,
    }


def _exception():
    return {
        "leg_sequence": 2, "kind": "CUSTOMS_HOLD",
        "evidence_state": "REVIEWED", "review_state": "REVIEWED",
    }


def test_capacity_is_report_only_even_with_all_reviews():
    result = review_capacity(
        plan=_plan(), records=[_capacity(1, "ROAD"), _capacity(2, "SEA")]
    )
    assert [x["declared_remaining_units"] for x in result["legs"]] == [15, 15]
    assert result["capacity_verified"] is False
    assert result["capacity_reserved"] is False
    assert result["carrier_assigned"] is False
    assert result["external_action_performed"] is False


@pytest.mark.parametrize("change", [
    {"available_units": -1}, {"reserved_units": 21},
    {"reserved_units": True}, {"operator_reviewed": "yes"},
    {"mode": "AIR"}, {"capacity_reserved": True},
])
def test_capacity_untrusted_or_inconsistent_inputs_fail_closed(change):
    with pytest.raises((ValueError, TypeError)):
        review_capacity(
            plan=_plan(),
            records=[{**_capacity(1, "ROAD"), **change}, _capacity(2, "SEA")],
        )


def test_recovery_report_does_not_settle_or_move_parcel():
    result = review_exceptions(plan=_plan(), reports=[_exception()])
    assert result["exceptions"][0]["resolved"] is False
    assert result["recovery_execution_allowed"] is False
    assert result["refund_authorised"] is False
    assert result["claim_settled"] is False
    assert result["parcel_state_changed"] is False


@pytest.mark.parametrize("change", [
    {"kind": "CUSTOMS_CLEARED"}, {"resolved": True},
    {"leg_sequence": 3}, {"leg_sequence": True},
    {"review_state": "APPROVED"},
])
def test_recovery_false_authority_fails_closed(change):
    with pytest.raises((ValueError, TypeError)):
        review_exceptions(plan=_plan(), reports=[{**_exception(), **change}])


def test_forged_draft_plan_does_not_pass_capacity_or_recovery():
    forged = {**_plan(), "legs": [{**_plan()["legs"][0], "state": "DELIVERED"}]}
    with pytest.raises((ValueError, TypeError)):
        review_capacity(plan=forged, records=[_capacity(1, "ROAD")])
    with pytest.raises((ValueError, TypeError)):
        review_exceptions(plan=forged, reports=[])
