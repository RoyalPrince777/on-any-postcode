"""Short-lived first-party OAP Link typing activity.

Only a bounded boolean-like activity signal is stored. No keystrokes, draft text,
message content, device fingerprint or analytics identifier is persisted.
Schema activation is explicit and never runs at import/startup.
"""
from __future__ import annotations

import uuid
from typing import Any

from . import link_relationships, linkup_safety, postgres_db

SCHEMA_VERSION = "link_activity_v1"
TYPING_TTL_SECONDS = 8
SCHEMA_SQL = (
    """CREATE TABLE IF NOT EXISTS link_typing_activity (
        identity_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        peer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        expires_at TIMESTAMPTZ NOT NULL,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY(identity_id,peer_id),
        CHECK(identity_id <> peer_id))""",
    "CREATE INDEX IF NOT EXISTS idx_link_typing_peer_expiry ON link_typing_activity(peer_id,expires_at)",
    "CREATE INDEX IF NOT EXISTS idx_link_typing_expiry ON link_typing_activity(expires_at)",
)


class LinkActivityUnavailable(RuntimeError):
    pass


def _uuid(value: object, code: str) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(code) from exc


def _guard(first_id: object, second_id: object) -> tuple[str, str]:
    first = _uuid(first_id, "invalid_identity")
    second = _uuid(second_id, "invalid_peer")
    if first == second:
        raise ValueError("cannot_activity_self")
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
        raise LinkActivityUnavailable("activity_link_guard_unavailable") from exc
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
        raise LinkActivityUnavailable("activity_schema_failed") from exc
    return {"version": SCHEMA_VERSION, "applied": True}


def status() -> dict[str, object]:
    result: dict[str, object] = {
        "configured": postgres_db.configured(),
        "schema_ready": False,
        "ready": False,
        "first_party": True,
        "stores_content": False,
        "typing_ttl_seconds": TYPING_TTL_SECONDS,
    }
    if not result["configured"]:
        return result
    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT 1 FROM information_schema.tables
                   WHERE table_schema='public' AND table_name='link_typing_activity'"""
            ).fetchone()
        result["schema_ready"] = row is not None
    except Exception:  # noqa: BLE001 - coarse fail-closed status only.
        return result
    result["ready"] = bool(result["schema_ready"])
    return result


def set_typing(identity_id: object, peer_id: object, *, active: bool) -> bool:
    identity = _uuid(identity_id, "invalid_identity")
    peer = _uuid(peer_id, "invalid_peer")
    if identity == peer:
        raise ValueError("cannot_activity_self")

    # Stopping your own activity must remain possible after a Block/revoke.
    if not active:
        try:
            with postgres_db.connect() as connection:
                connection.execute(
                    "DELETE FROM link_typing_activity WHERE identity_id=%s AND peer_id=%s",
                    (identity, peer),
                )
                connection.commit()
        except Exception as exc:
            raise LinkActivityUnavailable("activity_stop_failed") from exc
        return False

    identity, peer = _guard(identity, peer)
    try:
        with postgres_db.connect() as connection:
            connection.execute(
                """INSERT INTO link_typing_activity(identity_id,peer_id,expires_at,updated_at)
                   VALUES (%s,%s,CURRENT_TIMESTAMP + INTERVAL '8 seconds',CURRENT_TIMESTAMP)
                   ON CONFLICT(identity_id,peer_id) DO UPDATE
                   SET expires_at=EXCLUDED.expires_at,updated_at=CURRENT_TIMESTAMP""",
                (identity, peer),
            )
            connection.commit()
    except Exception as exc:
        raise LinkActivityUnavailable("activity_write_failed") from exc
    return True


def peer_typing(identity_id: object, peer_id: object) -> bool:
    identity, peer = _guard(identity_id, peer_id)
    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT 1 FROM link_typing_activity
                   WHERE identity_id=%s AND peer_id=%s
                     AND expires_at>CURRENT_TIMESTAMP LIMIT 1""",
                (peer, identity),
            ).fetchone()
    except Exception as exc:
        raise LinkActivityUnavailable("activity_read_failed") from exc
    return row is not None


def purge_expired() -> int:
    try:
        with postgres_db.connect() as connection:
            result = connection.execute(
                "DELETE FROM link_typing_activity WHERE expires_at<=CURRENT_TIMESTAMP"
            )
            connection.commit()
            return int(result.rowcount or 0)
    except Exception as exc:
        raise LinkActivityUnavailable("activity_purge_failed") from exc
