"""Additive, software-only identity association for OAP cross-service journeys.

This contract does not persist records, authorize access, book suppliers, dispatch,
charge, or confirm a reservation. Callers must validate ownership before use.
"""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

CONTRACT_VERSION = 1


def _uuid(value: str, field: str) -> str:
    try:
        return str(UUID(value))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"invalid_{field}") from exc


def _intent(value: str) -> str:
    if not isinstance(value, str) or not value.startswith("oap-book-"):
        raise ValueError("invalid_intent_id")
    suffix = value[len("oap-book-"):]
    if len(suffix) != 16 or any(char not in "0123456789abcdef" for char in suffix):
        raise ValueError("invalid_intent_id")
    return value


@dataclass(frozen=True)
class JourneyAssociation:
    """Identifiers remain owned by their existing services."""

    journey_id: str
    booking_id: str
    intent_id: str | None = None
    version: int = CONTRACT_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "journey_id", _uuid(self.journey_id, "journey_id"))
        object.__setattr__(self, "booking_id", _uuid(self.booking_id, "booking_id"))
        if self.intent_id is not None:
            object.__setattr__(self, "intent_id", _intent(self.intent_id))
        if type(self.version) is not int or self.version != CONTRACT_VERSION:
            raise ValueError("unsupported_contract_version")

    def same_identity(self, other: JourneyAssociation) -> bool:
        """A repeated association must be identical, never silently relinked."""
        return isinstance(other, JourneyAssociation) and self == other


def check_replay(existing: JourneyAssociation | None, proposed: JourneyAssociation) -> str:
    """Return CREATE or IDEMPOTENT; reject conflicts without side effects."""
    if not isinstance(proposed, JourneyAssociation):
        raise TypeError("association_required")
    if existing is None:
        return "CREATE"
    if not isinstance(existing, JourneyAssociation):
        raise TypeError("association_required")
    if existing.same_identity(proposed):
        return "IDEMPOTENT"
    raise ValueError("association_conflict")


def authorize_association(
    association: JourneyAssociation,
    *,
    actor_identity_id: str,
    booking_owner_identity_id: str,
    journey_owner_identity_id: str,
    intent_owner_identity_id: str | None = None,
) -> JourneyAssociation:
    """Fail closed unless authenticated actor owns every linked record.

    Owners must be loaded from trusted service records, never client claims.
    This function is a boundary helper, not a substitute for DB authorization.
    """
    if not isinstance(association, JourneyAssociation):
        raise TypeError("association_required")
    actor = _uuid(actor_identity_id, "actor_identity_id")
    booking_owner = _uuid(booking_owner_identity_id, "booking_owner_identity_id")
    journey_owner = _uuid(journey_owner_identity_id, "journey_owner_identity_id")
    if actor != booking_owner or actor != journey_owner:
        raise PermissionError("association_owner_mismatch")
    if association.intent_id is not None:
        if intent_owner_identity_id is None:
            raise PermissionError("intent_owner_evidence_required")
        if actor != _uuid(intent_owner_identity_id, "intent_owner_identity_id"):
            raise PermissionError("association_owner_mismatch")
    return association


def associate_in_transaction(
    connection,
    association: JourneyAssociation,
    *,
    actor_identity_id: str,
    journey_owner_identity_id: str,
) -> str:
    """Persist within caller's transaction; caller must commit or roll back.

    The journey owner must be resolved by the trusted Ride service. Booking
    ownership is checked against the Movement database under row lock.
    Intent associations are denied until durable intent ownership is available.
    Requires the separately approved global journey association migration.
    """
    if not isinstance(association, JourneyAssociation):
        raise TypeError("association_required")
    if association.intent_id is not None:
        raise PermissionError("intent_owner_evidence_required")
    actor = _uuid(actor_identity_id, "actor_identity_id")
    ride_owner = _uuid(journey_owner_identity_id, "journey_owner_identity_id")
    row = connection.execute(
        "SELECT member_identity_id FROM oap_movement_bookings "
        "WHERE booking_id=%s FOR UPDATE",
        (association.booking_id,),
    ).fetchone()
    if row is None:
        raise ValueError("booking_not_found")
    authorize_association(
        association,
        actor_identity_id=actor,
        booking_owner_identity_id=str(row[0]),
        journey_owner_identity_id=ride_owner,
    )
    existing = connection.execute(
        "SELECT journey_id, booking_id, intent_id, version "
        "FROM oap_global_journey_associations "
        "WHERE journey_id=%s OR booking_id=%s FOR UPDATE",
        (association.journey_id, association.booking_id),
    ).fetchall()
    if existing:
        if len(existing) != 1:
            raise ValueError("association_conflict")
        stored = JourneyAssociation(str(existing[0][0]), str(existing[0][1]), existing[0][2], existing[0][3])
        return check_replay(stored, association)
    connection.execute(
        "INSERT INTO oap_global_journey_associations "
        "(journey_id, booking_id, intent_id, version, owner_identity_id) "
        "VALUES (%s,%s,%s,%s,%s)",
        (association.journey_id, association.booking_id, association.intent_id, association.version, actor),
    )
    return "CREATE"
