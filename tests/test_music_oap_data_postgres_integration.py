"""Opt-in real PostgreSQL migration/readback proof for OAP Music 0007.

Run only against an isolated disposable database with 0006 already applied.
Never runs in the default test suite without OAP_TEST_MUSIC_PG=1.
"""
from __future__ import annotations

import os
from urllib.parse import urlparse

import pytest

from mission_control import music_oap_data_schema as data

pytestmark = pytest.mark.skipif(
    os.getenv("OAP_TEST_MUSIC_PG") != "1",
    reason="requires explicit isolated PostgreSQL test opt-in",
)


def test_real_0007_migration_and_consent_readback(monkeypatch):
    url = os.getenv("OAP_POSTGRES_URL") or os.getenv("DATABASE_URL", "")
    parsed = urlparse(url)
    if parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
        pytest.fail("refusing migration test outside loopback PostgreSQL")
    if not parsed.path.lstrip("/").startswith("oap_test_"):
        pytest.fail("database name must start with oap_test_")
    if not data.postgres_db.postgres_status().get("initialized"):
        pytest.fail("base schema missing from disposable test database")

    # This test must not grant publication or playback rights.
    result = data.init_oap_data_schema(assume_yes=True)
    assert result["checksum"] == data.OAP_DATA_MIGRATION_CHECKSUM
    assert data.oap_data_schema_status()["schema_ready"] is True
    data.init_oap_data_schema(assume_yes=True)  # repeat must be safe

    # Exercise the real public query with a transaction-scoped fixture.
    # This fixture must use actual product-core column requirements.
    import uuid

    with data.postgres_db.connect() as connection:
        connection.execute("SAVEPOINT oap_data_consent_probe")
        try:
            release_id = str(uuid.uuid4())
            track_id = str(uuid.uuid4())
            # The fixture deliberately relies on the product-core schema.
            # If its required columns change, this proof must be updated rather
            # than silently reporting success.
            connection.execute(
                """INSERT INTO oap_music_releases
                   (release_id, title, state, rights_status)
                   VALUES (%s, %s, 'PUBLISHED', 'VERIFIED')""",
                (release_id, "OAP consent probe"),
            )
            connection.execute(
                """INSERT INTO oap_music_tracks
                   (track_id, release_id, title, position)
                   VALUES (%s, %s, %s, 1)""",
                (track_id, release_id, "Consent test"),
            )
            connection.execute(
                """INSERT INTO oap_music_track_data
                   (track_id, genre, language, country, location_publication_consent)
                   VALUES (%s, 'Highlife', 'ak', 'GH', TRUE)""",
                (track_id,),
            )
            sql = data.public_discovery_projection() + " AND t.track_id=%s"
            row = connection.execute(sql, (track_id,)).fetchone()
            assert row is not None and row[6] == "GH"
            connection.execute(
                """UPDATE oap_music_track_data
                   SET location_publication_consent=FALSE WHERE track_id=%s""",
                (track_id,),
            )
            row = connection.execute(sql, (track_id,)).fetchone()
            assert row is not None and row[6] is None
            assert connection.execute(
                sql + " AND d.location_publication_consent IS TRUE AND d.country=%s",
                (track_id, "GH"),
            ).fetchone() is None
            connection.execute(
                "UPDATE oap_music_releases SET rights_status='UNVERIFIED' WHERE release_id=%s",
                (release_id,),
            )
            assert connection.execute(sql, (track_id,)).fetchone() is None
        finally:
            connection.execute("ROLLBACK TO SAVEPOINT oap_data_consent_probe")
            connection.rollback()

    # The migration itself is intentionally committed to the disposable database.
    # Only fixture writes above are rolled back.
    with data.postgres_db.connect() as connection:
        parent = connection.execute(
            "SELECT 1 FROM oap_schema_migrations WHERE version=%s",
            ("0006_music_market_post_office",),
        ).fetchone()
        assert parent is not None
        consent_default = connection.execute(
            """SELECT location_publication_consent FROM oap_music_track_data
               WHERE FALSE"""
        ).fetchall()
        assert consent_default == []
        constraint = connection.execute(
            """SELECT count(*) FROM pg_constraint
               WHERE conrelid='public.oap_music_track_data'::regclass
                 AND contype='f'"""
        ).fetchone()
        assert constraint is not None and constraint[0] >= 1
        connection.rollback()
