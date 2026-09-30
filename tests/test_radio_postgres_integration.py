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

        # Archive is a hard lifecycle barrier even when approval remains recorded.
        with isolated_connect() as conn:
            conn.execute(
                "UPDATE oap_radio_stations SET state='ARCHIVED' WHERE station_id=%s",
                (station_id,),
            )
            conn.commit()
        with pytest.raises(PermissionError):
            store.approve_station(founder_identity_id=owner, station_id=station_id)
        with pytest.raises(PermissionError):
            store.approve_show(
                founder_identity_id=owner, station_id=station_id,
                show_id=show["show_id"],
            )
        with pytest.raises(PermissionError):
            store.schedule_show(
                owner_identity_id=owner, station_id=station_id,
                show_id=show["show_id"],
                starts_at="2026-10-02T18:00:00+00:00",
                ends_at="2026-10-02T19:00:00+00:00",
            )
        with pytest.raises(PermissionError):
            store.set_always_on(
                owner_identity_id=owner, station_id=station_id, enabled=True
            )

        with isolated_connect() as conn:
            conn.execute(
                "UPDATE oap_radio_stations SET state='ACTIVE' WHERE station_id=%s",
                (station_id,),
            )
            conn.execute(
                "UPDATE oap_radio_shows SET state='ARCHIVED' WHERE show_id=%s",
                (show["show_id"],),
            )
            conn.commit()
        with pytest.raises(PermissionError):
            store.approve_show(
                founder_identity_id=owner, station_id=station_id,
                show_id=show["show_id"],
            )
        with pytest.raises(PermissionError):
            store.schedule_show(
                owner_identity_id=owner, station_id=station_id,
                show_id=show["show_id"],
                starts_at="2026-10-02T18:00:00+00:00",
                ends_at="2026-10-02T19:00:00+00:00",
            )
    finally:
        with psycopg.connect(URL, autocommit=True) as admin:
            admin.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")


