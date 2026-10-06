"""Governed OAP Library ebook schema installer tests."""

from contextlib import contextmanager

import pytest

from mission_control import oap_library_ebook_schema as schema


class FakeConnection:
    def __init__(self, present):
        self.present = set(present)
        self.calls = []
        self.committed = False
        self.last_name = None

    def execute(self, sql, parameters=None):
        self.calls.append((sql, parameters))
        if sql.startswith("SELECT to_regclass"):
            self.last_name = str(parameters[0]).removeprefix("public.")
        elif sql.startswith("CREATE TABLE IF NOT EXISTS"):
            marker = sql.split("CREATE TABLE IF NOT EXISTS", 1)[1].strip().split()[0]
            self.present.add(marker)
        return self

    def fetchone(self):
        if self.last_name is not None:
            value = self.last_name if self.last_name in self.present else None
            self.last_name = None
            return (value,)
        return None

    def commit(self):
        self.committed = True


def wire(monkeypatch, connection):
    @contextmanager
    def connect(*, readonly=False):
        yield connection

    monkeypatch.setattr(schema.postgres_db, "connect", connect)


def test_dry_run_does_not_touch_database(monkeypatch):
    def forbidden(*, readonly=False):
        raise AssertionError("database_must_not_be_opened")

    monkeypatch.setattr(schema.postgres_db, "connect", forbidden)
    result = schema.install(assume_yes=True, dry_run=True)
    assert result["dry_run"] is True
    assert result["schema_ready"] is False
    assert result["payment_capture_performed"] is False
    assert result["ownership_created"] is False


def test_install_requires_explicit_approval():
    with pytest.raises(RuntimeError, match="explicit_confirmation_required"):
        schema.install()


def test_install_fails_closed_when_prerequisite_missing(monkeypatch):
    present = set(schema._PREREQUISITES) - {"products"}
    connection = FakeConnection(present)
    wire(monkeypatch, connection)

    with pytest.raises(
        schema.LibraryEbookSchemaUnavailable,
        match="library_ebook_schema_prerequisites_missing:products",
    ):
        schema.install(assume_yes=True)

    assert connection.committed is False


def test_install_creates_only_schema_and_reads_back(monkeypatch):
    connection = FakeConnection(set(schema._PREREQUISITES))
    wire(monkeypatch, connection)

    result = schema.install(assume_yes=True)

    assert result["schema_ready"] is True
    assert result["prerequisites_ready"] is True
    assert result["member_rows_read"] is False
    assert result["payment_rows_read"] is False
    assert result["payment_capture_performed"] is False
    assert result["ownership_created"] is False
    assert connection.committed is True
    sql = "\n".join(call[0] for call in connection.calls)
    assert "INSERT INTO" not in sql
    assert "UPDATE " not in sql
    for table in schema._REQUIRED_TABLES:
        assert table in connection.present
