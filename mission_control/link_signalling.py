"""Ephemeral first-party signalling exchange for OAP Link Up.

This module carries WebRTC negotiation metadata only. It is not a message store,
does not record media, and never creates schema during import or app startup.
Production stays fail-closed until the explicit schema gate is applied.
"""
from __future__ import annotations

import json
import uuid
from collections.abc import Mapping
from typing import Any

from . import link_call_audit, linkup_safety, postgres_db

SCHEMA_VERSION = "link_signalling_v1"
EVENT_TTL_MINUTES = 5
MAX_PAYLOAD_BYTES = 32 * 1024
MAX_EVENTS_PER_MINUTE = 300
ALLOWED_EVENT_TYPES = frozenset({"offer", "answer", "ice", "hangup"})

SCHEMA_SQL = (
    """CREATE TABLE IF NOT EXISTS link_signalling_events (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        session_id UUID NOT NULL,
        sender_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        recipient_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        event_type TEXT NOT NULL CHECK (event_type IN ('offer','answer','ice','hangup')),
        payload JSONB NOT NULL DEFAULT '{}'::jsonb,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMPTZ NOT NULL DEFAULT (CURRENT_TIMESTAMP + INTERVAL '5 minutes'),
        CHECK (sender_id <> recipient_id),
        CHECK (octet_length(payload::text) <= 32768))""",
    """CREATE INDEX IF NOT EXISTS idx_link_signalling_recipient_session
        ON link_signalling_events(recipient_id, session_id, created_at)""",
    "CREATE INDEX IF NOT EXISTS idx_link_signalling_expiry ON link_signalling_events(expires_at)",
    "CREATE INDEX IF NOT EXISTS idx_link_signalling_sender_created ON link_signalling_events(sender_id, created_at DESC)",
)


class LinkSignallingUnavailable(RuntimeError):
    pass


def _uuid(value: object, code: str) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(code) from exc


def _event_type(value: object) -> str:
    event_type = str(value or "").strip().casefold()
    if event_type not in ALLOWED_EVENT_TYPES:
        raise ValueError("invalid_signalling_event")
    return event_type


def _payload(value: object) -> tuple[dict[str, Any], str]:
    if value is None:
        payload: dict[str, Any] = {}
    elif isinstance(value, Mapping):
        payload = {str(key): item for key, item in value.items()}
    else:
        raise ValueError("invalid_signalling_payload")
    try:
        encoded = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid_signalling_payload") from exc
    if len(encoded.encode("utf-8")) > MAX_PAYLOAD_BYTES:
        raise ValueError("signalling_payload_too_large")
    return payload, encoded


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
        raise LinkSignallingUnavailable("link_signalling_schema_failed") from exc
    return {"version": SCHEMA_VERSION, "applied": True}


