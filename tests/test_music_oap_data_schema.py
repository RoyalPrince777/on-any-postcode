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


def test_discovery_country_requires_consent_and_verified_release(monkeypatch):
    from contextlib import contextmanager

    from mission_control import music_oap_data_schema

    observed = {}

    class Connection:
        def execute(self, sql, params):
            observed["sql"] = sql
            observed["params"] = params
            return self

        def fetchall(self):
            return []

    @contextmanager
    def connect(*, readonly=False):
        observed["readonly"] = readonly
        yield Connection()

    monkeypatch.setattr(music_oap_data_schema.postgres_db, "connect", connect)
    assert music_oap_data_schema.discover_public_data(country="GH", limit=5) == []
    assert observed["readonly"] is True
    assert "d.location_publication_consent IS TRUE AND d.country=%s" in observed["sql"]
    assert "r.state = 'PUBLISHED'" in observed["sql"]
    assert "r.rights_status = 'VERIFIED'" in observed["sql"]
    assert observed["params"] == ("GH", 5)


def test_discovery_rejects_invalid_country_without_database_access(monkeypatch):
    import pytest

    from mission_control import music_oap_data_schema

    def unexpected_connection(*, readonly=False):
        raise AssertionError("database accessed with invalid input")

    monkeypatch.setattr(music_oap_data_schema.postgres_db, "connect", unexpected_connection)
    with pytest.raises(ValueError, match="invalid country|invalid metadata label"):
        music_oap_data_schema.discover_public_data(country="GHA")


def test_schema_status_requires_matching_checksum_and_real_table(monkeypatch):
    from contextlib import contextmanager

    from mission_control import music_oap_data_schema as data

    state = {"checksum": data.OAP_DATA_MIGRATION_CHECKSUM, "table": "oap_music_track_data"}

    class Connection:
        def execute(self, sql, params=None):
            self.sql = sql
            return self

        def fetchone(self):
            if "checksum" in self.sql:
                return (state["checksum"],) if state["checksum"] is not None else None
            return (state["table"],)

    @contextmanager
    def connect(*, readonly=False):
        assert readonly is True
        yield Connection()

    monkeypatch.setattr(data.postgres_db, "postgres_status", lambda: {"initialized": True})
    monkeypatch.setattr(data.postgres_db, "connect", connect)
    assert data.oap_data_schema_status()["schema_ready"] is True
    state["checksum"] = "incorrect"
    assert data.oap_data_schema_status()["schema_ready"] is False
    state["checksum"] = data.OAP_DATA_MIGRATION_CHECKSUM
    state["table"] = None
    assert data.oap_data_schema_status()["error"] == "oap_data_table_missing"


def test_migration_executes_once_and_checks_parent_and_checksum(monkeypatch):
    from contextlib import contextmanager

    import pytest

    from mission_control import music_oap_data_schema as data

    state = {"parent": True, "checksum": None, "statements": [], "commits": 0}

    class Connection:
        def execute(self, sql, params=None):
            state["statements"].append(sql)
            self.sql = sql
            if sql.startswith("INSERT INTO oap_schema_migrations"):
                state["checksum"] = params[1]
            return self

        def fetchone(self):
            if "SELECT 1 FROM oap_schema_migrations" in self.sql:
                return (1,) if state["parent"] else None
            if "SELECT checksum FROM oap_schema_migrations" in self.sql:
                return (state["checksum"],) if state["checksum"] else None
            return None

        def commit(self):
            state["commits"] += 1

    @contextmanager
    def connect():
        yield Connection()

    monkeypatch.setattr(data.postgres_db, "postgres_status", lambda: {"initialized": True})
    monkeypatch.setattr(data.postgres_db, "connect", connect)

    state["parent"] = False
    with pytest.raises(RuntimeError, match="product-core migration required"):
        data.init_oap_data_schema(assume_yes=True)
    assert not any("CREATE TABLE" in sql for sql in state["statements"])

    state["parent"] = True
    state["statements"].clear()
    data.init_oap_data_schema(assume_yes=True)
    assert sum("CREATE TABLE" in sql for sql in state["statements"]) == 1
    assert state["commits"] == 1

    state["statements"].clear()
    data.init_oap_data_schema(assume_yes=True)
    assert not any("CREATE TABLE" in sql for sql in state["statements"])

    state["checksum"] = "unexpected"
    with pytest.raises(RuntimeError, match="checksum mismatch"):
        data.init_oap_data_schema(assume_yes=True)
