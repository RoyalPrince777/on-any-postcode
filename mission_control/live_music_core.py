"""First-party OAP Live Music session body.

Live Music binds sessions to canonical OAP Music releases and the shared
Universal Player. Sessions are created fail-closed and STOPPED by default.
This module does not access microphones/cameras, deliver media, or claim a live
broadcast without a separately proven runtime and rights/entitlement path.
"""
from __future__ import annotations

from collections.abc import Mapping
from uuid import UUID

from . import entertainment_catalogue, postgres_db

LIVE_MUSIC_MIGRATION_VERSION = "0010_oap_live_music"
SESSION_STATES = frozenset({"DRAFT", "READY_FOR_REVIEW", "STOPPED", "ARCHIVED"})
MAX_TEXT = 240

SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_live_music_sessions (
        session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        release_id UUID NOT NULL REFERENCES oap_music_releases(release_id)
            ON DELETE RESTRICT,
        title TEXT NOT NULL,
        state TEXT NOT NULL DEFAULT 'DRAFT'
            CHECK (state IN ('DRAFT','READY_FOR_REVIEW','STOPPED','ARCHIVED')),
        stopped BOOLEAN NOT NULL DEFAULT TRUE,
        archive_master_id UUID REFERENCES oap_records_masters(master_id)
            ON DELETE SET NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE INDEX IF NOT EXISTS ix_live_music_owner_created
        ON oap_live_music_sessions(owner_identity_id,created_at DESC)""",
    """CREATE TABLE IF NOT EXISTS oap_live_music_events (
        event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        session_id UUID NOT NULL REFERENCES oap_live_music_sessions(session_id)
            ON DELETE CASCADE,
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        event_type TEXT NOT NULL CHECK (event_type IN
            ('SESSION_CREATED','STOPPED','ARCHIVED')),
        reference TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
)


def _uuid(value: object, name: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"invalid_{name}") from exc


def _text(value: object, name: str, *, optional: bool = False) -> str | None:
    if value is None and optional:
        return None
    if not isinstance(value, str):
        raise TypeError(f"invalid_{name}")
    cleaned = " ".join(value.split())
    if not cleaned or len(cleaned) > MAX_TEXT:
        raise ValueError(f"invalid_{name}")
    return cleaned


def live_contract() -> dict[str, object]:
    return {
        "organ": "OAP Live",
        "music_source": "OAP Music",
        "player": entertainment_catalogue.universal_player_contract(),
        "capabilities": (
            "session",
            "stop",
            "archive",
            "player_handoff_plan",
        ),
        "microphone_access_performed": False,
        "camera_access_performed": False,
        "broadcast_enabled": False,
        "public_streaming_enabled": False,
        "playback_enabled": False,
        "human_authority_final": True,
    }


def player_handoff_plan(
    *, session: object, music_gate: object
) -> dict[str, object]:
    session_row = session if isinstance(session, Mapping) else {}
    gate = music_gate if isinstance(music_gate, Mapping) else {}
    stopped = session_row.get("stopped") is not False
    private_ready = gate.get("private_handoff_ready") is True
    return {
        "session_id": session_row.get("session_id"),
        "private_handoff_ready": bool(private_ready and not stopped),
        "rights_chain_ready": private_ready,
        "stopped": stopped,
        "player_owner": entertainment_catalogue.PLAYER_OWNER,
        "broadcast_enabled": False,
        "public_streaming_enabled": False,
        "media_delivery_performed": False,
        "human_authority_final": True,
    }


class LiveMusicStore:
    """Durable Live Music session metadata with STOP as the default."""

    def ensure_schema(self) -> None:
        with postgres_db.connect() as connection:
            for statement in SCHEMA_STATEMENTS:
                connection.execute(statement)
            connection.commit()

    def create_session(
        self, *, owner_identity_id: object, release_id: object, title: object
    ) -> dict[str, object]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        release = _uuid(release_id, "release_id")
        session_title = _text(title, "title")
        with postgres_db.connect() as connection:
            owned = connection.execute(
                """SELECT 1 FROM oap_music_releases
                   WHERE release_id=%s AND owner_identity_id=%s FOR UPDATE""",
                (release, owner),
            ).fetchone()
            if owned is None:
                raise PermissionError("live_music_release_not_owned")
            row = connection.execute(
                """INSERT INTO oap_live_music_sessions(
                   owner_identity_id,release_id,title,state,stopped)
                   VALUES (%s,%s,%s,'DRAFT',TRUE)
                   RETURNING session_id,state,stopped""",
                (owner, release, session_title),
            ).fetchone()
            connection.execute(
                """INSERT INTO oap_live_music_events(
                   session_id,owner_identity_id,event_type)
                   VALUES (%s,%s,'SESSION_CREATED')""",
                (str(row[0]), owner),
            )
            connection.commit()
        return {
            "session_id": str(row[0]),
            "release_id": release,
            "title": session_title,
            "state": str(row[1]),
            "stopped": bool(row[2]),
            "broadcast_enabled": False,
        }

    def stop_session(
        self, *, owner_identity_id: object, session_id: object, reference: object = None
    ) -> dict[str, object]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        session = _uuid(session_id, "session_id")
        ref = _text(reference, "reference", optional=True)
        with postgres_db.connect() as connection:
            row = connection.execute(
                """UPDATE oap_live_music_sessions
                   SET stopped=TRUE,state='STOPPED',updated_at=CURRENT_TIMESTAMP
                   WHERE session_id=%s AND owner_identity_id=%s
                   RETURNING release_id""",
                (session, owner),
            ).fetchone()
            if row is None:
                raise PermissionError("live_music_session_not_owned")
            connection.execute(
                """INSERT INTO oap_live_music_events(
                   session_id,owner_identity_id,event_type,reference)
                   VALUES (%s,%s,'STOPPED',%s)""",
                (session, owner, ref),
            )
            connection.commit()
        return {
            "session_id": session,
            "release_id": str(row[0]),
            "stopped": True,
            "broadcast_enabled": False,
            "player_handoff_allowed": False,
        }

    def archive_session(
        self, *, owner_identity_id: object, session_id: object, master_id: object
    ) -> dict[str, object]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        session = _uuid(session_id, "session_id")
        master = _uuid(master_id, "master_id")
        with postgres_db.connect() as connection:
            row = connection.execute(
                """UPDATE oap_live_music_sessions s
                   SET archive_master_id=%s,state='ARCHIVED',stopped=TRUE,
                       updated_at=CURRENT_TIMESTAMP
                   FROM oap_records_masters m
                   WHERE s.session_id=%s AND s.owner_identity_id=%s
                     AND m.master_id=%s AND m.owner_identity_id=%s
                     AND m.release_id=s.release_id
                   RETURNING s.release_id""",
                (master, session, owner, master, owner),
            ).fetchone()
            if row is None:
                raise PermissionError("live_music_archive_not_owned")
            connection.execute(
                """INSERT INTO oap_live_music_events(
                   session_id,owner_identity_id,event_type,reference)
                   VALUES (%s,%s,'ARCHIVED',%s)""",
                (session, owner, master),
            )
            connection.commit()
        return {
            "session_id": session,
            "release_id": str(row[0]),
            "archive_master_id": master,
            "state": "ARCHIVED",
            "stopped": True,
            "broadcast_enabled": False,
        }

    def dashboard(self, *, owner_identity_id: object) -> dict[str, object]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        with postgres_db.connect(readonly=True) as connection:
            sessions = connection.execute(
                """SELECT session_id,release_id,title,state,stopped,archive_master_id
                   FROM oap_live_music_sessions
                   WHERE owner_identity_id=%s
                   ORDER BY created_at DESC LIMIT 200""",
                (owner,),
            ).fetchall()
            events = connection.execute(
                """SELECT event_id,session_id,event_type,reference,created_at
                   FROM oap_live_music_events
                   WHERE owner_identity_id=%s
                   ORDER BY created_at DESC LIMIT 500""",
                (owner,),
            ).fetchall()
        return {
            "organ": "OAP Live",
            "sessions": [
                {
                    "session_id": str(r[0]), "release_id": str(r[1]),
                    "title": str(r[2]), "state": str(r[3]), "stopped": bool(r[4]),
                    "archive_master_id": str(r[5]) if r[5] else None,
                    "broadcast_live": False,
                }
                for r in sessions
            ],
            "events": [
                {
                    "event_id": str(r[0]), "session_id": str(r[1]),
                    "event_type": str(r[2]), "reference": r[3],
                    "created_at": r[4].isoformat(),
                    "proves_broadcast": False,
                }
                for r in events
            ],
            "player": entertainment_catalogue.universal_player_contract(),
            "broadcast_enabled": False,
            "public_streaming_enabled": False,
            "human_authority_final": True,
        }
