"""Durable first-party OAP Radio layered on OAP Music and the Universal Player.

Radio owns station/show/schedule/rotation metadata and STOP state only. It never
creates a second media player, grants music rights, fetches audio, starts a
broadcast or claims that a queued track actually aired.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from uuid import UUID

from . import entertainment_catalogue, postgres_db

RADIO_MIGRATION_VERSION = "0008_oap_radio_core"
STATION_STATES = frozenset({"DRAFT", "REVIEW_REQUIRED", "ACTIVE", "ARCHIVED"})
SHOW_STATES = frozenset({"DRAFT", "SCHEDULED", "ACTIVE", "ARCHIVED"})
MAX_TEXT = 180
_SLUG = re.compile(r"^[a-z0-9](?:[a-z0-9-]{1,61}[a-z0-9])?$")

SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_radio_stations (
        station_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        name TEXT NOT NULL,
        slug TEXT NOT NULL,
        state TEXT NOT NULL DEFAULT 'DRAFT'
            CHECK (state IN ('DRAFT','REVIEW_REQUIRED','ACTIVE','ARCHIVED')),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(owner_identity_id,slug)
    )""",
    """CREATE INDEX IF NOT EXISTS ix_radio_station_owner_created
        ON oap_radio_stations(owner_identity_id,created_at DESC)""",
    """CREATE TABLE IF NOT EXISTS oap_radio_station_control (
        station_id UUID PRIMARY KEY REFERENCES oap_radio_stations(station_id)
            ON DELETE CASCADE,
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        stopped BOOLEAN NOT NULL DEFAULT TRUE,
        stop_reason TEXT,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS oap_radio_shows (
        show_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        station_id UUID NOT NULL REFERENCES oap_radio_stations(station_id)
            ON DELETE CASCADE,
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        title TEXT NOT NULL,
        state TEXT NOT NULL DEFAULT 'DRAFT'
            CHECK (state IN ('DRAFT','SCHEDULED','ACTIVE','ARCHIVED')),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS oap_radio_schedule (
        schedule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        station_id UUID NOT NULL REFERENCES oap_radio_stations(station_id)
            ON DELETE CASCADE,
        show_id UUID NOT NULL REFERENCES oap_radio_shows(show_id)
            ON DELETE CASCADE,
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        starts_at TIMESTAMPTZ NOT NULL,
        ends_at TIMESTAMPTZ NOT NULL CHECK (ends_at > starts_at),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE INDEX IF NOT EXISTS ix_radio_schedule_station_start
        ON oap_radio_schedule(station_id,starts_at)""",
    """CREATE TABLE IF NOT EXISTS oap_radio_rotation (
        rotation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        station_id UUID NOT NULL REFERENCES oap_radio_stations(station_id)
            ON DELETE CASCADE,
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        track_id UUID NOT NULL REFERENCES oap_music_tracks(track_id)
            ON DELETE RESTRICT,
        position INTEGER NOT NULL CHECK (position > 0),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(station_id,position),
        UNIQUE(station_id,track_id)
    )""",
    """CREATE TABLE IF NOT EXISTS oap_radio_activity_events (
        event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        station_id UUID NOT NULL REFERENCES oap_radio_stations(station_id)
            ON DELETE CASCADE,
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        event_type TEXT NOT NULL CHECK (event_type IN ('ROTATION_QUEUED','STOPPED')),
        track_id UUID REFERENCES oap_music_tracks(track_id) ON DELETE RESTRICT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE INDEX IF NOT EXISTS ix_radio_activity_station_created
        ON oap_radio_activity_events(station_id,created_at DESC)""",
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


def _slug(value: object) -> str:
    if not isinstance(value, str) or not _SLUG.fullmatch(value):
        raise ValueError("invalid_slug")
    return value


def station_projection(record: object) -> dict[str, object] | None:
    """Allowlist one owner-scoped station metadata record."""
    if not isinstance(record, Mapping):
        return None
    try:
        station_id = _uuid(record.get("station_id"), "station_id")
        name = _text(record.get("name"), "name")
    except (TypeError, ValueError):
        return None
    state = record.get("state")
    if state not in STATION_STATES:
        return None
    return {
        "station_id": station_id,
        "name": name,
        "state": state,
        "stopped": bool(record.get("stopped", True)),
        "broadcast_live": False,
        "public_stream_url": None,
    }


def rotation_gate(music_item: object) -> dict[str, object]:
    """Reuse the canonical Music rights gate; caller flags cannot bypass it."""
    item = music_item if isinstance(music_item, Mapping) else {}
    rights = entertainment_catalogue.rights_gate(item)
    return {
        "rotation_eligible": bool(rights.get("allowed") is True),
        "rights": rights,
        "player_owner": entertainment_catalogue.PLAYER_OWNER,
        "audio_fetch_performed": False,
        "broadcast_started": False,
        "external_distribution_performed": False,
        "human_authority_final": True,
    }


