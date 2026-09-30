"""First-party speaking lease for an already-active private Link Call.

The database arbitrates the floor; it does not claim to intercept WebRTC media.
No schema is created at import or app startup. Explicit migration is required.
"""
from __future__ import annotations

import uuid

from . import link_call_audit, postgres_db

LEASE_SECONDS = 8
SCHEMA_VERSION = "link_ptt_floor_v1"
SCHEMA_SQL = (
    """CREATE TABLE IF NOT EXISTS link_ptt_floor (
        session_id UUID PRIMARY KEY REFERENCES link_call_sessions(session_id) ON DELETE CASCADE,
        holder_id UUID REFERENCES users(id) ON DELETE CASCADE,
        lease_until TIMESTAMPTZ NOT NULL,
        stopped BOOLEAN NOT NULL DEFAULT FALSE,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    "CREATE INDEX IF NOT EXISTS idx_link_ptt_floor_expiry ON link_ptt_floor(lease_until)",
)


class LinkPttFloorUnavailable(RuntimeError):
    pass


def _uuid(value: object, code: str) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(code) from exc


def status() -> dict[str, bool]:
    if not link_call_audit.status().get("ready"):
        return {"ready": False, "schema_ready": False, "mode_ready": False, "server_controls_media": False}
    table_ready = False
    mode_ready = False
    try:
        with postgres_db.connect(readonly=True) as connection:
            table_ready = connection.execute(
                """SELECT 1 FROM information_schema.tables
                   WHERE table_schema='public' AND table_name='link_ptt_floor'"""
            ).fetchone() is not None
            mode = connection.execute(
                """SELECT pg_get_constraintdef(oid) FROM pg_constraint
                   WHERE conrelid='link_call_sessions'::regclass
                     AND conname='link_call_sessions_mode_check'"""
            ).fetchone()
            mode_ready = bool(mode and "'ptt'" in str(mode[0]))
    except Exception:  # noqa: BLE001 - readiness must fail closed.
        table_ready = False
        mode_ready = False
    return {
        "ready": table_ready and mode_ready,
        "schema_ready": table_ready,
        "mode_ready": mode_ready,
        "server_controls_media": False,
    }


def init_schema(*, assume_yes: bool = False, dry_run: bool = False) -> dict:
    if not dry_run and not assume_yes:
        raise PermissionError("explicit_confirmation_required")
    if dry_run:
        return {"version": SCHEMA_VERSION, "statements": list(SCHEMA_SQL), "applied": False}
    if not link_call_audit.status().get("schema_ready"):
        raise LinkPttFloorUnavailable("link_call_schema_required")
    try:
        with postgres_db.connect() as connection:
            for statement in SCHEMA_SQL:
                connection.execute(statement)
            connection.commit()
    except Exception as exc:
        raise LinkPttFloorUnavailable("ptt_floor_schema_failed") from exc
    return {"version": SCHEMA_VERSION, "applied": True}


def _require_ready() -> None:
    if not status()["ready"]:
        raise LinkPttFloorUnavailable("ptt_floor_unavailable")


def _active_pair(connection, identity: str, session: str, *, lock: bool = True) -> str:
    # Lock the owning call first: a finished or expired session cannot obtain a floor.
    row = connection.execute(
        """SELECT initiator_id,recipient_id FROM link_call_sessions
           WHERE session_id=%s AND mode='ptt' AND state='active'
             AND expires_at>CURRENT_TIMESTAMP
             AND (initiator_id=%s OR recipient_id=%s)
           """ + (" FOR UPDATE" if lock else ""),
        (session, identity, identity),
    ).fetchone()
    if row is None:
        raise ValueError("active_ptt_call_required")
    first, second = str(row[0]), str(row[1])
    peer = second if identity == first else first
    link_call_audit._relationship_guard(identity, peer)
    link_call_audit._youth_guard(identity, peer)
    return peer


def floor(identity_id: object, session_id: object, *, action: str) -> dict:
    identity = _uuid(identity_id, "invalid_identity")
    session = _uuid(session_id, "invalid_call_session")
    if not isinstance(action, str) or action not in {"acquire", "release", "stop"}:
        raise ValueError("invalid_ptt_action")
    _require_ready()
    try:
        with postgres_db.connect() as connection:
            _active_pair(connection, identity, session)
            previous = connection.execute(
                """SELECT holder_id,lease_until>CURRENT_TIMESTAMP,stopped FROM link_ptt_floor
                   WHERE session_id=%s FOR UPDATE""",
                (session,),
            ).fetchone()
            holder = str(previous[0]) if previous and previous[1] else None
            stopped = bool(previous[2]) if previous else False
            if action == "acquire":
                if stopped:
                    raise ValueError("ptt_floor_stopped")
                if holder and holder != identity:
                    raise ValueError("ptt_floor_busy")
                connection.execute(
                    """INSERT INTO link_ptt_floor(session_id,holder_id,lease_until,updated_at,stopped)
                       VALUES (%s,%s,CURRENT_TIMESTAMP + (%s * INTERVAL '1 second'),CURRENT_TIMESTAMP,FALSE)
                       ON CONFLICT(session_id) DO UPDATE SET
                         holder_id=EXCLUDED.holder_id,
                         lease_until=EXCLUDED.lease_until,
                         updated_at=CURRENT_TIMESTAMP""",
                    (session, identity, LEASE_SECONDS),
                )
                result = {"granted": True, "holder_id": identity, "lease_seconds": LEASE_SECONDS}
            elif action == "stop":
                # Session-scoped tombstone: a queued acquire/renew cannot reverse STOP.
                connection.execute(
                    """INSERT INTO link_ptt_floor(session_id,holder_id,lease_until,stopped)
                       VALUES (%s,NULL,CURRENT_TIMESTAMP,TRUE)
                       ON CONFLICT(session_id) DO UPDATE SET
                         holder_id=NULL,lease_until=CURRENT_TIMESTAMP,stopped=TRUE,
                         updated_at=CURRENT_TIMESTAMP""",
                    (session,),
                )
                result = {"granted": False, "holder_id": None, "stopped": True}
            else:
                if holder and holder != identity:
                    raise ValueError("ptt_floor_not_holder")
                if not stopped:
                    connection.execute(
                        "DELETE FROM link_ptt_floor WHERE session_id=%s AND stopped=FALSE",
                        (session,),
                    )
                result = {"granted": False, "holder_id": None, "stopped": stopped}
            connection.commit()
    except (ValueError, link_call_audit.LinkCallAuditUnavailable):
        raise
    except Exception as exc:
        raise LinkPttFloorUnavailable("ptt_floor_mutation_failed") from exc
    return result


def read(identity_id: object, session_id: object) -> dict:
    identity = _uuid(identity_id, "invalid_identity")
    session = _uuid(session_id, "invalid_call_session")
    _require_ready()
    try:
        with postgres_db.connect(readonly=True) as connection:
            _active_pair(connection, identity, session, lock=False)
            row = connection.execute(
                """SELECT CASE WHEN lease_until>CURRENT_TIMESTAMP AND stopped=FALSE THEN holder_id END,stopped
                   FROM link_ptt_floor WHERE session_id=%s""",
                (session,),
            ).fetchone()
    except (ValueError, link_call_audit.LinkCallAuditUnavailable):
        raise
    except Exception as exc:
        raise LinkPttFloorUnavailable("ptt_floor_read_failed") from exc
    return {"holder_id": str(row[0]) if row and row[0] else None,
            "stopped": bool(row[1]) if row else False, "lease_seconds": LEASE_SECONDS}
