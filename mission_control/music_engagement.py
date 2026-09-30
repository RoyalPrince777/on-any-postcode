"""First-party OAP Music / OAP TV qualified engagement measurement.

Stores pseudonymous listener events against the canonical content-group identity.
Artists receive aggregate metrics only; listener identity and precise location are
not exposed. This module does not create payouts or ranking authority.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from uuid import UUID, uuid4

from . import postgres_db

MUSIC_ENGAGEMENT_MIGRATION_VERSION = "0020_oap_music_engagement"
PLAYBACK_SESSION_MIGRATION_VERSION = "0022_oap_music_playback_sessions"
SURFACES = frozenset({"OAP_MUSIC", "OAP_TV", "OAP_RADIO"})
EVENT_TYPES = frozenset({"START", "HEARTBEAT", "COMPLETE"})
MIN_QUALIFIED_SECONDS = 30
ACTIVE_WINDOW_SECONDS = 90

SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_music_engagement_events (
        event_id UUID PRIMARY KEY,
        content_group_id UUID NOT NULL REFERENCES oap_music_content_groups(content_group_id)
            ON DELETE CASCADE,
        track_id UUID NOT NULL REFERENCES oap_music_tracks(track_id) ON DELETE CASCADE,
        surface TEXT NOT NULL CHECK (surface IN ('OAP_MUSIC','OAP_TV','OAP_RADIO')),
        listener_key CHAR(64) NOT NULL,
        event_type TEXT NOT NULL CHECK (event_type IN ('START','HEARTBEAT','COMPLETE')),
        playback_seconds INTEGER NOT NULL DEFAULT 0 CHECK (playback_seconds >= 0),
        duration_seconds INTEGER CHECK (duration_seconds IS NULL OR duration_seconds > 0),
        qualified BOOLEAN NOT NULL DEFAULT FALSE,
        postcode TEXT,
        borough TEXT,
        region TEXT,
        country TEXT,
        continent TEXT,
        occurred_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE INDEX IF NOT EXISTS ix_music_engagement_group_time
       ON oap_music_engagement_events(content_group_id,occurred_at DESC)""",
    """CREATE INDEX IF NOT EXISTS ix_music_engagement_listener_time
       ON oap_music_engagement_events(listener_key,occurred_at DESC)""",
)


