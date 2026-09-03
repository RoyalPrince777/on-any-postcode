"""Bounded metadata-only audit for OAP Link Call and Face Up sessions.

The audit records session state and participants only. It never stores audio,
video, SDP, ICE candidates, transcripts, device fingerprints or call content.
Schema activation and retention remain explicit and fail closed.
"""
from __future__ import annotations

import os
import uuid
from typing import Any

from . import link_relationships, linkup_safety, postgres_db

SCHEMA_VERSION = "link_call_audit_v1"
MIN_RETENTION_DAYS = 1
MAX_RETENTION_DAYS = 90
ALLOWED_MODES = frozenset({"call", "face_up"})
FINAL_OUTCOMES = frozenset({"completed", "cancelled", "declined", "failed"})

SCHEMA_SQL = (
    """CREATE TABLE IF NOT EXISTS link_call_sessions (
        session_id UUID PRIMARY KEY,
        initiator_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        recipient_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        mode TEXT NOT NULL CHECK (mode IN ('call','face_up')),
        state TEXT NOT NULL DEFAULT 'ringing'
            CHECK (state IN ('ringing','active','ended')),
        outcome TEXT CHECK (outcome IN ('completed','cancelled','declined','failed')),
        started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        answered_at TIMESTAMPTZ,
        ended_at TIMESTAMPTZ,
        expires_at TIMESTAMPTZ NOT NULL,
        CHECK (initiator_id <> recipient_id),
        CHECK (answered_at IS NULL OR answered_at >= started_at),
        CHECK (ended_at IS NULL OR ended_at >= started_at),
        CHECK ((state = 'ended') = (ended_at IS NOT NULL)),
        CHECK ((state = 'ended') = (outcome IS NOT NULL)))""",
    """CREATE INDEX IF NOT EXISTS idx_link_call_sessions_recipient_state
        ON link_call_sessions(recipient_id,state,started_at DESC)""",
    """CREATE INDEX IF NOT EXISTS idx_link_call_sessions_initiator_state
        ON link_call_sessions(initiator_id,state,started_at DESC)""",
    "CREATE INDEX IF NOT EXISTS idx_link_call_sessions_expiry ON link_call_sessions(expires_at)",
)


class LinkCallAuditUnavailable(RuntimeError):
    pass


def _uuid(value: object, code: str) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(code) from exc


def _mode(value: object) -> str:
    mode = str(value or "").strip().casefold()
    if mode not in ALLOWED_MODES:
        raise ValueError("invalid_call_mode")
    return mode


def retention_days() -> int | None:
    raw = os.environ.get("OAP_LINK_CALL_AUDIT_RETENTION_DAYS", "").strip()
    if not raw:
        return None
    try:
        value = int(raw)
    except ValueError:
        return None
    if not MIN_RETENTION_DAYS <= value <= MAX_RETENTION_DAYS:
        return None
    return value


