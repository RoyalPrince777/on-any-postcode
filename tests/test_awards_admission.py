"""CC21X real admission, auth, CSRF, SQL ownership and retry regressions."""
from uuid import uuid4

import pytest
from flask import Flask

from mission_control import awards_admission, product_core_views, web_security

OWNER = str(uuid4())
NOMINATION_ID = str(uuid4())
GOOD = {
    "nominee_name": "Artist Example",
    "award_type": "Music",
    "achievement_date": "2020-02-29",
    "evidence_reference": "catalogue:independent-1",
    "idempotency_key": "nomination:example-001",
}


class Result:
    def __init__(self, row):
        self.row = row

    def fetchone(self):
        return self.row


class Connection:
    def __init__(self, *, duplicate=False, conflicting=False):
        self.duplicate = duplicate
        self.conflicting = conflicting
        self.calls = []
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, sql, params=()):
        self.calls.append((sql, params))
        if "INSERT INTO oap_award_nominations" in sql:
            return Result(None if self.duplicate else (NOMINATION_ID,))
        if "SELECT nomination_id" in sql:
            return Result((
                NOMINATION_ID, 2020, 2029,
                "Another Artist" if self.conflicting else GOOD["nominee_name"],
                GOOD["award_type"], GOOD["achievement_date"], GOOD["evidence_reference"],
            ))
        return Result(None)

    def commit(self):
        self.committed = True


def test_explicit_migration_only(monkeypatch):
    with pytest.raises(PermissionError):
        awards_admission.init_schema()
    conn = Connection()
    monkeypatch.setattr(awards_admission.postgres_db, "connect", lambda: conn)
    awards_admission.init_schema(assume_yes=True)
    assert conn.committed
    assert len(conn.calls) == len(awards_admission.SCHEMA_STATEMENTS)
    assert "UNIQUE(owner_identity_id,award_program,idempotency_key)" in awards_admission.SCHEMA_STATEMENTS[0]
    assert "CHECK (status = 'PENDING_REVIEW')" in awards_admission.SCHEMA_STATEMENTS[0]


def test_decade_must_be_explicit(monkeypatch):
    monkeypatch.delenv("OAP_AWARDS_DECADE_FIRST_YEAR", raising=False)
    with pytest.raises(RuntimeError, match="awards_decade_not_approved"):
        awards_admission.configured_decade()
    monkeypatch.setenv("OAP_AWARDS_DECADE_FIRST_YEAR", "2020")
    assert awards_admission.configured_decade() == (2020, 2029)


def test_invalid_nomination_never_opens_store(monkeypatch):
    monkeypatch.setenv("OAP_AWARDS_DECADE_FIRST_YEAR", "2020")
    monkeypatch.setattr(awards_admission.postgres_db, "connect",
                        lambda: pytest.fail("invalid nomination must not touch DB"))
    with pytest.raises(ValueError, match="outside_decade"):
        awards_admission.submit_nomination(
            {**GOOD, "achievement_date": "2019-12-31"}, owner_identity_id=OWNER,
        )
    with pytest.raises(ValueError, match="invalid_idempotency_key"):
        awards_admission.submit_nomination(
            {**GOOD, "idempotency_key": "x"}, owner_identity_id=OWNER,
        )


def test_insert_is_owner_scoped_and_pending_only(monkeypatch):
    monkeypatch.setenv("OAP_AWARDS_DECADE_FIRST_YEAR", "2020")
    conn = Connection()
    monkeypatch.setattr(awards_admission.postgres_db, "connect", lambda: conn)
    result = awards_admission.submit_nomination(GOOD, owner_identity_id=OWNER)
    assert result["status"] == "PENDING_REVIEW"
    assert result["evidence_verified"] is False
    assert result["voting_enabled"] is False
    assert result["winner_declared"] is False
    assert conn.committed
    assert OWNER == conn.calls[0][1][0]
    assert "ON CONFLICT (owner_identity_id,award_program,idempotency_key)" in conn.calls[0][0]


def test_identical_retry_and_changed_payload_conflict(monkeypatch):
    monkeypatch.setenv("OAP_AWARDS_DECADE_FIRST_YEAR", "2020")
    duplicate = Connection(duplicate=True)
    monkeypatch.setattr(awards_admission.postgres_db, "connect", lambda: duplicate)
    assert awards_admission.submit_nomination(GOOD, owner_identity_id=OWNER)["nomination_id"] == NOMINATION_ID
    assert duplicate.committed
    conflict = Connection(duplicate=True, conflicting=True)
    monkeypatch.setattr(awards_admission.postgres_db, "connect", lambda: conflict)
    with pytest.raises(ValueError, match="idempotency_conflict"):
        awards_admission.submit_nomination(GOOD, owner_identity_id=OWNER)
    assert not conflict.committed


def test_private_route_denies_anonymous_and_missing_csrf(monkeypatch):
    app = Flask(__name__)
    app.secret_key = "test-only"
    app.register_blueprint(product_core_views.bp, url_prefix="/mission/organs")
    route = "/mission/organs/awards/best-of-the-decade/nominations"
    client = app.test_client()
    monkeypatch.setattr(web_security, "current_authenticated_user", lambda: None)
    assert client.post(route, json=GOOD).status_code == 401
    monkeypatch.setattr(web_security, "current_authenticated_user",
                        lambda: {"id": OWNER, "email_verified": True})
    monkeypatch.setattr(web_security, "private_authority_allowed", lambda _user: True)
    assert client.post(route, json=GOOD).status_code == 403


def test_authenticated_csrf_post_remains_pending(monkeypatch):
    app = Flask(__name__)
    app.secret_key = "test-only"
    app.register_blueprint(product_core_views.bp, url_prefix="/mission/organs")
    monkeypatch.setattr(web_security, "current_authenticated_user",
                        lambda: {"id": OWNER, "email_verified": True})
    monkeypatch.setattr(web_security, "private_authority_allowed", lambda _user: True)
    monkeypatch.setattr(product_core_views, "_identity", lambda *, sync=False: OWNER)
    monkeypatch.setenv("OAP_AWARDS_DECADE_FIRST_YEAR", "2020")
    conn = Connection()
    monkeypatch.setattr(awards_admission.postgres_db, "connect", lambda: conn)
    client = app.test_client()
    with client.session_transaction() as sess:
        sess[web_security.CSRF_SESSION_KEY] = "x" * 40
    response = client.post(
        "/mission/organs/awards/best-of-the-decade/nominations",
        json=GOOD, headers={"X-OAP-CSRF": "x" * 40},
    )
    assert response.status_code == 201
    assert response.get_json()["status"] == "PENDING_REVIEW"
    assert response.headers["Cache-Control"] == "no-store"
    assert conn.committed
