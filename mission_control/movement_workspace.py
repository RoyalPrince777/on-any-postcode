"""Read-only private workspace projection for OAP Movement.

This module deliberately exposes only data that belongs to the authenticated
member/worker. It never lists other workers globally, never returns precise
tracking coordinates, and never mutates booking, availability or match state.
"""
from __future__ import annotations

from typing import Any
from uuid import UUID

from . import postgres_db

WORKER_ROLE_IDS = frozenset(
    {"MOVEMENT_DRIVER", "MOVEMENT_RIDER", "MOVEMENT_COURIER"}
)


class MovementWorkspaceUnavailable(RuntimeError):
    """Raised when the private Movement projection cannot be loaded safely."""


def _identity(value: object) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("invalid_identity_id") from exc


def _iso(value: object) -> str | None:
    if value is None:
        return None
    isoformat = getattr(value, "isoformat", None)
    return str(isoformat()) if callable(isoformat) else str(value)


def snapshot(identity_id: object, *, limit: int = 20) -> dict[str, Any]:
    """Return a bounded, object-authorized Movement workspace snapshot."""

    identity = _identity(identity_id)
    bounded_limit = min(max(int(limit), 1), 50)
    try:
        with postgres_db.connect(readonly=True) as connection:
            booking_rows = connection.execute(
                """SELECT booking_id::text, service_type, state,
                          pickup->>'label', pickup->>'zone',
                          destination->>'label', destination->>'zone',
                          scheduled_for, route_snapshot, created_at, updated_at
                     FROM oap_movement_bookings
                    WHERE member_identity_id=%s
                    ORDER BY created_at DESC
                    LIMIT %s""",
                (identity, bounded_limit),
            ).fetchall()
            availability_rows = connection.execute(
                """SELECT role_type, availability_state, zone,
                          available_until, updated_at
                     FROM oap_movement_availability
                    WHERE identity_id=%s
                    ORDER BY role_type""",
                (identity,),
            ).fetchall()
            worker_match_rows = connection.execute(
                """SELECT p.proposal_id::text, p.booking_id::text,
                          p.worker_role, p.state, p.score, p.reason,
                          b.service_type, b.state,
                          b.pickup->>'zone', b.destination->>'zone',
                          p.created_at, p.updated_at
                     FROM oap_movement_match_proposals p
                     JOIN oap_movement_bookings b
                       ON b.booking_id=p.booking_id
                    WHERE p.worker_identity_id=%s
                    ORDER BY p.created_at DESC
                    LIMIT %s""",
                (identity, bounded_limit),
            ).fetchall()
            member_match_rows = connection.execute(
                """SELECT p.proposal_id::text, p.booking_id::text,
                          p.worker_role, p.state, p.score, p.reason,
                          p.created_at, p.updated_at
                     FROM oap_movement_match_proposals p
                     JOIN oap_movement_bookings b
                       ON b.booking_id=p.booking_id
                    WHERE b.member_identity_id=%s
                    ORDER BY p.created_at DESC
                    LIMIT %s""",
                (identity, bounded_limit),
            ).fetchall()
            role_rows = connection.execute(
                """SELECT role_id
                     FROM oap_identity_roles
                    WHERE identity_id=%s
                      AND role_id IN ('MOVEMENT_DRIVER','MOVEMENT_RIDER',
                                      'MOVEMENT_COURIER')
                    ORDER BY role_id""",
                (identity,),
            ).fetchall()
    except Exception as exc:
        raise MovementWorkspaceUnavailable("movement_workspace_unavailable") from exc

    bookings = []
    for row in booking_rows:
        route_snapshot = row[8] if isinstance(row[8], dict) else {}
        bookings.append(
            {
                "booking_id": row[0],
                "service_type": row[1],
                "state": row[2],
                "pickup_label": row[3] or "",
                "pickup_zone": row[4] or "",
                "destination_label": row[5] or "",
                "destination_zone": row[6] or "",
                "scheduled_for": _iso(row[7]),
                "route_distance_m": route_snapshot.get("distance_m"),
                "route_duration_s": route_snapshot.get("duration_s"),
                "route_ready": bool(route_snapshot),
                "created_at": _iso(row[9]),
                "updated_at": _iso(row[10]),
            }
        )

    availability = [
        {
            "role_type": row[0],
            "state": row[1],
            "zone": row[2] or "",
            "available_until": _iso(row[3]),
            "updated_at": _iso(row[4]),
        }
        for row in availability_rows
    ]
    worker_matches = [
        {
            "proposal_id": row[0],
            "booking_id": row[1],
            "worker_role": row[2],
            "proposal_state": row[3],
            "score": float(row[4]),
            "reason": row[5],
            "service_type": row[6],
            "booking_state": row[7],
            "pickup_zone": row[8] or "",
            "destination_zone": row[9] or "",
            "created_at": _iso(row[10]),
            "updated_at": _iso(row[11]),
        }
        for row in worker_match_rows
    ]
    member_matches = [
        {
            "proposal_id": row[0],
            "booking_id": row[1],
            "worker_role": row[2],
            "proposal_state": row[3],
            "score": float(row[4]),
            "reason": row[5],
            "created_at": _iso(row[6]),
            "updated_at": _iso(row[7]),
        }
        for row in member_match_rows
    ]
    certified_roles = [str(row[0]) for row in role_rows if str(row[0]) in WORKER_ROLE_IDS]

    return {
        "bookings": bookings,
        "availability": availability,
        "worker_matches": worker_matches,
        "member_matches": member_matches,
        "certified_roles": certified_roles,
        "precise_tracking_exposed": False,
        "other_worker_directory_exposed": False,
    }
