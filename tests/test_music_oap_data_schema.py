"""Fail-closed contracts for first-party OAP Data persistence."""
from mission_control.music_oap_data_schema import (
    OAP_DATA_SCHEMA_STATEMENTS,
    public_discovery_projection,
)


def test_additive_storage_and_indexes():
    ddl = "\n".join(OAP_DATA_SCHEMA_STATEMENTS)
    assert "CREATE TABLE IF NOT EXISTS oap_music_track_data" in ddl
    assert "REFERENCES oap_music_tracks(track_id)" in ddl
    assert "location_publication_consent BOOLEAN NOT NULL DEFAULT FALSE" in ddl
    assert "ix_oap_music_data_country_consented" in ddl
    assert "WHERE location_publication_consent IS TRUE" in ddl


def test_public_projection_is_rights_and_consent_gated():
    sql = public_discovery_projection()
    assert "r.state = 'PUBLISHED'" in sql
    assert "r.rights_status = 'VERIFIED'" in sql
    assert "CASE WHEN d.location_publication_consent IS TRUE" in sql
    assert "THEN d.country ELSE NULL END" in sql
    for prohibited in ("stream_url", "payment_authorized", "playback_enabled"):
        assert prohibited not in sql


def test_migration_requires_explicit_approval():
    import pytest

    from mission_control.music_oap_data_schema import init_oap_data_schema

    with pytest.raises(RuntimeError, match="Explicit human approval"):
        init_oap_data_schema()


def test_migration_dry_run_is_non_mutating(monkeypatch):
    from mission_control import music_oap_data_schema
    from mission_control.music_oap_data_schema import (
        OAP_DATA_MIGRATION_CHECKSUM,
        OAP_DATA_MIGRATION_VERSION,
        init_oap_data_schema,
    )

    monkeypatch.setattr(
        music_oap_data_schema.postgres_db,
        "postgres_status",
        lambda: {"initialized": True},
    )
    result = init_oap_data_schema(assume_yes=True, dry_run=True)
    assert result["dry_run"] is True
    assert result["migration"] == OAP_DATA_MIGRATION_VERSION
    assert result["checksum"] == OAP_DATA_MIGRATION_CHECKSUM
