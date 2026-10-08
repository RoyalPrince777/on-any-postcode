"""Fail-closed consent transaction tests with audit failure injection.

These tests prove no application commit is attempted; PostgreSQL rollback and
concurrent transaction behaviour require separate database-backed tests.
"""
from contextlib import contextmanager
from uuid import uuid4

import pytest

from mission_control import koradaso_publications, koradaso_releases


class Result:
    def __init__(self, row=None):
        self.row = row

    def fetchone(self):
        return self.row


class AuditFailureConnection:
    def __init__(self, actor, claim, release):
        self.actor = actor
        self.claim = claim
        self.release = release
        self.committed = False
        self.queries = []

    def execute(self, sql, params=None):
        self.queries.append(sql)
        if "FROM oap_identity_roles" in sql:
            return Result((1,))
        if "FROM koradaso_claims WHERE claim_id=%s FOR UPDATE" in sql:
            if "privacy_scope,created_by" in sql:
                return Result(("ME", self.actor))
            return Result(("DOCUMENTED", "ME"))
        if "FROM koradaso_claim_reviews" in sql:
            return Result((1,))
        if "FROM koradaso_release_consents" in sql:
            if "summary_hash=%s" in sql:
                return Result((self.release,))
            if "WHERE release_id=%s FOR UPDATE" in sql:
                return Result((self.claim, None, self.actor))
            if "WHERE release_id=%s" in sql:
                return Result((self.claim,))
            return Result(None)
        if "INSERT INTO audit_events" in sql:
            raise RuntimeError("audit_failed")
        return Result()

    def commit(self):
        self.committed = True


@pytest.mark.parametrize("operation", ["grant", "publish", "revoke"])
def test_consent_operations_do_not_commit_when_audit_fails(monkeypatch, operation):
    actor, claim, release = uuid4(), uuid4(), uuid4()
    db = AuditFailureConnection(actor, claim, release)

    @contextmanager
    def connect(*args, **kwargs):
        yield db

    monkeypatch.setattr(koradaso_releases.postgres_db, "connect", connect)
    monkeypatch.setattr(koradaso_releases, "_audit", lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("audit_failed")))
    monkeypatch.setattr(koradaso_publications, "_audit", lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("audit_failed")))
    monkeypatch.setattr(koradaso_releases, "claim_fingerprint", lambda *a: "fingerprint")
    monkeypatch.setattr(koradaso_publications, "claim_fingerprint", lambda *a: "fingerprint")

    with pytest.raises(RuntimeError, match="audit_failed"):
        if operation == "grant":
            koradaso_releases.grant_release(
                actor_id=actor, claim_id=claim, reason="approved",
                public_summary="reviewed summary",
            )
        elif operation == "publish":
            koradaso_publications.publish_claim(
                publisher_id=actor, claim_id=claim, public_summary="reviewed summary",
            )
        else:
            koradaso_releases.revoke_release(
                actor_id=actor, release_id=release, reason="withdrawn",
            )

    assert not db.committed
    assert any(
        ("INSERT INTO koradaso_" in query or "UPDATE koradaso_" in query)
        for query in db.queries
    )
