"""OAP Commons: real storage boundary, consent and Founder-only queue."""
from __future__ import annotations

import json
import uuid
from contextlib import nullcontext

import pytest

from mission_control import oap_commons as commons


def test_explicit_consent_is_required_and_fields_are_bounded():
    with pytest.raises(ValueError, match="explicit_commons_consent_required"):
        commons.validate_proposal("Local transport", "Please improve bus stops", False)
    with pytest.raises(ValueError, match="invalid_proposal_text"):
        commons.validate_proposal("Bad", "Meaningful proposal content long enough", True)
    with pytest.raises(ValueError, match="invalid_proposal_text"):
        commons.validate_proposal("Good proposal", "short", True)
    with pytest.raises(ValueError, match="invalid_proposal_text"):
        commons.validate_proposal("Valid idea", "x" * 1201, True)
    valid = commons.validate_proposal(
        " Fair local services ", " More public community discussion please. ", True
    )
    assert valid == {
        "title": "Fair local services",
        "body": "More public community discussion please.",
    }


def test_malformed_or_unconsented_rows_do_not_render():
    from datetime import UTC, datetime

    item_id = str(uuid.uuid4())
    row = (str(uuid.uuid4()), commons.PREFIX + item_id, json.dumps({
        "title": "Safer crossings", "body": "We want better crossing visibility.",
        "consent_to_private_review": True, "state": "PENDING_FOUNDER_REVIEW",
        "published": False,
    }), datetime.now(UTC))
    good = commons._safe_record(row)
    assert good is not None
    assert good["proposal_id"] == item_id
    assert good["published"] is False
    unconsented = json.dumps({"title": "a", "body": "b", "published": False})
    assert commons._safe_record((row[0], row[1], unconsented, row[3])) is None
    assert commons._safe_record((row[0], "OAP-OTHER", row[2], row[3])) is None


def test_member_page_and_private_route_need_login(anonymous_client):
    assert anonymous_client.get("/commons").status_code == 302
    assert anonymous_client.post("/commons/proposals").status_code == 401
    assert anonymous_client.get("/commons/status").status_code == 401


def test_member_submit_fails_closed_without_csrf(client, monkeypatch):
    monkeypatch.setattr(commons, "submit", lambda *a, **k: pytest.fail("must not submit"))
    response = client.post("/commons/proposals", json={
        "title": "Local improvements", "body": "Better neighbourhood services please.",
        "consent": True,
    })
    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "csrf_failed"


def test_member_can_only_submit_with_valid_consent(client, csrf, monkeypatch):
    from mission_control import oap_commons_routes

    seen = []
    monkeypatch.setattr(oap_commons_routes.public_store,
                        "ensure_authenticated_user", lambda *a, **k: None)
    monkeypatch.setattr(commons, "submit", lambda identity, **data:
                        seen.append((identity, data)) or {
                            "state": "PENDING_FOUNDER_REVIEW", "published": False,
                        })
    missing = client.post("/commons/proposals", json={
        "title": "Improve local spaces",
        "body": "We would like better accessible playgrounds.",
        "consent": False,
    }, headers={"X-OAP-CSRF": csrf["csrf_token"]})
    assert missing.status_code == 400
    assert seen == []
    valid = client.post("/commons/proposals", json={
        "title": "Improve local spaces",
        "body": "We would like better accessible playgrounds.",
        "consent": True,
    }, headers={"X-OAP-CSRF": csrf["csrf_token"]})
    assert valid.status_code == 201
    assert valid.get_json()["state"] == "PENDING_FOUNDER_REVIEW"
    assert len(seen) == 1
    assert seen[0][0] == "11111111-1111-4111-8111-111111111111"


def test_member_own_page_is_owner_scoped(client, monkeypatch):
    requested = []
    def only_mine(identity, **kwargs):
        requested.append(identity)
        return ()
    monkeypatch.setattr(commons, "mine", only_mine)
    page = client.get("/commons")
    assert page.status_code == 200
    assert "OAP Commons" in page.get_data(as_text=True)
    assert "Submit privately" in page.get_data(as_text=True)
    assert requested == ["11111111-1111-4111-8111-111111111111"]


def test_founder_queue_is_privately_gated(client, monkeypatch):
    monkeypatch.setattr(commons, "founder_queue", lambda: ())
    r = client.get("/mission/digital-government/commons/queue")
    assert r.status_code == 200
    assert "no-store" in r.headers["Cache-Control"]
    assert "Commons Review Inbox" in r.get_data(as_text=True)
    assert client.post("/mission/digital-government/commons/queue").status_code == 405


def test_anonymous_founder_queue_never_reveals_proposals(anonymous_client):
    response = anonymous_client.get("/mission/digital-government/commons/queue")
    assert response.status_code == 302


def test_nonfounder_queue_denied(client, monkeypatch):
    from mission_control import web_security

    monkeypatch.setattr(web_security, "private_authority_allowed",
                        lambda _user: False)
    response = client.get("/mission/digital-government/commons/queue")
    assert response.status_code == 403
    assert "Commons Review Inbox" not in response.get_data(as_text=True)


def test_founder_queue_store_failure_denied(client, monkeypatch):
    def fail():
        raise commons.CommonsUnavailable("unavailable")
    monkeypatch.setattr(commons, "founder_queue", fail)
    response = client.get("/mission/digital-government/commons/queue")
    assert response.status_code == 503
    assert "Commons Review Inbox" not in response.get_data(as_text=True)


def test_canonical_postgres_real_transactional_proposal_and_audit(monkeypatch):
    """No fake DB: verify the actual SQL in a rollback-only PostgreSQL transaction."""
    from mission_control import postgres_db

    if not postgres_db.configured():
        pytest.skip("PostgreSQL not configured for real transactional check")

    original = postgres_db.connect
    with original() as connection:
        identity = str(uuid.uuid4())
        connection.execute(
            """INSERT INTO users(id,username,email,display_name,status)
               VALUES (%s,%s,NULL,'OAP Commons test','active')""",
            (identity, "commons_test_" + identity.replace("-", "")),
        )
        class RollbackOnly:
            def execute(self, *args, **kwargs):
                return connection.execute(*args, **kwargs)
            def commit(self):
                pass
        monkeypatch.setattr(commons.postgres_db, "connect",
                            lambda **_kwargs: nullcontext(RollbackOnly()))
        try:
            created = commons.submit(
                identity, title="Improve local crossings",
                body="Install better accessible pedestrian crossings.",
                consent=True,
            )
            proposal_id = created["proposal_id"]
            saved = commons.mine(identity)
            queue = commons.founder_queue()
            assert any(item["proposal_id"] == proposal_id for item in saved)
            assert any(item["proposal_id"] == proposal_id for item in queue)
            audit = connection.execute(
                """SELECT COUNT(*) FROM audit_events WHERE action=%s
                   AND target=%s AND actor_id=%s""",
                ("OAP_COMMONS_PROPOSAL_RECEIVED", f"oap_commons:{proposal_id}", identity),
            ).fetchone()
            assert audit == (1,)
            assert created["published"] is False
            assert created["voting_enabled"] is False
        finally:
            connection.rollback()


def test_commons_status_has_no_fake_public_votes(monkeypatch):
    monkeypatch.setattr(commons.postgres_db, "connect",
                        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("offline")))
    status = commons.status()
    assert status["schema_ready"] is False
    assert status["public_voting_enabled"] is False
    assert status["automatic_decisions"] is False
    assert status["production_vpi_percent"] is None
