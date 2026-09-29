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
SURFACES = frozenset({"OAP_MUSIC", "OAP_TV"})
EVENT_TYPES = frozenset({"START", "HEARTBEAT", "COMPLETE"})
MIN_QUALIFIED_SECONDS = 30
ACTIVE_WINDOW_SECONDS = 90

SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_music_engagement_events (
        event_id UUID PRIMARY KEY,
        content_group_id UUID NOT NULL REFERENCES oap_music_content_groups(content_group_id)
            ON DELETE CASCADE,
        track_id UUID NOT NULL REFERENCES oap_music_tracks(track_id) ON DELETE CASCADE,
        surface TEXT NOT NULL CHECK (surface IN ('OAP_MUSIC','OAP_TV')),
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
    played = int(playback_seconds or 0)
    duration = None if duration_seconds in (None, "") else int(duration_seconds)
    is_qualified = qualifies(
        event_type=event_value,
        playback_seconds=played,
        duration_seconds=duration,
    )
    key = listener_key(session_identity)
    with postgres_db.connect() as connection:
        row = connection.execute(
            """SELECT content_group_id FROM oap_music_content_groups WHERE track_id=%s""",
            (track,),
        ).fetchone()
        if row is None:
            raise ValueError("content_group_missing")
        group_id = str(row[0])
        event_id = str(uuid4())
        connection.execute(
            """INSERT INTO oap_music_engagement_events(
               event_id,content_group_id,track_id,surface,listener_key,event_type,
               playback_seconds,duration_seconds,qualified,
               postcode,borough,region,country,continent)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                event_id,group_id,track,surface_value,key,event_value,played,duration,
                is_qualified,_coarse(postcode,16),_coarse(borough,120),_coarse(region,120),
                _coarse(country,120),_coarse(continent,80),
            ),
        )
        connection.commit()
    return {
        "event_id": event_id,
        "content_group_id": group_id,
        "surface": surface_value,
        "event_type": event_value,
        "qualified": is_qualified,
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
                 COUNT(*) FILTER (WHERE e.event_type='START'),
                 COUNT(*) FILTER (WHERE e.qualified=TRUE),
                 COUNT(DISTINCT e.listener_key) FILTER (WHERE e.qualified=TRUE),
                 COUNT(DISTINCT e.listener_key) FILTER (
                   WHERE e.occurred_at >= CURRENT_TIMESTAMP - INTERVAL '90 seconds'
                 ),
                 COUNT(*) FILTER (WHERE e.surface='OAP_MUSIC' AND e.qualified=TRUE),
                 COUNT(*) FILTER (WHERE e.surface='OAP_TV' AND e.qualified=TRUE),
                 COUNT(DISTINCT (e.content_group_id,e.listener_key)) FILTER (WHERE e.qualified=TRUE)
               FROM oap_music_engagement_events e
               JOIN oap_music_content_groups g ON g.content_group_id=e.content_group_id
               WHERE g.owner_identity_id=%s""",
            (owner,),
        ).fetchone()
        places = connection.execute(
            """SELECT COALESCE(e.country,'Unknown') AS country,
                      COALESCE(e.region,'Unknown') AS region,
                      COALESCE(e.borough,'Unknown') AS borough,
                      COUNT(DISTINCT e.listener_key) AS listeners
               FROM oap_music_engagement_events e
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
               FROM oap_music_engagement_events e
               JOIN oap_music_content_groups g ON g.content_group_id=e.content_group_id
               WHERE g.owner_identity_id=%s
               GROUP BY e.track_id
               ORDER BY qualified_events DESC,listeners DESC
               LIMIT 25""",
            (owner,),
        ).fetchall()
    row = totals or (0,0,0,0,0,0,0)
    return {
        "measured_at": now.isoformat(),
        "raw_starts": int(row[0] or 0),
        "qualified_listens": int(row[1] or 0),
        "unique_qualified_listeners": int(row[2] or 0),
        "listening_now": int(row[3] or 0),
        "music_qualified_views": int(row[4] or 0),
        "tv_qualified_views": int(row[5] or 0),
        "combined_reach": int(row[6] or 0),
        "cross_surface_deduplication": "content_group_plus_listener",
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
                "qualified_events": int(t[1]),
                "unique_listeners": int(t[2]),
            }
            for t in tracks
        ],
        "listener_identity_exposed": False,
        "precise_location_exposed": False,
        "payout_created": False,
        "ranking_authority_created": False,
    }
