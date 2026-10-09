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

    # Readback is deliberately transactional and rolls back all fixture data.
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
