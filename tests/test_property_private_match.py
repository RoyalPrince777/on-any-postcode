"""Private matching regressions; gate doubles are not live authority proof."""
from uuid import uuid4

import pytest

from mission_control import property_advertising as ads
from mission_control.property_private_match import eligible_match

PUBLISHER = str(uuid4())
REVIEWER = str(uuid4())
ADVERTISER = str(uuid4())


def yes(*_):
    return True


def no(*_):
    return False


GATES = {
    "seller_permission": yes,
    "buyer_qualification": yes,
    "authority_check": yes,
    "certified_check": yes,
    "reviewer_check": yes,
}


@pytest.fixture
def approved():
    draft = ads.property_draft({
        "advertiser_id": ADVERTISER,
        "property_ref": "private-1",
        "title": "Private test",
        "description": "Test only",
        "category": "house",
        "country": "United Kingdom",
        "locality": "Mitcham",
        "postcode": "CR4 1AA",
        "price": "250000",
        "currency": "GBP",
        "advertiser_contact": "https://example.org/contact",
    }, publisher_id=PUBLISHER)
    return ads.approve(
        draft, evidence_ref="test", approved_by=REVIEWER,
        authority_check=yes, certified_check=yes, reviewer_check=yes,
    )


@pytest.fixture
def buyer():
    return {
        "country": "United Kingdom", "locality": "Mitcham",
        "postcode": "CR4", "currency": "GBP",
        "category": "house", "max_price": "250000",
    }


def test_matching_returns_boolean_only(approved, buyer):
    assert eligible_match(approved, buyer, **GATES) is True


@pytest.mark.parametrize("field,value", [
    ("country", "Ghana"), ("locality", "Croydon"),
    ("currency", "GHS"), ("postcode", "CR40"),
    ("category", "flat"), ("max_price", "249999"),
    ("max_price", "NaN"), ("max_price", None),
])
def test_mismatch(approved, buyer, field, value):
    assert eligible_match(approved, {**buyer, field: value}, **GATES) is False


@pytest.mark.parametrize("gate", list(GATES))
def test_each_gate_denies(approved, buyer, gate):
    assert eligible_match(approved, buyer, **{**GATES, gate: no}) is False


@pytest.mark.parametrize("state", ["DRAFT", "ACTIVE", "WITHDRAWN"])
def test_only_approved_private_candidate(approved, buyer, state):
    assert eligible_match({**approved, "state": state}, buyer, **GATES) is False


def test_missing_evidence_and_provider_outage(approved, buyer):
    def outage(*_):
        raise RuntimeError("unavailable")

    assert eligible_match(
        {**approved, "authority_evidence_ref": None}, buyer, **GATES,
    ) is False
    assert eligible_match(
        approved, buyer, **{**GATES, "seller_permission": outage},
    ) is False
