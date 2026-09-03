"""Governed Link Request and accepted Link relationship store.

Schema changes remain explicit. Importing this module never mutates production.
Accepted Link Requests are the canonical relationship record; no duplicate Links
or Conversations table is introduced.
"""
from __future__ import annotations

import uuid
from typing import Any

from . import postgres_db

SCHEMA_VERSION = "link_relationships_v1"
SCHEMA_SQL = (
    """CREATE TABLE IF NOT EXISTS link_requests (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        requester_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        recipient_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        status TEXT NOT NULL DEFAULT 'pending'
            CHECK (status IN ('pending','accepted','declined','cancelled')),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        responded_at TIMESTAMPTZ,
        CHECK (requester_id <> recipient_id))""",
    """CREATE UNIQUE INDEX IF NOT EXISTS ux_link_requests_pending_pair
        ON link_requests (LEAST(requester_id,recipient_id), GREATEST(requester_id,recipient_id))
        WHERE status='pending'""",
    """CREATE UNIQUE INDEX IF NOT EXISTS ux_link_requests_accepted_pair
        ON link_requests (LEAST(requester_id,recipient_id), GREATEST(requester_id,recipient_id))
        WHERE status='accepted'""",
    """CREATE INDEX IF NOT EXISTS ix_link_requests_recipient_status_created
        ON link_requests(recipient_id,status,created_at DESC)""",
    """CREATE INDEX IF NOT EXISTS ix_link_requests_requester_status_created
        ON link_requests(requester_id,status,created_at DESC)""",
)


class LinkRelationshipUnavailable(RuntimeError):
    pass


def _uuid(value: object, code: str = "invalid_identity") -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(code) from exc


def init_schema(*, assume_yes: bool = False, dry_run: bool = False) -> dict[str, Any]:
    if not assume_yes and not dry_run:
        raise PermissionError("explicit_confirmation_required")
    if dry_run:
        return {"version": SCHEMA_VERSION, "statements": list(SCHEMA_SQL), "applied": False}
    try:
        with postgres_db.connect() as connection:
            for statement in SCHEMA_SQL:
                connection.execute(statement)
            connection.commit()
    except Exception as exc:
        raise LinkRelationshipUnavailable("link_relationship_schema_failed") from exc
    return {"version": SCHEMA_VERSION, "applied": True}


def status() -> dict[str, Any]:
    result = {"configured": postgres_db.configured(), "ready": False, "table": False}
    if not result["configured"]:
        return result
    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT 1 FROM information_schema.tables
                   WHERE table_schema='public' AND table_name='link_requests'"""
            ).fetchone()
        result["table"] = row is not None
        result["ready"] = result["table"]
    except Exception:
        return result
    return result


def dashboard(identity_id: object) -> dict[str, Any]:
    identity = _uuid(identity_id)
    try:
        with postgres_db.connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT r.id,r.requester_id,r.recipient_id,r.status,r.created_at,r.responded_at,
                          COALESCE(a.display_name,a.username),COALESCE(b.display_name,b.username)
                   FROM link_requests r
                   JOIN users a ON a.id=r.requester_id
                   JOIN users b ON b.id=r.recipient_id
                   WHERE r.requester_id=%s OR r.recipient_id=%s
                   ORDER BY r.created_at DESC LIMIT 200""",
                (identity, identity),
            ).fetchall()
    except Exception as exc:
        raise LinkRelationshipUnavailable("link_relationship_read_failed") from exc
    incoming, outgoing, links = [], [], []
    for row in rows:
        requester, recipient, state = str(row[1]), str(row[2]), str(row[3])
        other_id = recipient if requester == identity else requester
        other_name = str(row[7] if requester == identity else row[6])
        item = {
            "request_id": str(row[0]), "other_identity_id": other_id,
            "display_name": other_name, "status": state,
            "created_at": row[4].isoformat(),
            "responded_at": row[5].isoformat() if row[5] else None,
        }
        if state == "accepted":
            links.append(item)
        elif state == "pending" and recipient == identity:
            incoming.append(item)
        elif state == "pending" and requester == identity:
            outgoing.append(item)
    return {"incoming": incoming, "outgoing": outgoing, "links": links}


def request_link(requester_id: object, recipient_id: object) -> str:
    requester = _uuid(requester_id, "invalid_requester")
    recipient = _uuid(recipient_id, "invalid_recipient")
    if requester == recipient:
        raise ValueError("cannot_link_self")
    try:
        with postgres_db.connect() as connection:
            active = connection.execute(
                "SELECT id FROM users WHERE id IN (%s,%s) AND status='active'",
                (requester, recipient),
            ).fetchall()
            if {str(row[0]) for row in active} != {requester, recipient}:
                raise ValueError("member_unavailable")
            blocked = connection.execute(
                """SELECT 1 FROM linkup_blocks WHERE
                   (blocker_id=%s AND blocked_id=%s) OR
                   (blocker_id=%s AND blocked_id=%s) LIMIT 1""",
                (requester, recipient, recipient, requester),
            ).fetchone()
            if blocked:
                raise ValueError("link_unavailable")
            existing = connection.execute(
                """SELECT status FROM link_requests
                   WHERE LEAST(requester_id,recipient_id)=LEAST(%s::uuid,%s::uuid)
                     AND GREATEST(requester_id,recipient_id)=GREATEST(%s::uuid,%s::uuid)
                     AND status IN ('pending','accepted') LIMIT 1""",
                (requester, recipient, requester, recipient),
            ).fetchone()
            if existing:
                raise ValueError("link_already_exists" if str(existing[0]) == "accepted" else "link_request_pending")
            row = connection.execute(
                """INSERT INTO link_requests(requester_id,recipient_id)
                   VALUES (%s,%s) RETURNING id""", (requester, recipient)
            ).fetchone()
            connection.commit()
    except ValueError:
        raise
    except Exception as exc:
        raise LinkRelationshipUnavailable("link_request_failed") from exc
    return str(row[0])


def respond(identity_id: object, request_id: object, decision: str) -> bool:
    identity = _uuid(identity_id)
    request_value = _uuid(request_id, "invalid_link_request")
    decision_value = str(decision).strip().lower()
    if decision_value not in {"accepted", "declined"}:
        raise ValueError("invalid_link_decision")
    try:
        with postgres_db.connect() as connection:
            row = connection.execute(
                """UPDATE link_requests SET status=%s,responded_at=CURRENT_TIMESTAMP
                   WHERE id=%s AND recipient_id=%s AND status='pending' RETURNING id""",
                (decision_value, request_value, identity),
            ).fetchone()
            connection.commit()
    except Exception as exc:
        raise LinkRelationshipUnavailable("link_response_failed") from exc
    return row is not None


def cancel(identity_id: object, request_id: object) -> bool:
    identity = _uuid(identity_id)
    request_value = _uuid(request_id, "invalid_link_request")
    try:
        with postgres_db.connect() as connection:
            row = connection.execute(
                """UPDATE link_requests SET status='cancelled',responded_at=CURRENT_TIMESTAMP
                   WHERE id=%s AND requester_id=%s AND status='pending' RETURNING id""",
                (request_value, identity),
            ).fetchone()
            connection.commit()
    except Exception as exc:
        raise LinkRelationshipUnavailable("link_cancel_failed") from exc
    return row is not None
