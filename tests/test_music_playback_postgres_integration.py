"""Disposable PostgreSQL acceptance for one qualified play per playback session.

Uses isolated schema and never writes to an existing application schema.
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from mission_control import music_engagement

URL = os.getenv("OAP_MUSIC_TEST_POSTGRES_URL")


@pytest.mark.skipif(not URL, reason="isolated Music PostgreSQL URL not configured")
def test_playback_session_qualification_replay_and_identity_boundaries(monkeypatch):
    psycopg = pytest.importorskip("psycopg")
    schema = "music_session_proof_" + uuid4().hex
    track = str(uuid4())
    group = str(uuid4())
    other_track = str(uuid4())
    with psycopg.connect(URL, autocommit=True) as admin:
        admin.execute(f"CREATE SCHEMA {schema}")
    try:
        @contextmanager
        def isolated_connect(*, readonly=False):
            with psycopg.connect(URL, options=f"-c search_path={schema}") as conn:
                if readonly:
                    conn.execute("SET TRANSACTION READ ONLY")
                yield conn

        with isolated_connect() as conn:
            conn.execute(
                """CREATE TABLE oap_music_tracks (
                    track_id UUID PRIMARY KEY, duration_ms INTEGER
                )"""
            )
            conn.execute(
                """CREATE TABLE oap_music_content_groups (
                    content_group_id UUID PRIMARY KEY,
                    track_id UUID NOT NULL REFERENCES oap_music_tracks(track_id),
                    owner_identity_id UUID NOT NULL
                )"""
            )
            conn.execute(
                "INSERT INTO oap_music_tracks(track_id,duration_ms) VALUES (%s,60000),(%s,60000)",
                (track, other_track),
            )
            conn.execute(
                "INSERT INTO oap_music_content_groups(content_group_id,track_id,owner_identity_id) "
                "VALUES (%s,%s,%s)",
                (group, track, str(uuid4())),
            )
            for statement in music_engagement.SCHEMA_STATEMENTS:
                conn.execute(statement)
            for statement in music_engagement.PLAYBACK_SESSION_SCHEMA_STATEMENTS:
                conn.execute(statement)
            conn.commit()

        monkeypatch.setattr(music_engagement.postgres_db, "connect", isolated_connect)
        store = music_engagement.record_event
        start = store(
            track_id=track, session_identity="listener-a", surface="OAP_MUSIC",
            event_type="START", playback_seconds=600,
        )
        sid = start["playback_session_id"]
        assert start["qualified"] is False
        assert start["event_sequence"] == 1

        # A client COMPLETE cannot manufacture 30 seconds immediately.
        early = store(
            track_id=track, session_identity="listener-a", surface="OAP_MUSIC",
            event_type="COMPLETE", playback_session_id=sid, event_sequence=2,
            playback_seconds=1,
        )
        assert early["qualified"] is False
        with pytest.raises(ValueError, match="playback_session_complete"):
            store(
                track_id=track, session_identity="listener-a", surface="OAP_MUSIC",
                event_type="HEARTBEAT", playback_session_id=sid, event_sequence=3,
                playback_seconds=30,
            )

        active = store(
            track_id=track, session_identity="listener-a", surface="OAP_MUSIC",
            event_type="START",
        )
        sid2 = active["playback_session_id"]
        with isolated_connect() as conn:
            conn.execute(
                "UPDATE oap_music_playback_sessions "
                "SET started_at=CURRENT_TIMESTAMP - INTERVAL '45 seconds' "
                "WHERE playback_session_id=%s",
                (sid2,),
            )
            conn.commit()
        with pytest.raises(ValueError, match="playback_session_mismatch"):
            store(
                track_id=track, session_identity="listener-b", surface="OAP_MUSIC",
                event_type="HEARTBEAT", playback_session_id=sid2,
                event_sequence=2, playback_seconds=30,
            )
        with pytest.raises(ValueError, match="playback_session_mismatch"):
            store(
                track_id=track, session_identity="listener-a", surface="OAP_RADIO",
                event_type="HEARTBEAT", playback_session_id=sid2,
                event_sequence=2, playback_seconds=30,
            )
        heartbeat = store(
            track_id=track, session_identity="listener-a", surface="OAP_MUSIC",
            event_type="HEARTBEAT", playback_session_id=sid2,
            event_sequence=2, playback_seconds=30,
        )
        assert heartbeat["qualified"] is True
        with pytest.raises(ValueError, match="engagement_replay"):
            store(
                track_id=track, session_identity="listener-a", surface="OAP_MUSIC",
                event_type="HEARTBEAT", playback_session_id=sid2,
                event_sequence=2, playback_seconds=30,
            )
        completed = store(
            track_id=track, session_identity="listener-a", surface="OAP_MUSIC",
            event_type="COMPLETE", playback_session_id=sid2,
            event_sequence=3, playback_seconds=30,
        )
        assert completed["qualified"] is True
        with isolated_connect(readonly=True) as conn:
            session_counts = conn.execute(
                """SELECT COUNT(*) FILTER (WHERE qualified),
                          COUNT(*) FROM oap_music_playback_sessions"""
            ).fetchone()
            events = conn.execute(
                """SELECT COUNT(*) FROM oap_music_engagement_events
                   WHERE playback_session_id=%s""",
                (sid2,),
            ).fetchone()[0]
        assert session_counts == (1, 2)
        assert events == 3  # START, HEARTBEAT and COMPLETE: only one qualified session.
    finally:
        with psycopg.connect(URL, autocommit=True) as admin:
            admin.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")
