"""First-party OAP Ping Up attention runtime.

Ping Up is an attention event, not a message. It is allowed only between
accepted Links, respects blocks, supports per-peer mute, expires automatically,
and stores no message body, location, device fingerprint, or media.
"""
from __future__ import annotations

import uuid
from typing import Any

from . import link_relationships, linkup_safety, postgres_db

SCHEMA_VERSION = "link_ping_v1"
MAX_PINGS_PER_MINUTE = 6
PING_TTL_MINUTES = 60
ALLOWED_INTENSITIES = frozenset({"normal", "double", "priority"})

SCHEMA_SQL = (
    """CREATE TABLE IF NOT EXISTS link_ping_events (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        sender_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        recipient_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        intensity TEXT NOT NULL DEFAULT 'normal'
            CHECK (intensity IN ('normal','double','priority')),
        seen_at TIMESTAMPTZ,
        expires_at TIMESTAMPTZ NOT NULL DEFAULT
            (CURRENT_TIMESTAMP + INTERVAL '60 minutes'),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CHECK (sender_id <> recipient_id))""",
    """CREATE TABLE IF NOT EXISTS link_ping_mutes (
        owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        peer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        muted BOOLEAN NOT NULL DEFAULT TRUE,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (owner_id, peer_id),
        CHECK (owner_id <> peer_id))""",
    """CREATE INDEX IF NOT EXISTS idx_link_ping_recipient_unseen
        ON link_ping_events(recipient_id,seen_at,created_at DESC)""",
    "CREATE INDEX IF NOT EXISTS idx_link_ping_expiry ON link_ping_events(expires_at)",
)

class LinkPingUnavailable(RuntimeError):
    pass

def _uuid(value: object, code: str) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(code) from exc

def _peer_guard(first_id: object, second_id: object) -> tuple[str, str]:
    first = _uuid(first_id, "invalid_identity")
    second = _uuid(second_id, "invalid_peer")
    if first == second:
        raise ValueError("cannot_ping_self")
    try:
        if linkup_safety.blocked_between(first, second):
            raise ValueError("link_blocked")
        if not link_relationships.accepted_between(first, second):
            raise ValueError("accepted_link_required")
    except ValueError:
        raise
    except (
        linkup_safety.LinkUpSafetyUnavailable,
        link_relationships.LinkRelationshipsUnavailable,
    ) as exc:
        raise LinkPingUnavailable("ping_link_guard_unavailable") from exc
    return first, second

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
        raise LinkPingUnavailable("ping_schema_failed") from exc
    return {"version": SCHEMA_VERSION, "applied": True}

def status() -> dict[str, Any]:
    result = {
        "configured": postgres_db.configured(),
        "schema_ready": False,
        "ready": False,
        "first_party": True,
        "message_body_stored": False,
        "ttl_minutes": PING_TTL_MINUTES,
        "max_per_minute": MAX_PINGS_PER_MINUTE,
    }
    if not result["configured"]:
        return result
    try:
        with postgres_db.connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT table_name FROM information_schema.tables
                   WHERE table_schema='public'
                     AND table_name IN ('link_ping_events','link_ping_mutes')"""
            ).fetchall()
        tables = sorted(str(row[0]) for row in rows)
        result["schema_ready"] = tables == ["link_ping_events", "link_ping_mutes"]
    except Exception:
        return result
    result["ready"] = bool(result["schema_ready"])
    return result

def _muted(recipient: str, sender: str) -> bool:
    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT muted FROM link_ping_mutes
                   WHERE owner_id=%s AND peer_id=%s LIMIT 1""",
                (recipient, sender),
            ).fetchone()
    except Exception as exc:
        raise LinkPingUnavailable("ping_mute_read_failed") from exc
    return bool(row and row[0])