def _table_ready() -> bool:
    if not postgres_db.configured():
        return False
    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT 1 FROM information_schema.tables
                   WHERE table_schema='public' AND table_name='link_call_sessions'"""
            ).fetchone()
    except Exception:  # noqa: BLE001 - readiness must fail closed.
        return False
    return row is not None


def status() -> dict[str, Any]:
    retention = retention_days()
    schema_ready = _table_ready()
    return {
        "configured": postgres_db.configured(),
        "schema_ready": schema_ready,
        "retention_configured": retention is not None,
        "retention_days": retention,
        "records_media": False,
        "ready": schema_ready and retention is not None,
    }


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
        raise LinkCallAuditUnavailable("link_call_audit_schema_failed") from exc
    return {"version": SCHEMA_VERSION, "applied": True}


def _relationship_guard(first: str, second: str) -> None:
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
        raise LinkCallAuditUnavailable("link_call_relationship_guard_unavailable") from exc


def _require_ready() -> int:
    state = status()
    if not state["ready"] or state["retention_days"] is None:
        raise LinkCallAuditUnavailable("link_call_audit_unavailable")
    return int(state["retention_days"])


def start_session(initiator_id: object, recipient_id: object, *, mode: object) -> str:
    initiator = _uuid(initiator_id, "invalid_initiator")
    recipient = _uuid(recipient_id, "invalid_recipient")
    if initiator == recipient:
        raise ValueError("cannot_call_self")
    call_mode = _mode(mode)
    _relationship_guard(initiator, recipient)
    retention = _require_ready()
    session_id = str(uuid.uuid4())
    try:
        with postgres_db.connect() as connection:
            connection.execute(
                "DELETE FROM link_call_sessions WHERE expires_at<=CURRENT_TIMESTAMP"
            )
            existing = connection.execute(
                """SELECT 1 FROM link_call_sessions
                   WHERE state IN ('ringing','active')
                     AND LEAST(initiator_id,recipient_id)=LEAST(%s::uuid,%s::uuid)
                     AND GREATEST(initiator_id,recipient_id)=GREATEST(%s::uuid,%s::uuid)
                   LIMIT 1""",
                (initiator, recipient, initiator, recipient),
            ).fetchone()
            if existing:
                raise ValueError("active_call_exists")
            connection.execute(
                """INSERT INTO link_call_sessions(
                       session_id,initiator_id,recipient_id,mode,expires_at)
                   VALUES (%s,%s,%s,%s,CURRENT_TIMESTAMP + (%s * INTERVAL '1 day'))""",
                (session_id, initiator, recipient, call_mode, retention),
            )
            connection.commit()
    except ValueError:
        raise
    except Exception as exc:
        raise LinkCallAuditUnavailable("link_call_start_failed") from exc
    return session_id


def answer_session(identity_id: object, session_id: object) -> bool:
    identity = _uuid(identity_id, "invalid_identity")
    session = _uuid(session_id, "invalid_call_session")
    _require_ready()
    try:
        with postgres_db.connect() as connection:
            pending = connection.execute(
                """SELECT initiator_id FROM link_call_sessions
                   WHERE session_id=%s AND recipient_id=%s AND state='ringing'
                     AND expires_at>CURRENT_TIMESTAMP
                   FOR UPDATE""",
                (session, identity),
            ).fetchone()
            if pending is None:
                connection.commit()
                return False
            _relationship_guard(identity, str(pending[0]))
            row = connection.execute(
                """UPDATE link_call_sessions
                   SET state='active',answered_at=CURRENT_TIMESTAMP
                   WHERE session_id=%s AND recipient_id=%s AND state='ringing'
                     AND expires_at>CURRENT_TIMESTAMP
                   RETURNING session_id""",
                (session, identity),
            ).fetchone()
            connection.commit()
    except ValueError:
        raise
    except Exception as exc:
        raise LinkCallAuditUnavailable("link_call_answer_failed") from exc
    return row is not None


def finish_session(identity_id: object, session_id: object, *, outcome: object) -> bool:
    identity = _uuid(identity_id, "invalid_identity")
    session = _uuid(session_id, "invalid_call_session")
    result = str(outcome or "").strip().casefold()
    if result not in FINAL_OUTCOMES:
        raise ValueError("invalid_call_outcome")
    _require_ready()
    try:
        with postgres_db.connect() as connection:
            row = connection.execute(
                """SELECT initiator_id,recipient_id,state FROM link_call_sessions
                   WHERE session_id=%s AND state IN ('ringing','active')
                     AND expires_at>CURRENT_TIMESTAMP
                   FOR UPDATE""",
                (session,),
            ).fetchone()
            if row is None:
                connection.commit()
                return False
            initiator, recipient, state = str(row[0]), str(row[1]), str(row[2])
            if identity not in {initiator, recipient}:
                connection.commit()
                return False
            if state == "ringing":
                if result == "cancelled" and identity != initiator:
                    raise ValueError("invalid_call_outcome")
                if result == "declined" and identity != recipient:
                    raise ValueError("invalid_call_outcome")
                if result not in {"cancelled", "declined", "failed"}:
                    raise ValueError("invalid_call_outcome")
            elif result not in {"completed", "failed"}:
                raise ValueError("invalid_call_outcome")
            connection.execute(
                """UPDATE link_call_sessions
                   SET state='ended',outcome=%s,ended_at=CURRENT_TIMESTAMP
                   WHERE session_id=%s""",
                (result, session),
            )
            connection.commit()
    except ValueError:
        raise
    except Exception as exc:
        raise LinkCallAuditUnavailable("link_call_finish_failed") from exc
    return True


def session_allows_signalling(
    first_id: object, second_id: object, session_id: object
) -> bool:
    first = _uuid(first_id, "invalid_identity")
    second = _uuid(second_id, "invalid_identity")
    session = _uuid(session_id, "invalid_call_session")
    if first == second:
        return False
    _require_ready()
    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT 1 FROM link_call_sessions
                   WHERE session_id=%s AND state IN ('ringing','active')
                     AND expires_at>CURRENT_TIMESTAMP
                     AND LEAST(initiator_id,recipient_id)=LEAST(%s::uuid,%s::uuid)
                     AND GREATEST(initiator_id,recipient_id)=GREATEST(%s::uuid,%s::uuid)
                   LIMIT 1""",
                (session, first, second, first, second),
            ).fetchone()
    except Exception as exc:
        raise LinkCallAuditUnavailable("link_call_session_check_failed") from exc
    return row is not None


def identity_allows_signalling(identity_id: object, session_id: object) -> bool:
    identity = _uuid(identity_id, "invalid_identity")
    session = _uuid(session_id, "invalid_call_session")
    _require_ready()
    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT 1 FROM link_call_sessions
                   WHERE session_id=%s AND state IN ('ringing','active')
                     AND expires_at>CURRENT_TIMESTAMP
                     AND (initiator_id=%s OR recipient_id=%s)
                   LIMIT 1""",
                (session, identity, identity),
            ).fetchone()
    except Exception as exc:
        raise LinkCallAuditUnavailable("link_call_session_check_failed") from exc
    return row is not None


def purge_expired() -> int:
    try:
        with postgres_db.connect() as connection:
            result = connection.execute(
                "DELETE FROM link_call_sessions WHERE expires_at<=CURRENT_TIMESTAMP"
            )
            removed = int(result.rowcount or 0)
            connection.commit()
    except Exception as exc:
        raise LinkCallAuditUnavailable("link_call_audit_purge_failed") from exc
    return removed
