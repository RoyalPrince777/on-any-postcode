"""Race-safe certified matching boundary for OAP Movement.

This store subclasses the existing Movement persistence layer but hardens the
match proposal/acceptance path. It never dispatches a person; acceptance remains
an internal OAP booking state transition only.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from . import movement_operations, postgres_db


def _uuid(value: object, name: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"invalid_{name}") from exc


def _certified(connection: Any, identity_id: str, role_type: str) -> bool:
    role_id = movement_operations.MOVEMENT_ROLE_IDS[role_type]
    return (
        connection.execute(
            """SELECT 1 FROM oap_identity_roles
               WHERE identity_id=%s AND role_id=%s LIMIT 1""",
            (identity_id, role_id),
        ).fetchone()
        is not None
    )


class SafePostgresMovementStore(movement_operations.PostgresMovementStore):
    """Movement store with match-time certification and transactional race safety."""

    def certified_for_role(self, *, identity_id: object, role_type: object) -> bool:
        identity = _uuid(identity_id, "identity_id")
        role = movement_operations._role(role_type)
        with postgres_db.connect(readonly=True) as connection:
            return _certified(connection, identity, role)

    def propose_match(
        self, *, booking_id: object, member_identity_id: object
    ) -> dict[str, Any] | None:
        booking = _uuid(booking_id, "booking_id")
        member = _uuid(member_identity_id, "member_identity_id")
        with postgres_db.connect() as connection:
            booking_row = connection.execute(
                """SELECT service_type,pickup,state FROM oap_movement_bookings
                   WHERE booking_id=%s AND member_identity_id=%s
                   FOR UPDATE""",
                (booking, member),
            ).fetchone()
            if booking_row is None:
                raise PermissionError("booking_not_found")
            service = str(booking_row[0])
            if str(booking_row[2]) not in {"REQUESTED", "MATCH_PROPOSED"}:
                raise ValueError("booking_not_matchable")
            roles = {
                "ride": ("driver",),
                "delivery": ("rider", "courier"),
                "ebike": (),
            }[service]
            if not roles:
                return None
            pickup = dict(booking_row[1])
            zone = str(pickup.get("zone") or "").upper()
            role_placeholders = ",".join(["%s"] * len(roles))
            role_case = " ".join(
                f"WHEN '{role}' THEN '{movement_operations.MOVEMENT_ROLE_IDS[role]}'"
                for role in roles
            )
            query = f"""SELECT a.identity_id,a.role_type,a.zone
                         FROM oap_movement_availability a
                         WHERE a.availability_state='ONLINE'
                           AND a.role_type IN ({role_placeholders})
                           AND (a.available_until IS NULL
                                OR a.available_until > CURRENT_TIMESTAMP)
                           AND EXISTS (
                               SELECT 1 FROM oap_identity_roles ir
                               WHERE ir.identity_id=a.identity_id
                                 AND ir.role_id=(CASE a.role_type {role_case} END)
                           )
                         ORDER BY
                           CASE WHEN a.zone=%s AND %s<>'' THEN 0 ELSE 1 END,
                           a.updated_at DESC
                         LIMIT 1"""
            candidate = connection.execute(query, (*roles, zone, zone)).fetchone()
            if candidate is None:
                return None
            same_zone = bool(zone and str(candidate[2]).upper() == zone)
            score = 1.0 if same_zone else 0.5
            reason = "same_zone_certified_available" if same_zone else "certified_available_candidate"
            row = connection.execute(
                """INSERT INTO oap_movement_match_proposals
                   (booking_id,worker_identity_id,worker_role,score,reason)
                   VALUES (%s,%s,%s,%s,%s)
                   ON CONFLICT (booking_id,worker_identity_id,worker_role)
                   DO UPDATE SET state=CASE
                       WHEN oap_movement_match_proposals.state='ACCEPTED'
                       THEN 'ACCEPTED' ELSE 'PROPOSED' END,
                       score=EXCLUDED.score,reason=EXCLUDED.reason,
                       updated_at=CURRENT_TIMESTAMP
                   RETURNING proposal_id,worker_identity_id,worker_role,state,
                             score,reason,created_at""",
                (booking, candidate[0], candidate[1], score, reason),
            ).fetchone()
            connection.execute(
                """UPDATE oap_movement_bookings
                   SET state='MATCH_PROPOSED',updated_at=CURRENT_TIMESTAMP
                   WHERE booking_id=%s AND state='REQUESTED'""",
                (booking,),
            )
            connection.commit()
        return {
            "proposal_id": str(row[0]),
            "worker_identity_id": str(row[1]),
            "worker_role": str(row[2]),
            "state": str(row[3]),
            "score": float(row[4]),
            "reason": str(row[5]),
            "created_at": row[6].isoformat(),
            "current_certification_required": True,
            "dispatch_performed": False,
        }

    def accept_match(
        self, *, proposal_id: object, worker_identity_id: object
    ) -> dict[str, Any]:
        proposal = _uuid(proposal_id, "proposal_id")
        worker = _uuid(worker_identity_id, "worker_identity_id")
        with postgres_db.connect() as connection:
            proposal_row = connection.execute(
                """SELECT booking_id,worker_role,state
                   FROM oap_movement_match_proposals
                   WHERE proposal_id=%s AND worker_identity_id=%s
                   FOR UPDATE""",
                (proposal, worker),
            ).fetchone()
            if proposal_row is None or str(proposal_row[2]) != "PROPOSED":
                raise PermissionError("match_proposal_not_available")
            booking = str(proposal_row[0])
            role = str(proposal_row[1])

            booking_row = connection.execute(
                """SELECT state FROM oap_movement_bookings
                   WHERE booking_id=%s FOR UPDATE""",
                (booking,),
            ).fetchone()
            if booking_row is None or str(booking_row[0]) != "MATCH_PROPOSED":
                raise PermissionError("booking_not_available_for_match")

            availability = connection.execute(
                """SELECT availability_state,available_until
                   FROM oap_movement_availability
                   WHERE identity_id=%s AND role_type=%s
                   FOR UPDATE""",
                (worker, role),
            ).fetchone()
            if availability is None or str(availability[0]) != "ONLINE":
                raise PermissionError("worker_not_online")
            if availability[1] is not None:
                expiry = availability[1]
                if expiry.tzinfo is None:
                    expiry = expiry.replace(tzinfo=timezone.utc)
                if expiry.astimezone(timezone.utc) <= datetime.now(timezone.utc):
                    raise PermissionError("worker_availability_expired")
            if not _certified(connection, worker, role):
                raise PermissionError("certified_movement_role_required")

            accepted = connection.execute(
                """SELECT proposal_id FROM oap_movement_match_proposals
                   WHERE booking_id=%s AND state='ACCEPTED'
                   FOR UPDATE""",
                (booking,),
            ).fetchone()
            if accepted is not None:
                raise PermissionError("booking_already_matched")

            row = connection.execute(
                """UPDATE oap_movement_match_proposals
                   SET state='ACCEPTED',updated_at=CURRENT_TIMESTAMP
                   WHERE proposal_id=%s AND worker_identity_id=%s
                     AND state='PROPOSED'
                   RETURNING booking_id,worker_role,updated_at""",
                (proposal, worker),
            ).fetchone()
            if row is None:
                raise PermissionError("match_proposal_not_available")
            connection.execute(
                """UPDATE oap_movement_match_proposals
                   SET state='EXPIRED',updated_at=CURRENT_TIMESTAMP
                   WHERE booking_id=%s AND proposal_id<>%s AND state='PROPOSED'""",
                (booking, proposal),
            )
            updated_booking = connection.execute(
                """UPDATE oap_movement_bookings
                   SET state='ACCEPTED',updated_at=CURRENT_TIMESTAMP
                   WHERE booking_id=%s AND state='MATCH_PROPOSED'
                   RETURNING booking_id""",
                (booking,),
            ).fetchone()
            if updated_booking is None:
                raise PermissionError("booking_not_available_for_match")
            updated_availability = connection.execute(
                """UPDATE oap_movement_availability
                   SET availability_state='BUSY',updated_at=CURRENT_TIMESTAMP
                   WHERE identity_id=%s AND role_type=%s
                     AND availability_state='ONLINE'
                   RETURNING identity_id""",
                (worker, role),
            ).fetchone()
            if updated_availability is None:
                raise PermissionError("worker_not_online")
            connection.commit()
        return {
            "booking_id": str(row[0]),
            "worker_role": str(row[1]),
            "state": "ACCEPTED",
            "updated_at": row[2].isoformat(),
            "certification_revalidated": True,
            "availability_revalidated": True,
            "other_proposals_expired": True,
            "external_dispatch_performed": False,
        }


STORE = SafePostgresMovementStore()
