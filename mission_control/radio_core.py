"""Durable first-party OAP Radio layered on OAP Music and the Universal Player.

Radio owns station/show/schedule/rotation metadata and STOP state only. It never
creates a second media player, grants music rights, fetches audio, starts a
broadcast or claims that a queued track actually aired.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from uuid import UUID, uuid4

from . import entertainment_catalogue, postgres_db

RADIO_MIGRATION_VERSION = "0008_oap_radio_core"
RADIO_ALWAYS_ON_MIGRATION_VERSION = "0016_oap_radio_always_on"
RADIO_FOUNDER_APPROVAL_MIGRATION_VERSION = "0021_oap_radio_founder_approval"
RADIO_DELIVERY_ADMISSION_MIGRATION_VERSION = "0023_oap_radio_delivery_admission"
RADIO_DELIVERY_ADMISSION_SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_radio_delivery_admissions (
        receipt_id UUID PRIMARY KEY,
        station_id UUID NOT NULL REFERENCES oap_radio_stations(station_id)
            ON DELETE RESTRICT,
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        track_id UUID NOT NULL REFERENCES oap_music_tracks(track_id)
            ON DELETE RESTRICT,
        asset_id UUID NOT NULL REFERENCES oap_music_assets(asset_id)
            ON DELETE RESTRICT,
        entitlement_id UUID NOT NULL REFERENCES oap_music_entitlements(entitlement_id)
            ON DELETE RESTRICT,
        rights_decision_hash CHAR(64) NOT NULL,
        media_sha256 CHAR(64) NOT NULL,
        prepared_bytes INTEGER NOT NULL CHECK (prepared_bytes > 0),
        response_status INTEGER NOT NULL CHECK (response_status IN (200,206)),
        receipt_type TEXT NOT NULL DEFAULT 'RESPONSE_PREPARED'
            CHECK (receipt_type='RESPONSE_PREPARED'),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE INDEX IF NOT EXISTS ix_radio_delivery_station_created
       ON oap_radio_delivery_admissions(station_id,created_at DESC)""",
)
RADIO_FOUNDER_APPROVAL_SCHEMA_STATEMENTS = (
    """ALTER TABLE oap_radio_stations
       ADD COLUMN IF NOT EXISTS founder_approved BOOLEAN NOT NULL DEFAULT FALSE""",
    """ALTER TABLE oap_radio_stations
       ADD COLUMN IF NOT EXISTS founder_approved_at TIMESTAMPTZ""",
    """ALTER TABLE oap_radio_shows
       ADD COLUMN IF NOT EXISTS founder_approved BOOLEAN NOT NULL DEFAULT FALSE""",
    """ALTER TABLE oap_radio_shows
       ADD COLUMN IF NOT EXISTS founder_approved_at TIMESTAMPTZ""",
)

