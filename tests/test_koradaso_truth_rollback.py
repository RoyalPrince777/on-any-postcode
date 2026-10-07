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
