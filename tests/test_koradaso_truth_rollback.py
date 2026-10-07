"""Rollback proof for Koradaso truth auditing."""
from contextlib import contextmanager
from uuid import uuid4

import pytest

from mission_control import koradaso_evidence

class R:
    def __init__(self, row=None):
        self.row = row
    def fetchone(self):
        return self.row

class BrokenAuditDB:
    def __init__(self):
        self.committed = False
    def execute(self, sql, params=None):
        if "oap_identity_roles" in sql:
            return R((1,))
        if "pg_advisory_xact_lock" in sql:
            return R()
        if "SELECT curr_hash" in sql:
            return R(None)
        if "INSERT INTO audit_events" in sql:
            raise RuntimeError("audit_failed")
        return R()
    def commit(self):
        self.committed = True

def test_evidence_is_not_committed_when_audit_fails(monkeypatch):
    db = BrokenAuditDB()
    @contextmanager
    def connect(*args, **kwargs):
        yield db
    monkeypatch.setattr(koradaso_evidence.postgres_db, "connect", connect)
    with pytest.raises(RuntimeError, match="audit_failed"):
        koradaso_evidence.record_evidence(
            actor_id=uuid4(),
            evidence_type="TEST",
            title="Test evidence",
            original_bytes=b"evidence",
            original_language="TWI",
            privacy_scope="ROYAL_HOUSE",
        )
    assert db.committed is False


def test_claim_is_not_committed_when_audit_fails(monkeypatch):
    db = BrokenAuditDB()
    @contextmanager
    def connect(*args, **kwargs):
        yield db
    monkeypatch.setattr(koradaso_evidence.postgres_db, "connect", connect)
    with pytest.raises(RuntimeError, match="audit_failed"):
        koradaso_evidence.record_claim(
            actor_id=uuid4(),
            subject_kind="PERSON",
            subject_ref="test-person",
            predicate="related_to",
            object_value="test-record",
            status="RESEARCHING",
            confidence=0.5,
            privacy_scope="FAMILY",
        )
    assert db.committed is False


class LinkAuditFailDB(BrokenAuditDB):
    def execute(self, sql, params=None):
        if "oap_identity_roles" in sql:
            return R((1,))
        if "FROM koradaso_claims c CROSS JOIN koradaso_evidence e" in sql:
            return R(("FAMILY", "FAMILY"))
        if "pg_advisory_xact_lock" in sql:
            return R()
        if "SELECT curr_hash" in sql:
            return R(None)
        if "INSERT INTO audit_events" in sql:
            raise RuntimeError("audit_failed")
        return R()

def test_link_is_not_committed_when_audit_fails(monkeypatch):
    db = LinkAuditFailDB()
    @contextmanager
    def connect(*args, **kwargs):
        yield db
    monkeypatch.setattr(koradaso_evidence.postgres_db, "connect", connect)
    with pytest.raises(RuntimeError, match="audit_failed"):
        koradaso_evidence.link_evidence(
            actor_id=uuid4(), claim_id=uuid4(), evidence_id=uuid4(),
            relation="SUPPORTS",
        )
    assert db.committed is False

class VersionAuditFailDB(BrokenAuditDB):
    def execute(self, sql, params=None):
        if "oap_identity_roles" in sql:
            return R((1,))
        if "SELECT evidence_id FROM koradaso_evidence" in sql:
            return R((uuid4(),))
        if "COALESCE(MAX(version_number),0)" in sql:
            return R((1,))
        if "pg_advisory_xact_lock" in sql:
            return R()
        if "SELECT curr_hash" in sql:
            return R(None)
        if "INSERT INTO audit_events" in sql:
            raise RuntimeError("audit_failed")
        return R()

def test_version_is_not_committed_when_audit_fails(monkeypatch):
    db = VersionAuditFailDB()
    @contextmanager
    def connect(*args, **kwargs):
        yield db
    monkeypatch.setattr(koradaso_evidence.postgres_db, "connect", connect)
    with pytest.raises(RuntimeError, match="audit_failed"):
        koradaso_evidence.append_evidence_version(
            actor_id=uuid4(), evidence_id=uuid4(),
            content_bytes=b"translation", change_kind="TRANSLATION",
            language="EN",
        )
    assert db.committed is False

class DeniedDB(BrokenAuditDB):
    def __init__(self):
        super().__init__()
        self.truth_write_seen = False
    def execute(self, sql, params=None):
        if "oap_identity_roles" in sql:
            return R(None)
        if "INSERT INTO koradaso_" in sql:
            self.truth_write_seen = True
        return R()

def test_permission_denial_happens_before_truth_write(monkeypatch):
    db = DeniedDB()
    @contextmanager
    def connect(*args, **kwargs):
        yield db
    monkeypatch.setattr(koradaso_evidence.postgres_db, "connect", connect)
    with pytest.raises(koradaso_evidence.KoradasoEvidenceDenied):
        koradaso_evidence.record_claim(
            actor_id=uuid4(), subject_kind="PERSON", subject_ref="x",
            predicate="related_to", object_value="y", status="RESEARCHING",
            confidence=0.2, privacy_scope="FAMILY",
        )
    assert db.truth_write_seen is False
    assert db.committed is False
