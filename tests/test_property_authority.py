"""Property grant reads: no migration, writes or external publication."""
import uuid
from contextlib import contextmanager
from pathlib import Path

from mission_control import property_authority as grants


def record():
    return {
        "publisher_id": str(uuid.uuid4()),
        "advertiser_id": str(uuid.uuid4()),
        "property_ref": "partner-property-1",
        "country": "United Kingdom",
    }


def test_scoped_active_grant_and_current_reviewer_required(monkeypatch):
    item = record()
    evidence_id = str(uuid.uuid4())
    reviewer = str(uuid.uuid4())
    calls = []
    class Connection:
        def execute(self, query, params):
            calls.append((query, params))
            return self
        def fetchone(self):
            return (reviewer,)
    @contextmanager
    def connect(*, readonly):
        assert readonly is True
        yield Connection()
    def require(connection, actor):
        assert actor == reviewer
        calls.append(("authority", actor))
        return {"is_human_authority": True}
    monkeypatch.setattr(grants.postgres_db, "connect", connect)
    monkeypatch.setattr(grants.authority, "require_human_authority", require)
    assert grants.verified_advertising_authority(item, evidence_id) is True
    sql, params = calls[0]
    assert params == (evidence_id, item["publisher_id"], item["advertiser_id"],
                      item["property_ref"], item["country"])
    for fragment in ("status='ACTIVE'", "revoked_at IS NULL",
                     "valid_until>CURRENT_TIMESTAMP", "activity='ADVERTISE'",
                     "reviewed_by<>publisher_id"):
        assert fragment in sql
    assert calls[1] == ("authority", reviewer)


def test_missing_grant_or_revoked_reviewer_denied(monkeypatch):
    item = record()
    evidence_id = str(uuid.uuid4())
    class Connection:
        def execute(self, query, params):
            return self
        def fetchone(self):
            return None
    @contextmanager
    def connect(*, readonly):
        yield Connection()
    monkeypatch.setattr(grants.postgres_db, "connect", connect)
    assert grants.verified_advertising_authority(item, evidence_id) is False

    reviewer = str(uuid.uuid4())
    class Found(Connection):
        def fetchone(self):
            return (reviewer,)
    @contextmanager
    def found(*, readonly):
        yield Found()
    monkeypatch.setattr(grants.postgres_db, "connect", found)
    def revoked(*_):
        raise grants.authority.HumanAuthorityRequired("revoked")
    monkeypatch.setattr(grants.authority, "require_human_authority", revoked)
    assert grants.verified_advertising_authority(item, evidence_id) is False


def test_invalid_identity_or_missing_schema_denied(monkeypatch):
    item = record()
    assert grants.verified_advertising_authority(item, "self-attested") is False
    assert grants.verified_advertising_authority({**item, "publisher_id": "bad"},
                                                 str(uuid.uuid4())) is False
    def offline(*, readonly):
        raise RuntimeError("table not migrated or database unavailable")
    monkeypatch.setattr(grants.postgres_db, "connect", offline)
    assert grants.verified_advertising_authority(item, str(uuid.uuid4())) is False


def test_migration_is_explicit_and_uses_shared_identity_tables():
    ddl = Path("migrations/0009_oap_property_advertising_authority.sql").read_text()
    assert "CREATE TABLE IF NOT EXISTS oap_property_advertising_authority" in ddl
    assert "REFERENCES oap_identities(identity_id)" in ddl
    assert "REVIEW_REQUIRED" in ddl and "REVOKED" in ddl
    assert "CHECK (publisher_id <> reviewed_by)" in ddl