def status() -> dict[str, Any]:
    result = {"configured": postgres_db.configured(), "ready": False}
    if not result["configured"]:
        return result
    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT 1 FROM information_schema.tables
                   WHERE table_schema='public' AND table_name='link_signalling_events'"""
            ).fetchone()
        result["ready"] = row is not None
    except Exception:  # noqa: BLE001 - readiness must fail closed.
        return result
    return result


def _accepted_between(connection, first: str, second: str) -> bool:
    row = connection.execute(
        """SELECT 1 FROM link_relationships
           WHERE LEAST(requester_id,recipient_id)=LEAST(%s::uuid,%s::uuid)
             AND GREATEST(requester_id,recipient_id)=GREATEST(%s::uuid,%s::uuid)
             AND status='accepted'
             AND (link_kind='permanent' OR expires_at>CURRENT_TIMESTAMP)
           LIMIT 1""",
        (first, second, first, second),
    ).fetchone()
    return row is not None


def _call_pair_allowed(first: str, second: str, session: str) -> None:
    try:
        if not link_call_audit.session_allows_signalling(first, second, session):
            raise ValueError("active_call_session_required")
    except ValueError:
        raise
    except link_call_audit.LinkCallAuditUnavailable as exc:
        raise LinkSignallingUnavailable("link_call_audit_unavailable") from exc


def _call_identity_allowed(identity: str, session: str) -> None:
    try:
        if not link_call_audit.identity_allows_signalling(identity, session):
            raise ValueError("active_call_session_required")
    except ValueError:
        raise
    except link_call_audit.LinkCallAuditUnavailable as exc:
        raise LinkSignallingUnavailable("link_call_audit_unavailable") from exc


def publish(
    sender_id: object,
    recipient_id: object,
    *,
    session_id: object,
    event_type: object,
    payload: object = None,
) -> str:
    sender = _uuid(sender_id, "invalid_sender")
    recipient = _uuid(recipient_id, "invalid_recipient")
    session = _uuid(session_id, "invalid_signalling_session")
    kind = _event_type(event_type)
    _, encoded_payload = _payload(payload)
    if sender == recipient:
        raise ValueError("cannot_signal_self")
    try:
        if linkup_safety.blocked_between(sender, recipient):
            raise ValueError("link_blocked")
        _call_pair_allowed(sender, recipient, session)
        with postgres_db.connect() as connection:
            if not _accepted_between(connection, sender, recipient):
                raise ValueError("accepted_link_required")
            recent = connection.execute(
                """SELECT COUNT(*) FROM link_signalling_events
                   WHERE sender_id=%s AND created_at>CURRENT_TIMESTAMP-INTERVAL '1 minute'""",
                (sender,),
            ).fetchone()
            if recent and int(recent[0]) >= MAX_EVENTS_PER_MINUTE:
                raise ValueError("signalling_rate_limited")
            connection.execute(
                "DELETE FROM link_signalling_events WHERE expires_at<=CURRENT_TIMESTAMP"
            )
            row = connection.execute(
                """INSERT INTO link_signalling_events(
                       session_id,sender_id,recipient_id,event_type,payload,expires_at)
                   VALUES (%s,%s,%s,%s,%s::jsonb,CURRENT_TIMESTAMP + INTERVAL '5 minutes')
                   RETURNING id""",
                (session, sender, recipient, kind, encoded_payload),
            ).fetchone()
            connection.commit()
    except ValueError:
        raise
    except linkup_safety.LinkUpSafetyUnavailable as exc:
        raise LinkSignallingUnavailable("link_signalling_safety_unavailable") from exc
    except LinkSignallingUnavailable:
        raise
    except Exception as exc:
        raise LinkSignallingUnavailable("link_signalling_publish_failed") from exc
    return str(row[0])


def list_events(identity_id: object, *, session_id: object, limit: int = 100) -> list[dict[str, Any]]:
    identity = _uuid(identity_id, "invalid_identity")
    session = _uuid(session_id, "invalid_signalling_session")
    safe_limit = min(100, max(1, int(limit)))
    _call_identity_allowed(identity, session)
    try:
        with postgres_db.connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT id,sender_id,event_type,payload,created_at
                   FROM link_signalling_events
                   WHERE recipient_id=%s AND session_id=%s AND expires_at>CURRENT_TIMESTAMP
                   ORDER BY created_at ASC LIMIT %s""",
                (identity, session, safe_limit),
            ).fetchall()
    except Exception as exc:
        raise LinkSignallingUnavailable("link_signalling_read_failed") from exc
    events: list[dict[str, Any]] = []
    for row in rows:
        payload = row[3]
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                payload = {}
        events.append(
            {
                "event_id": str(row[0]),
                "sender_id": str(row[1]),
                "event_type": str(row[2]),
                "payload": payload if isinstance(payload, dict) else {},
                "created_at": row[4].isoformat(),
            }
        )
    return events


def acknowledge(identity_id: object, event_id: object) -> bool:
    identity = _uuid(identity_id, "invalid_identity")
    event = _uuid(event_id, "invalid_signalling_event_id")
    try:
        with postgres_db.connect() as connection:
            row = connection.execute(
                """DELETE FROM link_signalling_events
                   WHERE id=%s AND recipient_id=%s RETURNING id""",
                (event, identity),
            ).fetchone()
            connection.commit()
    except Exception as exc:
        raise LinkSignallingUnavailable("link_signalling_ack_failed") from exc
    return row is not None


def purge_expired() -> int:
    try:
        with postgres_db.connect() as connection:
            result = connection.execute(
                "DELETE FROM link_signalling_events WHERE expires_at<=CURRENT_TIMESTAMP"
            )
            removed = int(result.rowcount or 0)
            connection.commit()
    except Exception as exc:
        raise LinkSignallingUnavailable("link_signalling_purge_failed") from exc
    return removed
