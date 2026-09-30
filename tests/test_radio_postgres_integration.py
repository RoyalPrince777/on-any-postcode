"""Real isolated PostgreSQL proof for Founder-only Radio station/show gates.

Never touches production. CI explicitly supplies a disposable PostgreSQL URL.
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from uuid import uuid4

import pytest

from mission_control import radio_core

URL = os.getenv("OAP_RADIO_TEST_POSTGRES_URL")


@pytest.mark.skipif(not URL, reason="isolated Radio PostgreSQL URL not configured")
def test_founder_station_and_show_gate_on_real_postgres(monkeypatch):
    psycopg = pytest.importorskip("psycopg")
    schema = "radio_proof_" + uuid4().hex
    owner = str(uuid4())
    # Names are generated from hex only; there is no user-controlled SQL identifier.
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
            conn.execute("CREATE TABLE users(id UUID PRIMARY KEY)")
            conn.execute("CREATE TABLE oap_music_tracks(track_id UUID PRIMARY KEY)")
            conn.execute("INSERT INTO users(id) VALUES (%s)", (owner,))
            for statement in radio_core.SCHEMA_STATEMENTS:
                conn.execute(statement)
            for statement in radio_core.RADIO_ALWAYS_ON_SCHEMA_STATEMENTS:
                conn.execute(statement)
            for statement in radio_core.RADIO_FOUNDER_APPROVAL_SCHEMA_STATEMENTS:
                conn.execute(statement)
            conn.commit()

        monkeypatch.setattr(radio_core.postgres_db, "connect", isolated_connect)
        store = radio_core.RadioStore()
        station = store.create_station(
            owner_identity_id=owner, name="Founder Station", slug="founder-station"
        )
        station_id = station["station_id"]
        with pytest.raises(PermissionError, match="radio_station_not_owned"):
            store.set_always_on(
                owner_identity_id=owner, station_id=station_id, enabled=True
            )

        show = store.create_show(
            owner_identity_id=owner, station_id=station_id, title="Founder Show"
        )
        with pytest.raises(PermissionError):
            store.schedule_show(
                owner_identity_id=owner, station_id=station_id,
                show_id=show["show_id"],
                starts_at="2026-10-01T18:00:00+00:00",
                ends_at="2026-10-01T19:00:00+00:00",
            )

        approved_station = store.approve_station(
            founder_identity_id=owner, station_id=station_id
        )
        assert approved_station["founder_approved"] is True
        assert approved_station["state"] == "ACTIVE"
        setting = store.set_always_on(
            owner_identity_id=owner, station_id=station_id, enabled=True
        )
        assert setting["always_on"] is True
        assert setting["public_broadcast_claimed"] is False

        with pytest.raises(PermissionError):
            store.schedule_show(
                owner_identity_id=owner, station_id=station_id,
                show_id=show["show_id"],
                starts_at="2026-10-01T18:00:00+00:00",
                ends_at="2026-10-01T19:00:00+00:00",
            )
        approved_show = store.approve_show(
            founder_identity_id=owner, station_id=station_id,
            show_id=show["show_id"],
        )
        assert approved_show["founder_approved"] is True
        schedule = store.schedule_show(
            owner_identity_id=owner, station_id=station_id,
            show_id=show["show_id"],
            starts_at="2026-10-01T18:00:00+00:00",
            ends_at="2026-10-01T19:00:00+00:00",
        )
        assert schedule["broadcast_started"] is False
        stopped = store.stop_station(
            owner_identity_id=owner, station_id=station_id, reason="Founder STOP"
        )
        assert stopped["stopped"] is True
        assert stopped["broadcast_enabled"] is False
    finally:
        with psycopg.connect(URL, autocommit=True) as admin:
            admin.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")
