"""Warehouse declarations are not physical warehouse or custody proof."""
from uuid import uuid4

import pytest

from mission_control.global_shipment import draft_global_shipment
from mission_control.global_transport_warehouse import review_warehouse


def _plan():
    return draft_global_shipment(
        parcel_id=uuid4(), owner_identity_id=uuid4(),
        legs=[
            {"sequence": 1, "mode": "SEA", "origin_country": "GB",
             "destination_country": "GH"},
        ],
    )


def _hubs():
    return [
        {"hub_id": str(uuid4()), "country": "GB", "state": "PLANNED",
         "capacity_units": 10, "occupied_units": 2,
         "operator_review_state": "REVIEWED"},
        {"hub_id": str(uuid4()), "country": "GH", "state": "PLANNED",
         "capacity_units": 10, "occupied_units": 1,
         "operator_review_state": "REVIEWED"},
    ]


def _transfer(hubs):
    return {
        "leg_sequence": 1,
        "from_hub_id": hubs[0]["hub_id"],
        "to_hub_id": hubs[1]["hub_id"],
        "reported_receipt": True,
        "evidence_review_state": "REVIEWED",
    }


def test_warehouse_review_never_mints_ownership_or_custody():
    hubs = _hubs()
    result = review_warehouse(plan=_plan(), hubs=hubs, transfers=[_transfer(hubs)])
    assert [x["declared_free_units"] for x in result["hubs"]] == [8, 9]
    assert result["warehouse_capacity_verified"] is False
    assert result["inventory_reserved"] is False
    assert result["physical_sites_activated"] is False
    assert result["custody_verified"] is False
    assert result["external_action_performed"] is False
    assert result["persisted"] is False
    assert result["transfers"][0]["carrier_handoff_performed"] is False


@pytest.mark.parametrize("change", [
    {"state": "ACTIVE"}, {"capacity_units": -1},
    {"occupied_units": 11}, {"occupied_units": True},
    {"operator_review_state": "CERTIFIED"}, {"capacity_reserved": True},
    {"country": "United Kingdom"},
])
def test_untrusted_hub_assertions_fail_closed(change):
    hubs = _hubs()
    hubs[0] = {**hubs[0], **change}
    with pytest.raises((ValueError, TypeError)):
        review_warehouse(plan=_plan(), hubs=hubs, transfers=[])


@pytest.mark.parametrize("change", [
    {"leg_sequence": True}, {"leg_sequence": 2},
    {"reported_receipt": "true"}, {"evidence_review_state": "APPROVED"},
    {"custody_verified": True}, {"carrier_handoff_performed": True},
])
def test_untrusted_transfer_assertions_fail_closed(change):
    hubs = _hubs()
    with pytest.raises((ValueError, TypeError)):
        review_warehouse(plan=_plan(), hubs=hubs, transfers=[{**_transfer(hubs), **change}])


def test_duplicate_hub_and_country_mismatch_fail_closed():
    hubs = _hubs()
    with pytest.raises(ValueError, match="duplicate_hub"):
        review_warehouse(plan=_plan(), hubs=[hubs[0], hubs[0]], transfers=[])
    bad = {**_transfer(hubs), "from_hub_id": hubs[1]["hub_id"],
           "to_hub_id": hubs[0]["hub_id"]}
    with pytest.raises(ValueError, match="transfer_country_mismatch"):
        review_warehouse(plan=_plan(), hubs=hubs, transfers=[bad])
