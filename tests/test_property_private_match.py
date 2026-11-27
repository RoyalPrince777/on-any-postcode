"""Private matching regressions; gate doubles are not live authority proof."""
from uuid import uuid4

import pytest

from mission_control import property_advertising as ads
from mission_control.property_private_match import eligible_match, review_match
from oap.contracts import IdentityRecord, OutputState
from oap.hrm import HRMCore
from oap.smi.bootstrap import build_smi

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


def test_review_uses_existing_brain_and_hrm(approved, buyer):
    store = HRMCore.in_memory()
    try:
        brain = build_smi(store.connection, identities=(
            IdentityRecord(
                identity_id="property-reviewer",
                identity_type="human",
                authority_level=0,
                permissions=frozenset({"REQUEST_RECOMMENDATION"}),
            ),
        ))
        kwargs = {"identity_id": "property-reviewer", **GATES}
        blocked = review_match(
            brain, approved, buyer, request_id="property-denied",
            **{**kwargs, "seller_permission": no},
        )
        assert blocked.output_state == OutputState.BLOCK_REQUEST
        assert "Property eligibility denied." in blocked.rationale
        result = review_match(
            brain, approved, buyer, request_id="property-review", **kwargs,
        )
        assert result.output_state in {
            OutputState.REVIEW_REQUIRED, OutputState.BLOCK_REQUEST,
        }
        assert not result.can_execute
        assert brain.hrm.has_request("property-review")
        assert brain.hrm.has_request("property-denied")
        assert brain.hrm.status()["memory_records"] == 2
        assert brain.hrm.status()["audit_events"] == 2
        repeat = review_match(
            brain, approved, buyer, request_id="property-review", **kwargs,
        )
        assert repeat.output_state == OutputState.SYSTEM_LOG_ONLY
        assert brain.hrm.status()["memory_records"] == 2
        assert brain.hrm.status()["kernel_outcomes"] == 0
        assert brain.hrm.status()["approval_receipts"] == 0
        rows = store.connection.execute(
            "SELECT summary, rationale_json FROM smi_memory_records"
        ).fetchall()
        assert all("example.org" not in str(tuple(row)) for row in rows)
    finally:
        store.connection.close()
