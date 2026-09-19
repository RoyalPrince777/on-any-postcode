"""Unified first-party Incoming projection for Link Up.

Incoming aggregates existing OAP communication state. It does not create a
second notification store and does not depend on external push or analytics.
"""
from __future__ import annotations

import uuid
from typing import Any

from . import postgres_db

REQUIRED_TABLES = {
    "messages",
    "link_relationships",
    "link_voice_notes",
    "link_call_sessions",
    "link_circle_invites",
    "link_circles",
}

class LinkIncomingUnavailable(RuntimeError):
    pass

def _uuid(value: object, code: str = "invalid_identity") -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(code) from exc

def status() -> dict[str, Any]:
    result = {
        "configured": postgres_db.configured(),
        "ready": False,
        "first_party": True,
        "external_notification_provider_required": False,
        "sources": sorted(REQUIRED_TABLES),
    }
    if not result["configured"]:
        return result
    try:
        with postgres_db.connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT table_name FROM information_schema.tables
                   WHERE table_schema='public' AND table_name=ANY(%s)""",
                (list(REQUIRED_TABLES),),
            ).fetchall()
        present = {str(row[0]) for row in rows}
        result["ready"] = REQUIRED_TABLES <= present
        result["missing"] = sorted(REQUIRED_TABLES - present)
    except Exception:
        result["missing"] = sorted(REQUIRED_TABLES)
    return result

def list_incoming(identity_id: object, *, limit: int = 80) -> list[dict[str, object]]:
    identity = _uuid(identity_id)
    bounded = max(1, min(int(limit), 100))
    if not status().get("ready"):
        raise LinkIncomingUnavailable("incoming_unavailable")
    try:
        with postgres_db.connect(readonly=True) as connection:
            rows = connection.execute(
                """
                SELECT * FROM (
                  SELECT
                    'link'::text AS event_type,
                    m.id::text AS event_id,
                    m.sender_id::text AS peer_id,
                    COALESCE(u.display_name,u.username)::text AS peer_name,
                    'New Link'::text AS title,
                    left(m.body,160)::text AS detail,
                    m.created_at AS created_at
                  FROM messages m
                  JOIN users u ON u.id=m.sender_id
                  WHERE m.recipient_id=%s AND m.read_at IS NULL

                  UNION ALL

                  SELECT
                    'link_request'::text,
                    r.id::text,
                    r.requester_id::text,
                    COALESCE(u.display_name,u.username)::text,
                    'Link Request'::text,
                    CASE WHEN r.link_kind='purpose'
                         THEN COALESCE(r.purpose_text,'Purpose Link')
                         ELSE 'Wants to Link Up'
                    END::text,
                    r.created_at
                  FROM link_relationships r
                  JOIN users u ON u.id=r.requester_id
                  WHERE r.recipient_id=%s AND r.status='pending'

                  UNION ALL

                  SELECT
                    'voice'::text,
                    v.id::text,
                    v.sender_id::text,
                    COALESCE(u.display_name,u.username)::text,
                    'Voice'::text,
                    'New Voice landed'::text,
                    v.created_at
                  FROM link_voice_notes v
                  JOIN users u ON u.id=v.sender_id
                  WHERE v.recipient_id=%s
                    AND v.created_at>=CURRENT_TIMESTAMP - INTERVAL '7 days'

                  UNION ALL

                  SELECT
                    'missed_call'::text,
                    c.session_id::text,
                    c.initiator_id::text,
                    COALESCE(u.display_name,u.username)::text,
                    CASE WHEN c.mode='face_up' THEN 'Missed Face Up' ELSE 'Missed Call' END::text,
                    COALESCE(c.outcome,'ended')::text,
                    COALESCE(c.ended_at,c.started_at)
                  FROM link_call_sessions c
                  JOIN users u ON u.id=c.initiator_id
                  WHERE c.recipient_id=%s
                    AND c.state='ended'
                    AND c.answered_at IS NULL
                    AND c.outcome IN ('cancelled','declined','failed')
                    AND COALESCE(c.ended_at,c.started_at)>=CURRENT_TIMESTAMP - INTERVAL '7 days'

                  UNION ALL

                  SELECT
                    'circle_invite'::text,
                    i.id::text,
                    i.inviter_id::text,
                    COALESCE(u.display_name,u.username)::text,
                    'Circle Invite'::text,
                    c.name::text,
                    i.created_at
                  FROM link_circle_invites i
                  JOIN link_circles c ON c.id=i.circle_id
                  JOIN users u ON u.id=i.inviter_id
                  WHERE i.invitee_id=%s
                    AND i.status='pending'
                    AND c.status='active'
                ) incoming
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (identity, identity, identity, identity, identity, bounded),
            ).fetchall()
    except Exception as exc:
        raise LinkIncomingUnavailable("incoming_read_failed") from exc
    return [
        {
            "event_type": str(row[0]),
            "event_id": str(row[1]),
            "peer_id": str(row[2]),
            "peer_name": str(row[3]),
            "title": str(row[4]),
            "detail": str(row[5] or ""),
            "created_at": row[6].isoformat(),
        }
        for row in rows
    ]
