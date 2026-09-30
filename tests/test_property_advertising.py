"""Property advertising contract regression checks (no DB, external contact or publication)."""
import uuid

import pytest

from mission_control import property_advertising as ads

OWNER = str(uuid.uuid4())
ADVERTISER = str(uuid.uuid4())
REVIEWER = str(uuid.uuid4())


def authority_check(record, evidence):
    return evidence == 'contract-ref' and record['advertiser_id'] == ADVERTISER


def certified_check(publisher_id):
    return publisher_id == OWNER


GATES = {'authority_check': authority_check, 'certified_check': certified_check}
def reviewer_check(reviewer, publisher):
    return reviewer == REVIEWER and reviewer != publisher


REVIEW_GATES = {**GATES, 'reviewer_check': reviewer_check}


def payload():
    return {
        "advertiser_id": ADVERTISER,
        "property_ref": "partner-property-1",
        "title": "Approved residential property",
        "description": "Advertiser-supplied property description",
        "category": "house",
        "country": "United Kingdom",
        "locality": "London",
        "postcode": "SW1",
        "price": "250000.00",
        "currency": "GBP",
        "advertiser_contact": "https://example.org/contact",
        "media": [{"asset_ref": "approved-photo", "rights_confirmed": True}],
    }


def test_draft_is_never_public():
    draft = ads.property_draft(payload(), publisher_id=OWNER)
    assert draft["publisher_id"] == OWNER
    assert draft["advertiser_id"] == ADVERTISER
    assert draft["state"] == "DRAFT"
    assert ads.public_record(draft) is None
    with pytest.raises(PermissionError, match="property_approval_required"):
        ads.publish(draft, actor_id=OWNER, channel="OAP Market", **GATES)


def test_approval_and_public_projection_hide_private_evidence():
    draft = ads.property_draft(payload(), publisher_id=OWNER)
    approved = ads.approve(draft, evidence_ref="contract-ref", approved_by=REVIEWER, **REVIEW_GATES)
    assert ads.public_record(approved) is None
    active = ads.publish(approved, actor_id=OWNER, channel="OAP Market", **GATES)
    public = ads.public_record(active, **GATES)
    assert public["title"] == payload()["title"]
    assert "authority_evidence_ref" not in public
    assert "approval_receipt" not in public
    assert "advertiser_id" not in public


def test_edit_revokes_approval_and_withdrawal_hides_listing():
    approved = ads.approve(
        ads.property_draft(payload(), publisher_id=OWNER),
        evidence_ref="contract-ref", approved_by=REVIEWER, **REVIEW_GATES,
    )
    active = ads.publish(approved, actor_id=OWNER, channel="OAP Market", **GATES)
    edited = ads.edit(active, {"price": "245000"}, actor_id=OWNER)
    assert edited["state"] == "DRAFT"
    assert edited["approval_receipt"] is None
    assert ads.public_record(edited) is None
    withdrawn = ads.withdraw(active, actor_id=OWNER, reason="Sold")
    assert ads.public_record(withdrawn) is None
    assert withdrawn["withdrawn_receipt"]["reason"] == "Sold"
    assert ads.withdraw(withdrawn, actor_id=OWNER, reason="Repeat") == withdrawn


def test_ownership_and_guarded_fields_fail_closed():
    draft = ads.property_draft(payload(), publisher_id=OWNER)
    with pytest.raises(PermissionError, match="property_publisher_required"):
        ads.edit(draft, {"title": "Changed"}, actor_id=ADVERTISER)
    with pytest.raises(PermissionError, match="property_guarded_field"):
        ads.edit(draft, {"state": "ACTIVE"}, actor_id=OWNER)
    with pytest.raises(PermissionError, match="property_publisher_required"):
        ads.withdraw(draft, actor_id=ADVERTISER, reason="No")


@pytest.mark.parametrize("change", [
    {"advertiser_contact": "http://example.org"},
    {"currency": "USD"},
    {"price": "-5"},
    {"media": [{"asset_ref": "bad", "rights_confirmed": False}]},
    {"category": "unrecognised"},
])
def test_invalid_property_data_blocked(change):
    data = {**payload(), **change}
    with pytest.raises(ValueError):
        ads.property_draft(data, publisher_id=OWNER)


def test_no_verifier_and_self_approval_fail_closed():
    draft = ads.property_draft(payload(), publisher_id=OWNER)
    with pytest.raises(PermissionError, match="independent_reviewer"):
        ads.approve(draft, evidence_ref="contract-ref", approved_by=OWNER, **REVIEW_GATES)
    with pytest.raises(PermissionError, match="verifiers_required"):
        ads.approve(draft, evidence_ref="contract-ref", approved_by=REVIEWER,
                    reviewer_check=REVIEW_GATES["reviewer_check"])
    with pytest.raises(PermissionError, match="authority_required"):
        ads.approve(draft, evidence_ref="wrong-ref", approved_by=REVIEWER, **REVIEW_GATES)
    with pytest.raises(PermissionError, match="certified_required"):
        ads.approve(draft, evidence_ref="contract-ref", approved_by=REVIEWER,
                    authority_check=authority_check, certified_check=lambda _: False,
                    reviewer_check=REVIEW_GATES['reviewer_check'])


def test_revocation_between_approval_publication_and_read():
    draft = ads.property_draft(payload(), publisher_id=OWNER)
    approved = ads.approve(draft, evidence_ref="contract-ref", approved_by=REVIEWER, **REVIEW_GATES)
    with pytest.raises(PermissionError, match="authority_required"):
        ads.publish(approved, actor_id=OWNER, channel="OAP Market",
                    authority_check=lambda *_: False, certified_check=certified_check)
    active = ads.publish(approved, actor_id=OWNER, channel="OAP Market", **GATES)
    assert ads.public_record(active) is None
    assert ads.public_record(active, authority_check=lambda *_: False,
                             certified_check=certified_check) is None
    assert ads.public_record(active, authority_check=authority_check,
                             certified_check=lambda _: False) is None
    assert ads.public_record(active, **GATES)["property_ref"] == "partner-property-1"


def test_checker_exception_and_forged_receipt_fail_closed():
    draft = ads.property_draft(payload(), publisher_id=OWNER)
    def unavailable(*_):
        raise RuntimeError("offline")
    with pytest.raises(PermissionError, match="verification_unavailable"):
        ads.approve(draft, evidence_ref="contract-ref", approved_by=REVIEWER,
                    authority_check=unavailable, certified_check=certified_check,
                    reviewer_check=REVIEW_GATES['reviewer_check'])
    forged = {**draft, "state": "ACTIVE", "authority_evidence_ref": "contract-ref",
              "approval_receipt": {"approved_by": OWNER}, "published_receipt": {"at": "now"}}
    assert ads.public_record(forged, **GATES) is None


def test_reviewer_gate_denies_missing_status_and_exceptions():
    draft = ads.property_draft(payload(), publisher_id=OWNER)
    with pytest.raises(PermissionError, match="human_reviewer_required"):
        ads.approve(draft, evidence_ref="contract-ref", approved_by=REVIEWER,
                    reviewer_check=lambda *_: False, **GATES)
    def unavailable(*_):
        raise RuntimeError("authority database down")
    with pytest.raises(PermissionError, match="human_reviewer_required"):
        ads.approve(draft, evidence_ref="contract-ref", approved_by=REVIEWER,
                    reviewer_check=unavailable, **GATES)
