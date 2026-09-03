"""Governed Link Requests and accepted Links for OAP Link Up.

Schema application is explicit. Importing this module never mutates production.
"""
from __future__ import annotations

import uuid
from typing import Any

from . import postgres_db

SCHEMA_VERSION = "linkup_connections_v1"
SCHEMA_SQL = (
    """CREATE TABLE IF NOT EXISTS linkup_requests (
        request_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        requester_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        recipient_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        status TEXT NOT NULL DEFAULT 'pending'
            CHECK (status IN ('pending','accepted','declined','cancelled')),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        resolved_at TIMESTAMPTZ,
        CHECK (requester_id <> recipient_id))""",
    """CREATE UNIQUE INDEX IF NOT EXISTS uq_linkup_pending_request_pair
       ON linkup_requests(LEAST(requester_id,recipient_id),GREATEST(requester_id,recipient_id))
       WHERE status='pending'""",
    """CREATE TABLE IF NOT EXISTS linkup_links (
        first_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        second_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (first_id, second_id),
        CHECK (first_id < second_id))""",
)


class LinkUpConnectionsUnavailable(RuntimeError):
    pass


def _uuid(value: object, code: str) -> str:
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
        raise LinkUpConnectionsUnavailable("linkup_connections_schema_failed") from exc
    return {"version": SCHEMA_VERSION, "applied": True}


def create_request(requester_id: object, recipient_id: object) -> str:
    requester = _uuid(requester_id, "invalid_requester")
    recipient = _uuid(recipient_id, "invalid_recipient")
    if requester == recipient:
        raise ValueError("cannot_link_self")
    first, second = sorted((requester, recipient))
    try:
        with postgres_db.connect() as connection:
            linked = connection.execute(
                "SELECT 1 FROM linkup_links WHERE first_id=%s AND second_id=%s",
                (first, second),
            ).fetchone()
            if linked:
                raise ValueError("already_linked")
            row = connection.execute(
                """INSERT INTO linkup_requests(requester_id,recipient_id)
                   VALUES (%s,%s) RETURNING request_id""",
                (requester, recipient),
            ).fetchone()
            connection.commit()
    except ValueError:
        raise
    except Exception as exc:
        raise LinkUpConnectionsUnavailable("link_request_failed") from exc
    return str(row[0])


def resolve_request(identity_id: object, request_id: object, decision: str) -> bool:
    identity = _uuid(identity_id, "invalid_identity")
    request = _uuid(request_id, "invalid_request")
    decision_value = str(decision or "").strip().lower()
    if decision_value not in {"accepted", "declined"}:
        raise ValueError("invalid_link_decision")
    try:
        with postgres_db.connect() as connection:
            row = connection.execute(
                """UPDATE linkup_requests
                   SET status=%s,resolved_at=CURRENT_TIMESTAMP
                   WHERE request_id=%s AND recipient_id=%s AND status='pending'
                   RETURNING requester_id,recipient_id""",
                (decision_value, request, identity),
            ).fetchone()
            if not row:
                connection.rollback()
                return False
            if decision_value == "accepted":
                first, second = sorted((str(row[0]), str(row[1])))
                connection.execute(
                    """INSERT INTO linkup_links(first_id,second_id)
                       VALUES (%s,%s) ON CONFLICT DO NOTHING""",
                    (first, second),
                )
            connection.commit()
    except Exception as exc:
        raise LinkUpConnectionsUnavailable("link_request_resolution_failed") from exc
    return True
