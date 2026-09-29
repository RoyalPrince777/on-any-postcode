"""Canonical Music content metadata and OAP TV linkage.

Lyrics, credits and video relationships remain attached to one Music track.
Video bytes are not duplicated here. OAP TV linkage uses a shared content-group
identity so future qualified engagement can aggregate across surfaces without
blindly summing duplicate views.
"""
from __future__ import annotations

import json
from uuid import UUID, uuid4

from . import postgres_db

MUSIC_CONTENT_LINK_MIGRATION_VERSION = "0019_oap_music_content_links"
VIDEO_KINDS = frozenset({"OFFICIAL_VIDEO","LYRIC_VIDEO","VISUALISER","LIVE_PERFORMANCE","BEHIND_THE_SCENES"})

SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_music_content_groups (
        content_group_id UUID PRIMARY KEY,
        track_id UUID NOT NULL UNIQUE REFERENCES oap_music_tracks(track_id) ON DELETE CASCADE,
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS oap_music_track_content (
        track_id UUID PRIMARY KEY REFERENCES oap_music_tracks(track_id) ON DELETE CASCADE,
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        lyrics TEXT,
        credits JSONB NOT NULL DEFAULT '[]'::jsonb,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS oap_music_video_links (
        video_link_id UUID PRIMARY KEY,
        content_group_id UUID NOT NULL REFERENCES oap_music_content_groups(content_group_id)
            ON DELETE CASCADE,
        track_id UUID NOT NULL REFERENCES oap_music_tracks(track_id) ON DELETE CASCADE,
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        video_kind TEXT NOT NULL CHECK (video_kind IN
            ('OFFICIAL_VIDEO','LYRIC_VIDEO','VISUALISER','LIVE_PERFORMANCE','BEHIND_THE_SCENES')),
        oap_tv_path TEXT NOT NULL,
        active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(track_id,video_kind,oap_tv_path)
    )""",
    """CREATE INDEX IF NOT EXISTS ix_music_video_links_group
       ON oap_music_video_links(content_group_id,active,created_at DESC)""",
)


def _uuid(value: object, name: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"invalid_{name}") from exc


def _owner_track(connection, owner: str, track: str) -> None:
    row = connection.execute(
        """SELECT 1
           FROM oap_music_tracks t
           JOIN oap_music_releases r ON r.release_id=t.release_id
           WHERE t.track_id=%s AND r.owner_identity_id=%s""",
        (track, owner),
    ).fetchone()
    if row is None:
        raise PermissionError("track_not_owned")


def _content_group(connection, owner: str, track: str) -> str:
    row = connection.execute(
        "SELECT content_group_id FROM oap_music_content_groups WHERE track_id=%s",
        (track,),
    ).fetchone()
    if row is not None:
        return str(row[0])
    group_id = str(uuid4())
    connection.execute(
        """INSERT INTO oap_music_content_groups(content_group_id,track_id,owner_identity_id)
           VALUES (%s,%s,%s)""",
        (group_id, track, owner),
    )
    return group_id


def save_track_content(
    *,
    owner_identity_id: object,
    track_id: object,
    lyrics: object = None,
    credits: object = None,
) -> dict[str, object]:
    owner = _uuid(owner_identity_id, "owner_identity_id")
    track = _uuid(track_id, "track_id")
    lyrics_value = None if lyrics in (None, "") else str(lyrics)
    if lyrics_value is not None and len(lyrics_value) > 100_000:
        raise ValueError("lyrics_too_long")
    credit_rows = [] if credits is None else credits
    if not isinstance(credit_rows, list) or len(credit_rows) > 200:
        raise ValueError("invalid_credits")
    normalized = []
    for item in credit_rows:
        if not isinstance(item, dict):
            raise ValueError("invalid_credit")
        name = " ".join(str(item.get("name") or "").split())
        role = " ".join(str(item.get("role") or "").split())
        if not name or not role or len(name) > 180 or len(role) > 120:
            raise ValueError("invalid_credit")
        normalized.append({"name": name, "role": role})
    with postgres_db.connect() as connection:
        _owner_track(connection, owner, track)
        group_id = _content_group(connection, owner, track)
        connection.execute(
            """INSERT INTO oap_music_track_content(track_id,owner_identity_id,lyrics,credits)
               VALUES (%s,%s,%s,%s::jsonb)
               ON CONFLICT (track_id) DO UPDATE SET
                 lyrics=EXCLUDED.lyrics,credits=EXCLUDED.credits,
                 updated_at=CURRENT_TIMESTAMP""",
            (track, owner, lyrics_value, json.dumps(normalized)),
        )
        connection.commit()
    return {
        "track_id": track,
        "content_group_id": group_id,
        "lyrics_present": bool(lyrics_value),
        "credit_count": len(normalized),
        "video_bytes_duplicated": False,
        "human_authority_final": True,
    }


def add_video_link(
    *,
    owner_identity_id: object,
    track_id: object,
    video_kind: object,
    oap_tv_path: object = "/tv-media",
) -> dict[str, object]:
    owner = _uuid(owner_identity_id, "owner_identity_id")
    track = _uuid(track_id, "track_id")
    kind = str(video_kind or "").strip().upper()
    if kind not in VIDEO_KINDS:
        raise ValueError("invalid_video_kind")
    path = str(oap_tv_path or "").strip()
    if not path.startswith("/") or len(path) > 500:
        raise ValueError("invalid_oap_tv_path")
    link_id = str(uuid4())
    with postgres_db.connect() as connection:
        _owner_track(connection, owner, track)
        group_id = _content_group(connection, owner, track)
        row = connection.execute(
            """INSERT INTO oap_music_video_links(
               video_link_id,content_group_id,track_id,owner_identity_id,video_kind,oap_tv_path)
               VALUES (%s,%s,%s,%s,%s,%s)
               ON CONFLICT (track_id,video_kind,oap_tv_path) DO UPDATE SET active=TRUE
               RETURNING video_link_id""",
            (link_id, group_id, track, owner, kind, path),
        ).fetchone()
        connection.commit()
    return {
        "video_link_id": str(row[0]),
        "track_id": track,
        "content_group_id": group_id,
        "video_kind": kind,
        "oap_tv_path": path,
        "video_bytes_duplicated": False,
        "shared_engagement_identity": True,
        "view_count": None,
        "qualified_engagement_measurement_proven": False,
    }


def engagement_contract(*, content_group_id: object) -> dict[str, object]:
    group_id = _uuid(content_group_id, "content_group_id")
    return {
        "content_group_id": group_id,
        "surfaces": ("OAP Music", "OAP TV"),
        "music_views": None,
        "tv_views": None,
        "combined_reach": None,
        "cross_surface_dedupe_ready": False,
        "raw_counts_must_not_be_blindly_added": True,
        "qualified_engagement_measurement_proven": False,
    }
