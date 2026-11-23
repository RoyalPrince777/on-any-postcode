"""Gate-25 Koradaso schema contract tests; database operations use fakes."""
from __future__ import annotations

from contextlib import contextmanager

import pytest

from mission_control import koradaso_schema, postgres_db


class Result:
    def __init__(self, value):
        self.value = value
    def fetchone(self):
        return (self.value,)


class Connection:
    def __init__(self, present=()):
        self.present = set(present)
        self.commands = []
        self.committed = False
    def execute(self, sql, params=None):
        self.commands.append((sql, params))
        if sql.startswith("SELECT to_regclass"):
            name = params[0].removeprefix("public.")
            return Result(name if name in self.present else None)
        if sql.startswith("CREATE TABLE IF NOT EXISTS"):
            name = sql.split()[5]
            self.present.add(name)
        return Result(1)
    def commit(self):
        self.committed = True


def attach(monkeypatch, connection):
    @contextmanager
    def connect(*, readonly=False):
        yield connection
    monkeypatch.setattr(postgres_db, "connect", connect)


def test_requires_explicit_confirmation_and_dry_run_does_not_connect(monkeypatch):
    def forbidden(*, readonly=False):
        raise AssertionError("unexpected database connection")
    monkeypatch.setattr(postgres_db, "connect", forbidden)
    with pytest.raises(RuntimeError, match="explicit_confirmation_required"):
        koradaso_schema.install()
    result = koradaso_schema.install(assume_yes=True, dry_run=True)
    assert result["dry_run"] is True
    assert result["schema_ready"] is False
    assert len(result["checksum"]) == 64


def test_refuses_install_without_canonical_identity_and_audit(monkeypatch):
    connection = Connection()
    attach(monkeypatch, connection)
    with pytest.raises(koradaso_schema.KoradasoSchemaUnavailable,
                       match="koradaso_schema_prerequisites_missing"):
        koradaso_schema.install(assume_yes=True)
    assert connection.committed is False
    assert not any(sql.startswith("CREATE TABLE") for sql, _ in connection.commands)


def test_install_reuses_oap_foundations_and_readback_is_truthful(monkeypatch):
    connection = Connection(koradaso_schema.PREREQUISITES)
    attach(monkeypatch, connection)
    result = koradaso_schema.install(assume_yes=True)
    assert connection.committed is True
    assert result["schema_ready"] is True
    assert result["prerequisites_ready"] is True
    assert result["royal_status_granted"] is False
    assert result["invite_issued"] is False
    assert result["evidence_published"] is False
    assert result["sika_issued"] is False


def test_schema_keeps_royal_access_claims_and_evidence_separate():
    sql = "\n".join(koradaso_schema.STATEMENTS)
    assert "koradaso_claims" in sql
    assert "koradaso_claim_evidence" in sql
    assert "SUPPORTS" in sql and "CONTRADICTS" in sql
    assert "koradaso_invites" in sql
    assert "token_hash TEXT NOT NULL UNIQUE" in sql
    assert "royal_status" not in sql.lower()
    assert "balance" not in sql.lower()


def test_relationships_are_typed_temporal_and_evidence_linkable():
    sql = "\n".join(koradaso_schema.STATEMENTS)
    assert "relationship_type TEXT NOT NULL" in sql
    assert "valid_from DATE" in sql
    assert "valid_until DATE" in sql
    assert "claim_id UUID REFERENCES koradaso_claims" in sql


def test_privacy_scopes_are_bounded():
    sql = "\n".join(koradaso_schema.STATEMENTS)
    for scope in ("ME", "ROYAL_HOUSE", "FAMILY", "COMMUNITY", "PUBLIC"):
        assert scope in sql
