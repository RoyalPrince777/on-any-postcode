"""Durable journey identity adapter for the existing Movement engine.

Journey IDs are minted on the server from a locked, owned Movement booking.
Legacy in-memory Ride UUIDs and Booking Core intents are never adopted by claim.
"""
from uuid import uuid4

from . import global_journey_contract, postgres_db


def ensure_booking_journey(connection, *, booking_id: str, owner_identity_id: str) -> str:
    row = connection.execute(
        """SELECT b.member_identity_id,i.status FROM oap_movement_bookings b
           JOIN oap_identities i ON i.identity_id=b.member_identity_id
           WHERE b.booking_id=%s FOR UPDATE OF b""", (booking_id,),
    ).fetchone()
    if row is None or str(row[0]) != owner_identity_id or str(row[1]) != "ACTIVE":
        raise PermissionError("journey_owner_required")
    existing = connection.execute(
        """SELECT journey_id,owner_identity_id,version,intent_id FROM oap_global_journey_associations
           WHERE booking_id=%s FOR UPDATE""", (booking_id,),
    ).fetchone()
    if existing is not None:
        if str(existing[1]) != owner_identity_id or existing[2] != 1:
            raise PermissionError("association_owner_mismatch")
        if existing[3] is not None:
            raise PermissionError("intent_owner_evidence_required")
        return str(existing[0])
    association = global_journey_contract.JourneyAssociation(str(uuid4()), booking_id)
    global_journey_contract.associate_in_transaction(
        connection, association, actor_identity_id=owner_identity_id,
        journey_owner_identity_id=owner_identity_id,
    )
    return association.journey_id


def read_journey(*, journey_id: object, identity_id: object) -> dict | None:
    journey = global_journey_contract._uuid(str(journey_id), "journey_id")
    identity = global_journey_contract._uuid(str(identity_id), "identity_id")
    with postgres_db.connect(readonly=True) as connection:
        row = connection.execute(
            """SELECT a.journey_id,b.booking_id,b.service_type,b.state,c.cancelled_at
               FROM oap_global_journey_associations a
               JOIN oap_movement_bookings b ON b.booking_id=a.booking_id
               LEFT JOIN oap_journey_cancellations c ON c.booking_id=b.booking_id
               WHERE a.journey_id=%s AND a.owner_identity_id=%s
                 AND b.member_identity_id=%s AND a.version=1 AND a.intent_id IS NULL""", (journey, identity, identity),
        ).fetchone()
    if row is None:
        return None
    return {"journey_id": str(row[0]), "booking_id": str(row[1]), "service_type": str(row[2]),
            "state": str(row[3]), "cancelled_at": row[4].isoformat() if row[4] else None,
            "external_dispatch_performed": False, "payment_performed": False}
