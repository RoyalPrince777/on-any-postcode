"""Dynamic pressure tests for Koradaso claim review."""
from contextlib import contextmanager
from uuid import uuid4
import pytest
from mission_control import koradaso_reviews

class R:
    def __init__(self, row=None, rows=None):
        self.row, self.rows = row, rows or []
    def fetchone(self): return self.row
    def fetchall(self): return self.rows

class ReviewDB:
    def __init__(self, links=None, fail_audit=False):
        self.links = links or []
        self.fail_audit = fail_audit
        self.committed = False
        self.updated = False
    def execute(self, sql, params=None):
        if "oap_identity_roles" in sql: return R((1,))
        if "SELECT status FROM koradaso_claims" in sql: return R(("RESEARCHING",))
        if "FROM koradaso_claim_evidence" in sql: return R(rows=self.links)
        if "UPDATE koradaso_claims" in sql:
            self.updated = True
            return R()
        if "pg_advisory_xact_lock" in sql: return R()
        if "SELECT curr_hash" in sql: return R(None)
        if "INSERT INTO audit_events" in sql and self.fail_audit:
            raise RuntimeError("audit_failed")
        return R()
    def commit(self): self.committed = True

def wire(monkeypatch, db):
    @contextmanager
    def connect(*args, **kwargs):
        yield db
    monkeypatch.setattr(koradaso_reviews.postgres_db, "connect", connect)

def test_documented_rejects_contradictory_evidence(monkeypatch):
    db = ReviewDB(links=[("SUPPORTS", 1), ("CONTRADICTS", 1)])
    wire(monkeypatch, db)
    with pytest.raises(koradaso_reviews.KoradasoReviewDenied,
                       match="documented_claim_has_contradictory_evidence"):
        koradaso_reviews.review_claim(
            reviewer_id=uuid4(), claim_id=uuid4(),
            to_status="DOCUMENTED", reason="reviewed",
        )
    assert db.updated is False
    assert db.committed is False

def test_review_audit_failure_prevents_commit(monkeypatch):
    db = ReviewDB(links=[("SUPPORTS", 1)], fail_audit=True)
    wire(monkeypatch, db)
    with pytest.raises(RuntimeError, match="audit_failed"):
        koradaso_reviews.review_claim(
            reviewer_id=uuid4(), claim_id=uuid4(),
            to_status="DOCUMENTED", reason="reviewed",
        )
    assert db.updated is True
    assert db.committed is False