PLAYBACK_SESSION_SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_music_playback_sessions (
        playback_session_id UUID PRIMARY KEY,
        content_group_id UUID NOT NULL REFERENCES oap_music_content_groups(content_group_id)
            ON DELETE CASCADE,
        track_id UUID NOT NULL REFERENCES oap_music_tracks(track_id) ON DELETE CASCADE,
        surface TEXT NOT NULL CHECK (surface IN ('OAP_MUSIC','OAP_TV','OAP_RADIO')),
        listener_key CHAR(64) NOT NULL,
        started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        last_seen_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMPTZ,
        max_playback_seconds INTEGER NOT NULL DEFAULT 0 CHECK (max_playback_seconds >= 0),
        canonical_duration_seconds INTEGER,
        last_sequence INTEGER NOT NULL DEFAULT 0 CHECK (last_sequence >= 0),
        qualified BOOLEAN NOT NULL DEFAULT FALSE,
        qualified_at TIMESTAMPTZ,
        postcode TEXT,
        borough TEXT,
        region TEXT,
        country TEXT,
        continent TEXT
    )""",
    """CREATE INDEX IF NOT EXISTS ix_music_playback_sessions_group_time
       ON oap_music_playback_sessions(content_group_id,started_at DESC)""",
    """CREATE INDEX IF NOT EXISTS ix_music_playback_sessions_listener_time
       ON oap_music_playback_sessions(listener_key,last_seen_at DESC)""",
    """ALTER TABLE oap_music_engagement_events
       ADD COLUMN IF NOT EXISTS playback_session_id UUID
       REFERENCES oap_music_playback_sessions(playback_session_id) ON DELETE CASCADE""",
    """ALTER TABLE oap_music_engagement_events
       ADD COLUMN IF NOT EXISTS event_sequence INTEGER""",
    """CREATE UNIQUE INDEX IF NOT EXISTS ux_music_engagement_session_sequence
       ON oap_music_engagement_events(playback_session_id,event_sequence)
       WHERE playback_session_id IS NOT NULL AND event_sequence IS NOT NULL""",
)


def _uuid(value: object, name: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"invalid_{name}") from exc


def listener_key(session_identity: object) -> str:
    raw = str(session_identity or "").strip()
    if not raw:
        raise ValueError("listener_session_required")
    return hashlib.sha256(("oap-engagement-v1:" + raw).encode()).hexdigest()


def _coarse(value: object, maximum: int) -> str | None:
    if value in (None, ""):
        return None
    text = " ".join(str(value).split())
    if not text:
        return None
    return text[:maximum]


def qualifies(*, event_type: object, playback_seconds: object, duration_seconds: object = None) -> bool:
    event = str(event_type or "").strip().upper()
    if event not in EVENT_TYPES:
        raise ValueError("invalid_engagement_event")
    try:
        played = max(0, int(playback_seconds or 0))
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid_playback_seconds") from exc
    if event == "COMPLETE":
        return True
    if played >= MIN_QUALIFIED_SECONDS:
        return True
    if duration_seconds not in (None, ""):
        try:
            duration = int(duration_seconds)
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid_duration_seconds") from exc
        if duration > 0 and played >= max(10, int(duration * 0.5)):
            return True
    return False


def record_event(
    *,
    track_id: object,
    session_identity: object,
    surface: object,
    event_type: object,
    playback_session_id: object = None,
    event_sequence: object = None,
    playback_seconds: object = 0,
    duration_seconds: object = None,
    postcode: object = None,
    borough: object = None,
    region: object = None,
    country: object = None,
    continent: object = None,
) -> dict[str, object]:
    track = _uuid(track_id, "track_id")
    surface_value = str(surface or "").strip().upper()
    if surface_value not in SURFACES:
        raise ValueError("invalid_engagement_surface")
    event_value = str(event_type or "").strip().upper()
    if event_value not in EVENT_TYPES:
        raise ValueError("invalid_engagement_event")
    try:
        played = max(0, int(playback_seconds or 0))
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid_playback_seconds") from exc
    key = listener_key(session_identity)

    with postgres_db.connect() as connection:
        track_row = connection.execute(
            """SELECT g.content_group_id,t.duration_ms
               FROM oap_music_content_groups g
               JOIN oap_music_tracks t ON t.track_id=g.track_id
               WHERE g.track_id=%s""",
            (track,),
        ).fetchone()
        if track_row is None:
            raise ValueError("content_group_missing")
        group_id = str(track_row[0])
        canonical_duration = (
            max(1, int(track_row[1]) // 1000) if track_row[1] not in (None, 0) else None
        )

        if event_value == "START":
            if playback_session_id not in (None, ""):
                raise ValueError("playback_session_must_be_server_created")
            session_id = str(uuid4())
            sequence = 1
            connection.execute(
                """INSERT INTO oap_music_playback_sessions(
                   playback_session_id,content_group_id,track_id,surface,listener_key,
                   canonical_duration_seconds,last_sequence,
                   postcode,borough,region,country,continent)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    session_id,group_id,track,surface_value,key,canonical_duration,sequence,
                    _coarse(postcode,16),_coarse(borough,120),_coarse(region,120),
                    _coarse(country,120),_coarse(continent,80),
                ),
            )
            qualified_once = False
            observed_seconds = 0
        else:
            session_id = _uuid(playback_session_id, "playback_session_id")
            try:
                sequence = int(event_sequence)
            except (TypeError, ValueError) as exc:
                raise ValueError("event_sequence_required") from exc
            if sequence <= 1:
                raise ValueError("invalid_event_sequence")
            session_row = connection.execute(
                """SELECT listener_key,track_id,surface,last_sequence,max_playback_seconds,
                          started_at,completed_at,canonical_duration_seconds,qualified
                   FROM oap_music_playback_sessions
                   WHERE playback_session_id=%s FOR UPDATE""",
                (session_id,),
            ).fetchone()
            if session_row is None:
                raise ValueError("playback_session_missing")
            if str(session_row[0]) != key or str(session_row[1]) != track or str(session_row[2]) != surface_value:
                raise ValueError("playback_session_mismatch")
            if session_row[6] is not None:
                raise ValueError("playback_session_complete")
            if sequence <= int(session_row[3]):
                raise ValueError("engagement_replay")
            previous_played = int(session_row[4] or 0)
            if played < previous_played:
                raise ValueError("playback_progress_reversed")

            started_at = session_row[5]
            elapsed = max(0, int((datetime.now(timezone.utc) - started_at).total_seconds()))
            # Client progress may not outrun server-observed elapsed time by more than a small seek/grace window.
            if played > elapsed + 10:
                raise ValueError("playback_progress_impossible")
            observed_seconds = max(previous_played, min(played, elapsed + 10))
            canonical_duration = session_row[7]
            qualified_once = bool(session_row[8]) or qualifies(
                event_type=event_value,
                playback_seconds=observed_seconds,
                duration_seconds=canonical_duration,
            )
            connection.execute(
                """UPDATE oap_music_playback_sessions
                   SET last_seen_at=CURRENT_TIMESTAMP,
                       completed_at=CASE WHEN %s='COMPLETE' THEN CURRENT_TIMESTAMP ELSE completed_at END,
                       max_playback_seconds=%s,
                       last_sequence=%s,
                       qualified=%s,
                       qualified_at=CASE
                         WHEN qualified=FALSE AND %s=TRUE THEN CURRENT_TIMESTAMP
                         ELSE qualified_at
                       END
                   WHERE playback_session_id=%s""",
                (
                    event_value,observed_seconds,sequence,qualified_once,qualified_once,session_id,
                ),
            )

        event_id = str(uuid4())
        connection.execute(
            """INSERT INTO oap_music_engagement_events(
               event_id,content_group_id,track_id,surface,listener_key,event_type,
               playback_seconds,duration_seconds,qualified,
               postcode,borough,region,country,continent,
               playback_session_id,event_sequence)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                event_id,group_id,track,surface_value,key,event_value,
                observed_seconds,canonical_duration,qualified_once,
                _coarse(postcode,16),_coarse(borough,120),_coarse(region,120),
                _coarse(country,120),_coarse(continent,80),session_id,sequence,
            ),
        )
        connection.commit()
    return {
        "event_id": event_id,
        "playback_session_id": session_id,
        "event_sequence": sequence,
        "content_group_id": group_id,
        "surface": surface_value,
        "event_type": event_value,
        "qualified": qualified_once,
        "qualification_unit": "playback_session",
        "listener_identity_exposed": False,
        "precise_location_stored": False,
        "payout_created": False,
        "ranking_authority_created": False,
    }


def artist_audience(identity_id: object) -> dict[str, object]:
    owner = _uuid(identity_id, "identity_id")
    now = datetime.now(timezone.utc)
    with postgres_db.connect(readonly=True) as connection:
        totals = connection.execute(
            """SELECT
                 COUNT(*),
                 COUNT(*) FILTER (WHERE e.qualified=TRUE),
                 COUNT(DISTINCT e.listener_key) FILTER (WHERE e.qualified=TRUE),
                 COUNT(DISTINCT e.listener_key) FILTER (
                   WHERE e.last_seen_at >= CURRENT_TIMESTAMP - INTERVAL '90 seconds'
                     AND e.completed_at IS NULL
                 ),
                 COUNT(*) FILTER (WHERE e.surface='OAP_MUSIC' AND e.qualified=TRUE),
                 COUNT(*) FILTER (WHERE e.surface='OAP_TV' AND e.qualified=TRUE),
                 COUNT(*) FILTER (WHERE e.surface='OAP_RADIO' AND e.qualified=TRUE),
                 COUNT(DISTINCT (e.content_group_id,e.listener_key)) FILTER (WHERE e.qualified=TRUE)
               FROM oap_music_playback_sessions e
               JOIN oap_music_content_groups g ON g.content_group_id=e.content_group_id
               WHERE g.owner_identity_id=%s""",
            (owner,),
        ).fetchone()
        places = connection.execute(
            """SELECT COALESCE(e.country,'Unknown') AS country,
                      COALESCE(e.region,'Unknown') AS region,
                      COALESCE(e.borough,'Unknown') AS borough,
                      COUNT(DISTINCT e.listener_key) AS listeners
               FROM oap_music_playback_sessions e
               JOIN oap_music_content_groups g ON g.content_group_id=e.content_group_id
               WHERE g.owner_identity_id=%s AND e.qualified=TRUE
               GROUP BY country,region,borough
               ORDER BY listeners DESC,country,region,borough
               LIMIT 25""",
            (owner,),
        ).fetchall()
        tracks = connection.execute(
            """SELECT e.track_id,COUNT(*) FILTER (WHERE e.qualified=TRUE) AS qualified_events,
                      COUNT(DISTINCT e.listener_key) FILTER (WHERE e.qualified=TRUE) AS listeners
               FROM oap_music_playback_sessions e
               JOIN oap_music_content_groups g ON g.content_group_id=e.content_group_id
               WHERE g.owner_identity_id=%s
               GROUP BY e.track_id
               ORDER BY qualified_events DESC,listeners DESC
               LIMIT 25""",
            (owner,),
        ).fetchall()
    row = totals or (0,0,0,0,0,0,0,0)
    return {
        "measured_at": now.isoformat(),
        "raw_starts": int(row[0] or 0),
        "qualified_listens": int(row[1] or 0),
        "unique_qualified_listeners": int(row[2] or 0),
        "listening_now": int(row[3] or 0),
        "music_qualified_views": int(row[4] or 0),
        "tv_qualified_views": int(row[5] or 0),
        "radio_qualified_plays": int(row[6] or 0),
        "combined_reach": int(row[7] or 0),
        "cross_surface_deduplication": "qualified_playback_sessions",
        "places": [
            {
                "country": str(p[0]),
                "region": str(p[1]),
                "borough": str(p[2]),
                "unique_listeners": int(p[3]),
            }
            for p in places
        ],
        "top_tracks": [
            {
                "track_id": str(t[0]),
                "qualified_sessions": int(t[1]),
                "unique_listeners": int(t[2]),
            }
            for t in tracks
        ],
        "listener_identity_exposed": False,
        "precise_location_exposed": False,
        "payout_created": False,
        "ranking_authority_created": False,
    }