def radio_contract() -> dict[str, object]:
    """Describe the bounded first-party Radio organ and one shared player."""
    return {
        "organ": "OAP Radio",
        "owner": "OAP",
        "mode": "first_party_fail_closed",
        "capabilities": (
            "stations",
            "shows",
            "schedule",
            "rotation",
            "activity_history",
            "stop",
        ),
        "music_source": "OAP Music",
        "player": entertainment_catalogue.universal_player_contract(),
        "dedicated_media_player_created": False,
        "broadcast_enabled": False,
        "public_streaming_enabled": False,
        "external_distribution_enabled": False,
        "rights_verified_by_radio": False,
        "human_authority_final": True,
    }


class RadioStore:
    """Durable owner-scoped Radio metadata store; never executes a broadcast."""

    def ensure_schema(self) -> None:
        with postgres_db.connect() as connection:
            for statement in SCHEMA_STATEMENTS:
                connection.execute(statement)
            connection.commit()

    def create_station(
        self, *, owner_identity_id: object, name: object, slug: object
    ) -> dict[str, object]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        station_name = _text(name, "name")
        station_slug = _slug(slug)
        with postgres_db.connect() as connection:
            row = connection.execute(
                """INSERT INTO oap_radio_stations(owner_identity_id,name,slug)
                   VALUES (%s,%s,%s)
                   RETURNING station_id,name,slug,state""",
                (owner, station_name, station_slug),
            ).fetchone()
            connection.execute(
                """INSERT INTO oap_radio_station_control(
                   station_id,owner_identity_id,stopped,stop_reason)
                   VALUES (%s,%s,TRUE,'initial_fail_closed')""",
                (str(row[0]), owner),
            )
            connection.commit()
        return {
            "station_id": str(row[0]),
            "name": str(row[1]),
            "slug": str(row[2]),
            "state": str(row[3]),
            "stopped": True,
            "broadcast_started": False,
        }

    def create_show(
        self, *, owner_identity_id: object, station_id: object, title: object
    ) -> dict[str, object]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        station = _uuid(station_id, "station_id")
        show_title = _text(title, "title")
        with postgres_db.connect() as connection:
            owned = connection.execute(
                """SELECT 1 FROM oap_radio_stations
                   WHERE station_id=%s AND owner_identity_id=%s FOR UPDATE""",
                (station, owner),
            ).fetchone()
            if owned is None:
                raise PermissionError("radio_station_not_owned")
            row = connection.execute(
                """INSERT INTO oap_radio_shows(station_id,owner_identity_id,title)
                   VALUES (%s,%s,%s) RETURNING show_id,title,state""",
                (station, owner, show_title),
            ).fetchone()
            connection.commit()
        return {
            "show_id": str(row[0]),
            "station_id": station,
            "title": str(row[1]),
            "state": str(row[2]),
        }

    def schedule_show(
        self, *, owner_identity_id: object, station_id: object, show_id: object,
        starts_at: object, ends_at: object,
    ) -> dict[str, object]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        station = _uuid(station_id, "station_id")
        show = _uuid(show_id, "show_id")
        if not isinstance(starts_at, str) or not isinstance(ends_at, str):
            raise TypeError("invalid_schedule_time")
        with postgres_db.connect() as connection:
            row = connection.execute(
                """INSERT INTO oap_radio_schedule(
                   station_id,show_id,owner_identity_id,starts_at,ends_at)
                   SELECT s.station_id,sh.show_id,%s,%s::timestamptz,%s::timestamptz
                   FROM oap_radio_stations s
                   JOIN oap_radio_shows sh ON sh.station_id=s.station_id
                   WHERE s.station_id=%s AND s.owner_identity_id=%s
                     AND sh.show_id=%s AND sh.owner_identity_id=%s
                   RETURNING schedule_id,starts_at,ends_at""",
                (owner, starts_at, ends_at, station, owner, show, owner),
            ).fetchone()
            if row is None:
                raise PermissionError("radio_show_not_owned")
            connection.commit()
        return {
            "schedule_id": str(row[0]),
            "station_id": station,
            "show_id": show,
            "starts_at": row[1].isoformat(),
            "ends_at": row[2].isoformat(),
            "broadcast_started": False,
        }

    def add_rotation(
        self, *, owner_identity_id: object, station_id: object,
        track_id: object, position: object,
    ) -> dict[str, object]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        station = _uuid(station_id, "station_id")
        track = _uuid(track_id, "track_id")
        if type(position) is not int or position <= 0:
            raise ValueError("invalid_position")
        with postgres_db.connect() as connection:
            owned = connection.execute(
                """SELECT 1
                   FROM oap_radio_stations s
                   JOIN oap_music_tracks t ON t.track_id=%s
                   JOIN oap_music_releases r ON r.release_id=t.release_id
                   WHERE s.station_id=%s AND s.owner_identity_id=%s
                     AND r.owner_identity_id=%s FOR UPDATE OF s""",
                (track, station, owner, owner),
            ).fetchone()
            if owned is None:
                raise PermissionError("radio_station_or_track_not_owned")
            row = connection.execute(
                """INSERT INTO oap_radio_rotation(
                   station_id,owner_identity_id,track_id,position)
                   VALUES (%s,%s,%s,%s)
                   RETURNING rotation_id""",
                (station, owner, track, position),
            ).fetchone()
            connection.execute(
                """INSERT INTO oap_radio_activity_events(
                   station_id,owner_identity_id,event_type,track_id)
                   VALUES (%s,%s,'ROTATION_QUEUED',%s)""",
                (station, owner, track),
            )
            connection.commit()
        return {
            "rotation_id": str(row[0]),
            "station_id": station,
            "track_id": track,
            "position": position,
            "queued_only": True,
            "aired": False,
            "broadcast_started": False,
        }

    def stop_station(
        self, *, owner_identity_id: object, station_id: object, reason: object = None
    ) -> dict[str, object]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        station = _uuid(station_id, "station_id")
        stop_reason = _text(reason, "reason", optional=True)
        with postgres_db.connect() as connection:
            row = connection.execute(
                """UPDATE oap_radio_station_control
                   SET stopped=TRUE,stop_reason=%s,updated_at=CURRENT_TIMESTAMP
                   WHERE station_id=%s AND owner_identity_id=%s
                   RETURNING station_id""",
                (stop_reason, station, owner),
            ).fetchone()
            if row is None:
                raise PermissionError("radio_station_not_owned")
            connection.execute(
                """INSERT INTO oap_radio_activity_events(
                   station_id,owner_identity_id,event_type)
                   VALUES (%s,%s,'STOPPED')""",
                (station, owner),
            )
            connection.commit()
        return {
            "station_id": station,
            "stopped": True,
            "broadcast_enabled": False,
            "player_handoff_allowed": False,
        }

    def dashboard(self, *, owner_identity_id: object) -> dict[str, object]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        with postgres_db.connect(readonly=True) as connection:
            stations = connection.execute(
                """SELECT s.station_id,s.name,s.slug,s.state,c.stopped
                   FROM oap_radio_stations s
                   JOIN oap_radio_station_control c ON c.station_id=s.station_id
                   WHERE s.owner_identity_id=%s
                   ORDER BY s.created_at DESC LIMIT 100""",
                (owner,),
            ).fetchall()
            shows = connection.execute(
                """SELECT show_id,station_id,title,state
                   FROM oap_radio_shows
                   WHERE owner_identity_id=%s
                   ORDER BY created_at DESC LIMIT 200""",
                (owner,),
            ).fetchall()
            schedule = connection.execute(
                """SELECT schedule_id,station_id,show_id,starts_at,ends_at
                   FROM oap_radio_schedule
                   WHERE owner_identity_id=%s
                   ORDER BY starts_at LIMIT 200""",
                (owner,),
            ).fetchall()
            rotation = connection.execute(
                """SELECT rotation_id,station_id,track_id,position
                   FROM oap_radio_rotation
                   WHERE owner_identity_id=%s
                   ORDER BY station_id,position LIMIT 500""",
                (owner,),
            ).fetchall()
            history = connection.execute(
                """SELECT event_id,station_id,event_type,track_id,created_at
                   FROM oap_radio_activity_events
                   WHERE owner_identity_id=%s
                   ORDER BY created_at DESC LIMIT 200""",
                (owner,),
            ).fetchall()
        return {
            "organ": "OAP Radio",
            "stations": [
                {
                    "station_id": str(r[0]), "name": str(r[1]), "slug": str(r[2]),
                    "state": str(r[3]), "stopped": bool(r[4]),
                    "broadcast_live": False,
                }
                for r in stations
            ],
            "shows": [
                {
                    "show_id": str(r[0]), "station_id": str(r[1]),
                    "title": str(r[2]), "state": str(r[3]),
                }
                for r in shows
            ],
            "schedule": [
                {
                    "schedule_id": str(r[0]), "station_id": str(r[1]),
                    "show_id": str(r[2]), "starts_at": r[3].isoformat(),
                    "ends_at": r[4].isoformat(),
                }
                for r in schedule
            ],
            "rotation": [
                {
                    "rotation_id": str(r[0]), "station_id": str(r[1]),
                    "track_id": str(r[2]), "position": int(r[3]),
                    "queued_only": True, "aired": False,
                }
                for r in rotation
            ],
            "activity_history": [
                {
                    "event_id": str(r[0]), "station_id": str(r[1]),
                    "event_type": str(r[2]),
                    "track_id": str(r[3]) if r[3] is not None else None,
                    "created_at": r[4].isoformat(),
                    "proves_airplay": False,
                }
                for r in history
            ],
            "now_playing": None,
            "now_playing_confirmed": False,
            "broadcast_enabled": False,
            "public_streaming_enabled": False,
            "player": entertainment_catalogue.universal_player_contract(),
            "human_authority_final": True,
        }