def send(sender_id: object, recipient_id: object, *, intensity: object = "normal") -> dict[str, object]:
    sender, recipient = _peer_guard(sender_id, recipient_id)
    kind = str(intensity or "normal").strip().casefold()
    if kind not in ALLOWED_INTENSITIES:
        raise ValueError("invalid_ping_intensity")
    if _muted(recipient, sender):
        raise ValueError("ping_muted")
    try:
        with postgres_db.connect() as connection:
            recent = connection.execute(
                """SELECT COUNT(*) FROM link_ping_events
                   WHERE sender_id=%s AND recipient_id=%s
                     AND created_at >= CURRENT_TIMESTAMP - INTERVAL '1 minute'""",
                (sender, recipient),
            ).fetchone()
            count = int(recent[0] or 0) if recent else 0
            cost = 2 if kind == "double" else 3 if kind == "priority" else 1
            if count + cost > MAX_PINGS_PER_MINUTE:
                raise ValueError("ping_rate_limited")
            connection.execute(
                "DELETE FROM link_ping_events WHERE expires_at<=CURRENT_TIMESTAMP"
            )
            row = connection.execute(
                """INSERT INTO link_ping_events(sender_id,recipient_id,intensity,expires_at)
                   VALUES (%s,%s,%s,CURRENT_TIMESTAMP + (%s * INTERVAL '1 minute'))
                   RETURNING id,created_at,expires_at""",
                (sender, recipient, kind, PING_TTL_MINUTES),
            ).fetchone()
            connection.commit()
    except ValueError:
        raise
    except Exception as exc:
        raise LinkPingUnavailable("ping_send_failed") from exc
    return {
        "ping_id": str(row[0]),
        "state": "landed",
        "intensity": kind,
        "created_at": row[1].isoformat(),
        "expires_at": row[2].isoformat(),
    }

def incoming(identity_id: object, *, limit: int = 50) -> list[dict[str, object]]:
    identity = _uuid(identity_id, "invalid_identity")
    safe_limit = max(1, min(int(limit), 100))
    try:
        with postgres_db.connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT p.id,p.sender_id,p.intensity,p.seen_at,p.created_at,p.expires_at,
                          COALESCE(u.display_name,u.username)
                   FROM link_ping_events p
                   JOIN users u ON u.id=p.sender_id
                   WHERE p.recipient_id=%s
                     AND p.expires_at>CURRENT_TIMESTAMP
                   ORDER BY p.created_at DESC LIMIT %s""",
                (identity, safe_limit),
            ).fetchall()
    except Exception as exc:
        raise LinkPingUnavailable("ping_incoming_failed") from exc
    return [
        {
            "ping_id": str(row[0]),
            "sender_id": str(row[1]),
            "sender_name": str(row[6]),
            "intensity": str(row[2]),
            "seen": row[3] is not None,
            "created_at": row[4].isoformat(),
            "expires_at": row[5].isoformat(),
        }
        for row in rows
    ]

def mark_seen(identity_id: object, ping_id: object) -> bool:
    identity = _uuid(identity_id, "invalid_identity")
    ping = _uuid(ping_id, "invalid_ping")
    try:
        with postgres_db.connect() as connection:
            row = connection.execute(
                """UPDATE link_ping_events
                   SET seen_at=COALESCE(seen_at,CURRENT_TIMESTAMP)
                   WHERE id=%s AND recipient_id=%s
                     AND expires_at>CURRENT_TIMESTAMP
                   RETURNING id""",
                (ping, identity),
            ).fetchone()
            connection.commit()
    except Exception as exc:
        raise LinkPingUnavailable("ping_seen_failed") from exc
    return row is not None

def set_mute(owner_id: object, peer_id: object, *, muted: object) -> bool:
    owner, peer = _peer_guard(owner_id, peer_id)
    if not isinstance(muted, bool):
        raise TypeError("invalid_ping_mute")
    try:
        with postgres_db.connect() as connection:
            connection.execute(
                """INSERT INTO link_ping_mutes(owner_id,peer_id,muted)
                   VALUES (%s,%s,%s)
                   ON CONFLICT (owner_id,peer_id) DO UPDATE SET
                     muted=EXCLUDED.muted,
                     updated_at=CURRENT_TIMESTAMP""",
                (owner, peer, muted),
            )
            connection.commit()
    except Exception as exc:
        raise LinkPingUnavailable("ping_mute_update_failed") from exc
    return muted
