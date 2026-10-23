"""Regression tests for the additive Global Movement journey identity contract."""
from uuid import uuid4

import pytest

from mission_control.global_journey_contract import (
    JourneyAssociation,
    associate_in_transaction,
    authorize_association,
    check_replay,
)


def test_create_and_idempotent_replay():
    association = JourneyAssociation(str(uuid4()), str(uuid4()), "oap-book-" + "a" * 16)
    assert check_replay(None, association) == "CREATE"
    assert check_replay(association, association) == "IDEMPOTENT"


def test_relink_is_rejected():
    original = JourneyAssociation(str(uuid4()), str(uuid4()))
    changed = JourneyAssociation(original.journey_id, str(uuid4()))
    with pytest.raises(ValueError, match="association_conflict"):
        check_replay(original, changed)


@pytest.mark.parametrize("value", ["", "not-a-uuid", "oap-book-abcdef", None])
def test_invalid_journey_identifier(value):
    with pytest.raises(ValueError, match="invalid_journey_id"):
        JourneyAssociation(value, str(uuid4()))


@pytest.mark.parametrize("value", ["oap-book-ABCDEF0123456789", "oap-book-xyz", "external", ""])
def test_invalid_booking_intent(value):
    with pytest.raises(ValueError, match="invalid_intent_id"):
        JourneyAssociation(str(uuid4()), str(uuid4()), value)


def test_contract_version_fail_closed():
    with pytest.raises(ValueError, match="unsupported_contract_version"):
        JourneyAssociation(str(uuid4()), str(uuid4()), version=2)


def test_owner_evidence_allows_same_owner():
    owner = str(uuid4())
    association = JourneyAssociation(str(uuid4()), str(uuid4()), "oap-book-" + "a" * 16)
    assert authorize_association(
        association, actor_identity_id=owner, booking_owner_identity_id=owner,
        journey_owner_identity_id=owner, intent_owner_identity_id=owner,
    ) == association


def test_cross_user_association_denied():
    owner = str(uuid4())
    association = JourneyAssociation(str(uuid4()), str(uuid4()))
    with pytest.raises(PermissionError, match="association_owner_mismatch"):
        authorize_association(
            association, actor_identity_id=owner, booking_owner_identity_id=str(uuid4()),
            journey_owner_identity_id=owner,
        )


def test_intent_owner_evidence_is_mandatory():
    owner = str(uuid4())
    association = JourneyAssociation(str(uuid4()), str(uuid4()), "oap-book-" + "a" * 16)
    with pytest.raises(PermissionError, match="intent_owner_evidence_required"):
        authorize_association(
            association, actor_identity_id=owner, booking_owner_identity_id=owner,
            journey_owner_identity_id=owner,
        )


@pytest.mark.parametrize("owner_field", ["booking_owner_identity_id", "journey_owner_identity_id", "intent_owner_identity_id"])
def test_each_owner_mismatch_fails_closed(owner_field):
    owner = str(uuid4())
    owners = {
        "booking_owner_identity_id": owner,
        "journey_owner_identity_id": owner,
        "intent_owner_identity_id": owner,
    }
    owners[owner_field] = str(uuid4())
    association = JourneyAssociation(str(uuid4()), str(uuid4()), "oap-book-" + "b" * 16)
    with pytest.raises(PermissionError, match="association_owner_mismatch"):
        authorize_association(association, actor_identity_id=owner, **owners)


def test_owner_gate_rejects_invalid_actor_identity():
    owner = str(uuid4())
    association = JourneyAssociation(str(uuid4()), str(uuid4()))
    with pytest.raises(ValueError, match="invalid_actor_identity_id"):
        authorize_association(
            association, actor_identity_id="untrusted", booking_owner_identity_id=owner,
            journey_owner_identity_id=owner,
        )


class _DeniedConnection:
    def execute(self, *_args, **_kwargs):
        raise AssertionError("database_must_not_be_touched")


def test_intent_persistence_fails_before_database_access():
    association = JourneyAssociation(str(uuid4()), str(uuid4()), "oap-book-" + "c" * 16)
    with pytest.raises(PermissionError, match="intent_owner_evidence_required"):
        associate_in_transaction(
            _DeniedConnection(), association,
            actor_identity_id=str(uuid4()), journey_owner_identity_id=str(uuid4()),
        )


def test_invalid_actor_fails_before_database_access():
    association = JourneyAssociation(str(uuid4()), str(uuid4()))
    with pytest.raises(ValueError, match="invalid_actor_identity_id"):
        associate_in_transaction(
            _DeniedConnection(), association,
            actor_identity_id="not-valid", journey_owner_identity_id=str(uuid4()),
        )