@pytest.mark.skipif(not URL, reason="isolated Radio PostgreSQL URL not configured")
def test_delivery_admission_real_postgres_stop_and_receipt_readback(monkeypatch):
    """Exercise real constraints, row gate, committed receipt and STOP denial."""
    psycopg = pytest.importorskip("psycopg")
    schema = "radio_admission_" + uuid4().hex
    owner, station_track, asset, entitlement = (str(uuid4()) for _ in range(4))
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
            conn.execute(
                """CREATE TABLE oap_music_assets(
                   asset_id UUID PRIMARY KEY,
                   owner_identity_id UUID NOT NULL,
                   track_id UUID NOT NULL,
                   sha256 CHAR(64) NOT NULL,
                   stopped BOOLEAN NOT NULL DEFAULT FALSE)"""
            )
            conn.execute(
                """CREATE TABLE oap_music_entitlements(
                   entitlement_id UUID PRIMARY KEY,
                   asset_id UUID NOT NULL,
                   owner_identity_id UUID NOT NULL,
                   active BOOLEAN NOT NULL DEFAULT TRUE,
                   access_scope TEXT NOT NULL,
                   channel TEXT NOT NULL,
                   territory TEXT NOT NULL,
                   valid_from TIMESTAMPTZ,
                   valid_until TIMESTAMPTZ)"""
            )
            conn.execute(
                """CREATE TABLE oap_music_rights_grants(
                   grant_id UUID PRIMARY KEY,
                   asset_id UUID NOT NULL,
                   owner_identity_id UUID NOT NULL,
                   right_type TEXT NOT NULL,
                   permitted_uses TEXT[] NOT NULL,
                   territories TEXT[] NOT NULL,
                   permitted_channels TEXT[] NOT NULL,
                   authority_verified BOOLEAN NOT NULL,
                   authority_receipt_hash CHAR(64),
                   human_approved BOOLEAN NOT NULL,
                   human_approval_receipt_hash CHAR(64),
                   evidence_hashes TEXT[] NOT NULL,
                   revoked BOOLEAN NOT NULL DEFAULT FALSE,
                   valid_from TIMESTAMPTZ,
                   valid_until TIMESTAMPTZ)"""
            )
            conn.execute("INSERT INTO users(id) VALUES (%s)", (owner,))
            conn.execute(
                "INSERT INTO oap_music_tracks(track_id) VALUES (%s)", (station_track,)
            )
            for statement in radio_core.SCHEMA_STATEMENTS:
                conn.execute(statement)
            for statement in radio_core.RADIO_ALWAYS_ON_SCHEMA_STATEMENTS:
                conn.execute(statement)
            for statement in radio_core.RADIO_FOUNDER_APPROVAL_SCHEMA_STATEMENTS:
                conn.execute(statement)
            for statement in radio_core.RADIO_DELIVERY_ADMISSION_SCHEMA_STATEMENTS:
                conn.execute(statement)
            conn.commit()

        monkeypatch.setattr(radio_core.postgres_db, "connect", isolated_connect)
        store = radio_core.RadioStore()
        station = store.create_station(
            owner_identity_id=owner, name="Admission Proof", slug="admission-proof"
        )["station_id"]
        store.approve_station(founder_identity_id=owner, station_id=station)
        store.set_always_on(owner_identity_id=owner, station_id=station, enabled=True)

        with isolated_connect() as conn:
            conn.execute(
                """INSERT INTO oap_music_assets(
                   asset_id,owner_identity_id,track_id,sha256)
                   VALUES (%s,%s,%s,%s)""",
                (asset, owner, station_track, "b" * 64),
            )
            conn.execute(
                """INSERT INTO oap_music_entitlements(
                   entitlement_id,asset_id,owner_identity_id,
                   access_scope,channel,territory)
                   VALUES (%s,%s,%s,'PUBLIC_FREE','OAP Radio','*')""",
                (entitlement, asset, owner),
            )
            conn.execute(
                """INSERT INTO oap_radio_rotation(
                   station_id,owner_identity_id,track_id,position)
                   VALUES (%s,%s,%s,1)""",
                (station, owner, station_track),
            )
            grant_id = str(uuid4())
            conn.execute(
                """INSERT INTO oap_music_rights_grants(
                   grant_id,asset_id,owner_identity_id,right_type,
                   permitted_uses,territories,permitted_channels,
                   authority_verified,authority_receipt_hash,human_approved,
                   human_approval_receipt_hash,evidence_hashes)
                   VALUES (%s,%s,%s,'recording',ARRAY['stream'],ARRAY['*'],
                           ARRAY['OAP Radio'],TRUE,%s,TRUE,%s,ARRAY[%s])""",
                (grant_id, asset, owner, "c" * 64, "d" * 64, "e" * 64),
            )
            conn.commit()

        args = {
            "station_id": station,
            "track_id": station_track,
            "asset_id": asset,
            "owner_identity_id": owner,
            "entitlement_id": entitlement,
            "rights_decision_hash": "a" * 64,
            "media_sha256": "b" * 64,
            "prepared_bytes": 4,
            "response_status": 206,
        }
        receipt = store.admit_delivery(**args)
        assert receipt is not None
        with isolated_connect(readonly=True) as conn:
            row = conn.execute(
                """SELECT receipt_type,prepared_bytes,response_status,
                          rights_decision_hash,media_sha256
                   FROM oap_radio_delivery_admissions
                   WHERE receipt_id=%s AND station_id=%s""",
                (receipt, station),
            ).fetchone()
        assert row == ("RESPONSE_PREPARED", 4, 206, "a" * 64, "b" * 64)
        # A digest that was valid at asset-read time must still match the
        # locked canonical asset row before any prepared-response receipt.
        with isolated_connect() as conn:
            conn.execute(
                "UPDATE oap_music_assets SET sha256=%s WHERE asset_id=%s",
                ("f" * 64, asset),
            )
            conn.commit()
        assert store.admit_delivery(**args) is None
        with isolated_connect(readonly=True) as conn:
            assert conn.execute(
                "SELECT count(*) FROM oap_radio_delivery_admissions"
            ).fetchone()[0] == 1
        with isolated_connect() as conn:
            conn.execute(
                "UPDATE oap_music_assets SET sha256=%s WHERE asset_id=%s",
                ("b" * 64, asset),
            )
            conn.commit()
        receipts = store.delivery_receipts(owner_identity_id=owner, station_id=station)
        assert len(receipts) == 1
        assert receipts[0]["receipt_id"] == receipt
        assert receipts[0]["receipt_type"] == "RESPONSE_PREPARED"
        assert receipts[0]["prepared_bytes"] == 4
        assert receipts[0]["delivery_completed"] is False
        assert receipts[0]["airplay_confirmed"] is False
        assert store.delivery_receipts(
            owner_identity_id=str(uuid4()), station_id=station
        ) == []

        # Revocation holds a PostgreSQL UPDATE lock on the same grant that
        # response admission needs FOR SHARE. An uncommitted revocation must
        # prevent a new prepared-response receipt.
        with psycopg.connect(URL, options=f"-c search_path={schema}") as revoker:
            revoker.execute(
                "UPDATE oap_music_rights_grants SET revoked=TRUE WHERE grant_id=%s",
                (grant_id,),
            )

            @contextmanager
            def bounded_connect(*, readonly=False):
                with isolated_connect(readonly=readonly) as conn:
                    conn.execute("SET LOCAL lock_timeout='200ms'")
                    yield conn

            monkeypatch.setattr(radio_core.postgres_db, "connect", bounded_connect)
            with pytest.raises(psycopg.errors.LockNotAvailable):
                store.admit_delivery(**args)
            # The outer revoker commits on context exit.
        monkeypatch.setattr(radio_core.postgres_db, "connect", isolated_connect)
        assert store.admit_delivery(**args) is None
        with isolated_connect(readonly=True) as conn:
            assert conn.execute(
                "SELECT count(*) FROM oap_radio_delivery_admissions"
            ).fetchone()[0] == 1
        # Restore the valid grant to prove STOP remains an independent barrier.
        with isolated_connect() as conn:
            conn.execute(
                "UPDATE oap_music_rights_grants SET revoked=FALSE WHERE grant_id=%s",
                (grant_id,),
            )
            conn.commit()

        # Asset STOP and entitlement revocation must have the same
        # transaction boundary: their uncommitted UPDATE locks block
        # admission, and committed revocations deny it with no new receipt.
        for target, row_id, change, restore in (
            (
                "oap_music_entitlements", entitlement,
                "active=FALSE", "active=TRUE",
            ),
            (
                "oap_music_assets", asset,
                "stopped=TRUE", "stopped=FALSE",
            ),
        ):
            key = "entitlement_id" if target == "oap_music_entitlements" else "asset_id"
            with psycopg.connect(URL, options=f"-c search_path={schema}") as revoker:
                revoker.execute(
                    f"UPDATE {target} SET {change} WHERE {key}=%s", (row_id,)
                )
                monkeypatch.setattr(
                    radio_core.postgres_db, "connect", bounded_connect
                )
                with pytest.raises(psycopg.errors.LockNotAvailable):
                    store.admit_delivery(**args)
            monkeypatch.setattr(
                radio_core.postgres_db, "connect", isolated_connect
            )
            assert store.admit_delivery(**args) is None
            with isolated_connect(readonly=True) as conn:
                assert conn.execute(
                    "SELECT count(*) FROM oap_radio_delivery_admissions"
                ).fetchone()[0] == 1
            with isolated_connect() as conn:
                conn.execute(
                    f"UPDATE {target} SET {restore} WHERE {key}=%s", (row_id,)
                )
                conn.commit()

        store.stop_station(
            owner_identity_id=owner, station_id=station, reason="Founder STOP"
        )
        assert store.admit_delivery(**args) is None
        with isolated_connect(readonly=True) as conn:
            total = conn.execute(
                "SELECT count(*) FROM oap_radio_delivery_admissions"
            ).fetchone()[0]
        assert total == 1
    finally:
        with psycopg.connect(URL, autocommit=True) as admin:
            admin.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")
