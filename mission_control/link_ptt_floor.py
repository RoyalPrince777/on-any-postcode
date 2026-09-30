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
        holder_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        lease_until TIMESTAMPTZ NOT NULL,
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
        return {"ready": False, "schema_ready": False, "server_controls_media": False}
    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT 1 FROM information_schema.tables
                   WHERE table_schema='public' AND table_name='link_ptt_floor'"""
            ).fetchone()
    except Exception:  # noqa: BLE001 - readiness must fail closed.
        row = None
    return {
        "ready": row is not None,
        "schema_ready": row is not None,
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
           WHERE session_id=%s AND state='active'
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
    if action not in {"acquire", "release", "stop"}:
        raise ValueError("invalid_ptt_action")
    _require_ready()
    try:
        with postgres_db.connect() as connection:
            _active_pair(connection, identity, session)
            previous = connection.execute(
                """SELECT holder_id,lease_until>CURRENT_TIMESTAMP FROM link_ptt_floor
                   WHERE session_id=%s FOR UPDATE""",
                (session,),
            ).fetchone()
            holder = str(previous[0]) if previous and previous[1] else None
            if action == "acquire":
                if holder and holder != identity:
                    raise ValueError("ptt_floor_busy")
                connection.execute(
                    """INSERT INTO link_ptt_floor(session_id,holder_id,lease_until,updated_at)
                       VALUES (%s,%s,CURRENT_TIMESTAMP + (%s * INTERVAL '1 second'),CURRENT_TIMESTAMP)
                       ON CONFLICT(session_id) DO UPDATE SET
                         holder_id=EXCLUDED.holder_id,
                         lease_until=EXCLUDED.lease_until,
                         updated_at=CURRENT_TIMESTAMP""",
                    (session, identity, LEASE_SECONDS),
                )
                result = {"granted": True, "holder_id": identity, "lease_seconds": LEASE_SECONDS}
            else:
                if action == "release" and holder and holder != identity:
                    raise ValueError("ptt_floor_not_holder")
                # STOP is exercisable by either participant, including to end a peer's lease.
                connection.execute("DELETE FROM link_ptt_floor WHERE session_id=%s", (session,))
                result = {"granted": False, "holder_id": None, "stopped": action == "stop"}
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
                """SELECT holder_id FROM link_ptt_floor
                   WHERE session_id=%s AND lease_until>CURRENT_TIMESTAMP""",
                (session,),
            ).fetchone()
    except (ValueError, link_call_audit.LinkCallAuditUnavailable):
        raise
    except Exception as exc:
        raise LinkPttFloorUnavailable("ptt_floor_read_failed") from exc
    return {"holder_id": str(row[0]) if row else None, "lease_seconds": LEASE_SECONDS}