RADIO_ALWAYS_ON_SCHEMA_STATEMENTS = (
    """ALTER TABLE oap_radio_station_control
       ADD COLUMN IF NOT EXISTS always_on BOOLEAN NOT NULL DEFAULT FALSE""",
    """ALTER TABLE oap_radio_station_control
       ADD COLUMN IF NOT EXISTS auto_add_approved BOOLEAN NOT NULL DEFAULT TRUE""",
)
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

    def approve_station(
        self, *, founder_identity_id: object, station_id: object
    ) -> dict[str, object]:
        founder = _uuid(founder_identity_id, "founder_identity_id")
        station = _uuid(station_id, "station_id")
        with postgres_db.connect() as connection:
            row = connection.execute(
                """UPDATE oap_radio_stations
                   SET founder_approved=TRUE,
                       founder_approved_at=CURRENT_TIMESTAMP,
                       state=CASE WHEN state IN ('DRAFT','REVIEW_REQUIRED') THEN 'ACTIVE' ELSE state END,
                       updated_at=CURRENT_TIMESTAMP
                   WHERE station_id=%s AND owner_identity_id=%s
                     AND state IN ('DRAFT','REVIEW_REQUIRED','ACTIVE')
                   RETURNING station_id,state,founder_approved,founder_approved_at""",
                (station, founder),
            ).fetchone()
            if row is None:
                raise PermissionError("radio_station_not_owned")
            connection.commit()
        return {
            "station_id": str(row[0]),
            "state": str(row[1]),
            "founder_approved": bool(row[2]),
            "founder_approved_at": row[3].isoformat() if row[3] else None,
            "broadcast_started": False,
            "human_authority_final": True,
        }

    def approve_show(
        self, *, founder_identity_id: object, station_id: object, show_id: object
    ) -> dict[str, object]:
        founder = _uuid(founder_identity_id, "founder_identity_id")
        station = _uuid(station_id, "station_id")
        show = _uuid(show_id, "show_id")
        with postgres_db.connect() as connection:
            row = connection.execute(
                """UPDATE oap_radio_shows sh
                   SET founder_approved=TRUE,
                       founder_approved_at=CURRENT_TIMESTAMP
                   FROM oap_radio_stations s
                   WHERE sh.show_id=%s AND sh.station_id=%s
                     AND s.station_id=sh.station_id
                     AND s.owner_identity_id=%s
                     AND s.founder_approved=TRUE AND s.state='ACTIVE'
                     AND sh.state<>'ARCHIVED'
                   RETURNING sh.show_id,sh.state,sh.founder_approved,sh.founder_approved_at""",
                (show, station, founder),
            ).fetchone()
            if row is None:
                raise PermissionError("radio_station_or_show_not_approved_for_founder")
            connection.commit()
        return {
            "show_id": str(row[0]),
            "station_id": station,
            "state": str(row[1]),
            "founder_approved": bool(row[2]),
            "founder_approved_at": row[3].isoformat() if row[3] else None,
            "broadcast_started": False,
            "human_authority_final": True,
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
                     AND s.founder_approved=TRUE AND s.state='ACTIVE'
                     AND sh.show_id=%s AND sh.owner_identity_id=%s
                     AND sh.founder_approved=TRUE AND sh.state<>'ARCHIVED'
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

    def set_always_on(
        self,
        *,
        owner_identity_id: object,
        station_id: object,
        enabled: bool,
        auto_add_approved: bool = True,
    ) -> dict[str, object]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        station = _uuid(station_id, "station_id")
        with postgres_db.connect() as connection:
            row = connection.execute(
                """UPDATE oap_radio_station_control
                   SET always_on=%s,
                       auto_add_approved=%s,
                       stopped=CASE WHEN %s THEN FALSE ELSE stopped END,
                       stop_reason=CASE WHEN %s THEN NULL ELSE stop_reason END,
                       updated_at=CURRENT_TIMESTAMP
                   WHERE station_id=%s AND owner_identity_id=%s
                     AND EXISTS (
                       SELECT 1 FROM oap_radio_stations s
                       WHERE s.station_id=oap_radio_station_control.station_id
                         AND s.owner_identity_id=oap_radio_station_control.owner_identity_id
                         AND s.founder_approved=TRUE
                         AND s.state='ACTIVE'
                     )
                   RETURNING station_id,always_on,auto_add_approved,stopped""",
                (
                    bool(enabled),
                    bool(auto_add_approved),
                    bool(enabled),
                    bool(enabled),
                    station,
                    owner,
                ),
            ).fetchone()
            if row is None:
                raise PermissionError("radio_station_not_owned")
            connection.commit()
        return {
            "station_id": str(row[0]),
            "always_on": bool(row[1]),
            "auto_add_approved": bool(row[2]),
            "stopped": bool(row[3]),
            "operating_mode": "ALWAYS_ON" if bool(row[1]) else "MANUAL",
            "background_daemon_claimed": False,
            "public_broadcast_claimed": False,
            "human_authority_final": True,
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

    def public_station_candidates(self) -> list[dict[str, object]]:
        """List only approved, unstopped station candidates, not playable grants.

        Music's current Radio-channel rights and entitlement must be checked
        separately before exposing a media link. Never publish owner identity.
        """
        with postgres_db.connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT s.station_id,s.name,r.track_id,a.asset_id
                   FROM oap_radio_stations s
                   JOIN oap_radio_station_control c
                     ON c.station_id=s.station_id
                    AND c.owner_identity_id=s.owner_identity_id
                   JOIN LATERAL (
                     SELECT track_id
                     FROM oap_radio_rotation
                     WHERE station_id=s.station_id
                       AND owner_identity_id=s.owner_identity_id
                     ORDER BY position ASC LIMIT 1
                   ) r ON TRUE
                   JOIN oap_music_assets a ON a.track_id=r.track_id
                    AND a.owner_identity_id=s.owner_identity_id
                   WHERE s.state='ACTIVE' AND s.founder_approved=TRUE
                     AND c.stopped=FALSE AND c.always_on=TRUE
                     AND a.stopped=FALSE
                   ORDER BY s.name,s.station_id LIMIT 25"""
            ).fetchall()
        return [
            {
                "station_id": str(row[0]), "station_name": str(row[1]),
                "track_id": str(row[2]), "asset_id": str(row[3]),
                "delivery_authorized": False, "airplay_confirmed": False,
            }
            for row in rows
        ]

    def playout_candidate(
        self, *, station_id: object
    ) -> dict[str, object] | None:
        """Resolve a station-scoped candidate, never permission to deliver bytes.

        Recheck STOP, rights, entitlement and asset integrity at the eventual
        delivery boundary. A queue selection is not a broadcast or airplay.
        """
        station = _uuid(station_id, "station_id")
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT r.track_id,a.asset_id
                   FROM oap_radio_stations s
                   JOIN oap_radio_station_control c
                     ON c.station_id=s.station_id
                    AND c.owner_identity_id=s.owner_identity_id
                   JOIN oap_radio_rotation r
                     ON r.station_id=s.station_id
                    AND r.owner_identity_id=s.owner_identity_id
                   JOIN oap_music_assets a
                     ON a.track_id=r.track_id
                    AND a.owner_identity_id=s.owner_identity_id
                   WHERE s.station_id=%s AND s.state='ACTIVE'
                     AND s.founder_approved=TRUE
                     AND c.stopped=FALSE AND c.always_on=TRUE
                     AND a.stopped=FALSE
                   ORDER BY r.position ASC LIMIT 1""",
                (station,),
            ).fetchone()
        if row is None:
            return None
        return {
            "station_id": station,
            "track_id": str(row[0]),
            "asset_id": str(row[1]),
            "selection_only": True,
            "delivery_authorized": False,
            "live_rights_and_entitlement_check_required": True,
            "station_stop_recheck_required": True,
            "airplay_receipt": None,
            "broadcast_started": False,
        }

    def delivery_preflight(
        self, *, station_id: object, track_id: object, asset_id: object
    ) -> bool:
        """Fresh station/track/asset STOP gate; never a stand-alone rights grant.

        A caller must also enforce current OAP Music rights, Radio-channel
        entitlement and media integrity. This check does not create a stream
        or an airplay receipt.
        """
        station = _uuid(station_id, "station_id")
        track = _uuid(track_id, "track_id")
        asset = _uuid(asset_id, "asset_id")
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT 1 FROM oap_radio_stations s
                   JOIN oap_radio_station_control c
                     ON c.station_id=s.station_id
                    AND c.owner_identity_id=s.owner_identity_id
                   JOIN oap_radio_rotation r
                     ON r.station_id=s.station_id
                    AND r.owner_identity_id=s.owner_identity_id
                   JOIN oap_music_assets a
                     ON a.track_id=r.track_id
                    AND a.owner_identity_id=s.owner_identity_id
                   WHERE s.station_id=%s AND r.track_id=%s AND a.asset_id=%s
                     AND s.state='ACTIVE' AND s.founder_approved=TRUE
                     AND c.stopped=FALSE AND c.always_on=TRUE
                     AND a.stopped=FALSE
                   LIMIT 1""",
                (station, track, asset),
            ).fetchone()
        return row is not None

    def admit_delivery(
        self, *, station_id: object, track_id: object, asset_id: object,
        owner_identity_id: object, entitlement_id: object,
        rights_decision_hash: object, media_sha256: object,
        prepared_bytes: int, response_status: int,
    ) -> str | None:
        """Serialize response preparation with STOP and persist an honest receipt.

        This is NOT confirmation of socket delivery, listening, or broadcast.
        STOP and this gate both write-lock the same station-control row. The
        selected station, rotation, asset, entitlement and independently approved
        rights grant are share-locked through receipt commit, serializing
        changes to playout eligibility against admission.
        """
        station = _uuid(station_id, "station_id")
        track = _uuid(track_id, "track_id")
        asset = _uuid(asset_id, "asset_id")
        owner = _uuid(owner_identity_id, "owner_identity_id")
        entitlement = _uuid(entitlement_id, "entitlement_id")
        if not isinstance(rights_decision_hash, str) or not re.fullmatch(
            r"[0-9a-f]{64}", rights_decision_hash
        ):
            raise ValueError("invalid_rights_decision_hash")
        if not isinstance(media_sha256, str) or not re.fullmatch(
            r"[0-9a-f]{64}", media_sha256
        ):
            raise ValueError("invalid_media_sha256")
        if type(prepared_bytes) is not int or prepared_bytes < 1:
            raise ValueError("invalid_prepared_bytes")
        if response_status not in (200, 206):
            raise ValueError("invalid_response_status")
        receipt = str(uuid4())
        with postgres_db.connect() as connection:
            # Row locking makes STOP-before-admission deny; admission-before-STOP
            # records its receipt before STOP can commit.
            gate = connection.execute(
                """SELECT c.station_id
                   FROM oap_radio_station_control c
                   JOIN oap_radio_stations s
                     ON s.station_id=c.station_id
                    AND s.owner_identity_id=c.owner_identity_id
                   JOIN oap_radio_rotation r
                     ON r.station_id=s.station_id
                    AND r.owner_identity_id=s.owner_identity_id
                   JOIN oap_music_assets a
                     ON a.track_id=r.track_id
                    AND a.owner_identity_id=s.owner_identity_id
                   JOIN oap_music_entitlements e
                     ON e.asset_id=a.asset_id
                    AND e.owner_identity_id=s.owner_identity_id
                   JOIN oap_music_rights_grants g
                     ON g.asset_id=a.asset_id
                    AND g.owner_identity_id=s.owner_identity_id
                   WHERE c.station_id=%s AND c.owner_identity_id=%s
                     AND r.track_id=%s AND a.asset_id=%s AND e.entitlement_id=%s
                     AND s.state='ACTIVE' AND s.founder_approved=TRUE
                     AND c.stopped=FALSE AND c.always_on=TRUE
                     AND a.stopped=FALSE AND a.sha256=%s AND e.active=TRUE
                     AND e.access_scope='PUBLIC_FREE'
                     AND e.channel IN ('OAP Radio','*')
                     AND e.territory IN ('*')
                     AND (e.valid_from IS NULL OR e.valid_from<=CURRENT_TIMESTAMP)
                     AND (e.valid_until IS NULL OR e.valid_until>CURRENT_TIMESTAMP)
                     AND g.revoked=FALSE
                     AND g.authority_verified=TRUE
                     AND g.authority_receipt_hash IS NOT NULL
                     AND g.human_approved=TRUE
                     AND g.human_approval_receipt_hash IS NOT NULL
                     AND cardinality(g.evidence_hashes)>0
                     AND g.right_type IN ('recording','composition','performance','stream')
                     AND 'stream'=ANY(g.permitted_uses)
                     AND '*'=ANY(g.territories)
                     AND ('OAP Radio'=ANY(g.permitted_channels)
                          OR '*'=ANY(g.permitted_channels))
                     AND (g.valid_from IS NULL OR g.valid_from<=CURRENT_TIMESTAMP)
                     AND (g.valid_until IS NULL OR g.valid_until>CURRENT_TIMESTAMP)
                   LIMIT 1 FOR UPDATE OF c FOR SHARE OF s,r,a,e,g""",
                (station, owner, track, asset, entitlement, media_sha256),
            ).fetchone()
            if gate is None:
                return None
            connection.execute(
                """INSERT INTO oap_radio_delivery_admissions(
                   receipt_id,station_id,owner_identity_id,track_id,asset_id,
                   entitlement_id,rights_decision_hash,media_sha256,
                   prepared_bytes,response_status)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (receipt, station, owner, track, asset, entitlement,
                 rights_decision_hash, media_sha256, prepared_bytes, response_status),
            )
            connection.commit()
        return receipt

    def delivery_receipts(
        self, *, owner_identity_id: object, station_id: object
    ) -> list[dict[str, object]]:
        """Founder-only caller retrieves owner-scoped admission evidence, not airplay."""
        owner = _uuid(owner_identity_id, "owner_identity_id")
        station = _uuid(station_id, "station_id")
        with postgres_db.connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT d.receipt_id,d.track_id,d.asset_id,d.entitlement_id,
                          d.rights_decision_hash,d.media_sha256,
                          d.prepared_bytes,d.response_status,d.receipt_type,d.created_at
                   FROM oap_radio_delivery_admissions d
                   JOIN oap_radio_stations s ON s.station_id=d.station_id
                   WHERE d.station_id=%s AND d.owner_identity_id=%s
                     AND s.owner_identity_id=%s
                   ORDER BY d.created_at DESC,d.receipt_id DESC LIMIT 100""",
                (station, owner, owner),
            ).fetchall()
        return [
            {
                "receipt_id": str(r[0]),
                "station_id": station,
                "track_id": str(r[1]),
                "asset_id": str(r[2]),
                "entitlement_id": str(r[3]),
                "rights_decision_hash": str(r[4]),
                "media_sha256": str(r[5]),
                "prepared_bytes": int(r[6]),
                "response_status": int(r[7]),
                "receipt_type": str(r[8]),
                "created_at": r[9].isoformat(),
                "delivery_completed": False,
                "airplay_confirmed": False,
                "listener_completion_confirmed": False,
            }
            for r in rows
        ]

    def dashboard(self, *, owner_identity_id: object) -> dict[str, object]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        with postgres_db.connect(readonly=True) as connection:
            stations = connection.execute(
                """SELECT s.station_id,s.name,s.slug,s.state,c.stopped,
                          c.always_on,c.auto_add_approved,s.founder_approved
                   FROM oap_radio_stations s
                   JOIN oap_radio_station_control c ON c.station_id=s.station_id
                   WHERE s.owner_identity_id=%s
                   ORDER BY s.created_at DESC LIMIT 100""",
                (owner,),
            ).fetchall()
            shows = connection.execute(
                """SELECT show_id,station_id,title,state,founder_approved
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
                    "always_on": bool(r[5]),
                    "auto_add_approved": bool(r[6]),
                    "founder_approved": bool(r[7]),
                    "broadcast_live": False,
                }
                for r in stations
            ],
            "shows": [
                {
                    "show_id": str(r[0]), "station_id": str(r[1]),
                    "title": str(r[2]), "state": str(r[3]),
                    "founder_approved": bool(r[4]),
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
