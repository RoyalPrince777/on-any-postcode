"""OAP Commons: real storage boundary, consent and Founder-only queue."""
from __future__ import annotations

import json
import uuid
from contextlib import nullcontext

import pytest

from mission_control import oap_commons as commons
from mission_control import oap_commons_governance as governance


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
            human = governance.review(
                identity, proposal_id, outcome="NOTED",
                reason="Thank you, this has been considered privately.",
            )
            assert human["binding"] is False and human["published"] is False
            reviewed = commons.mine(identity)
            assert any(item["state"] == "REVIEWED"
                       and item["review_outcome"] == "NOTED"
                       for item in reviewed)
            assert not any(item["proposal_id"] == proposal_id
                           for item in commons.founder_queue())
            withdrawn = governance.withdraw(identity, proposal_id)
            assert withdrawn["content_redacted"] is True
            assert not any(item["proposal_id"] == proposal_id
                           for item in commons.mine(identity))
            assert not any(item["proposal_id"] == proposal_id
                           for item in commons.founder_queue())
            redacted = connection.execute(
                """SELECT body,status FROM oap_workspace_records
                   WHERE title=%s""", (commons.PREFIX + proposal_id,),
            ).fetchone()
            assert redacted[1] == "archived"
            assert "Improve local crossings" not in redacted[0]
            receipt = connection.execute(
                """SELECT COUNT(*) FROM audit_events WHERE action IN
                   ('OAP_COMMONS_HUMAN_REVIEW','OAP_COMMONS_CONSENT_WITHDRAWN')
                   AND target=%s""",
                (f"oap_commons:{proposal_id}",),
            ).fetchone()
            assert int(receipt[0]) == 2

            aged = commons.submit(
                identity, title="Old local crossing proposal",
                body="This idea is an expired and private proposal.",
                consent=True,
            )
            connection.execute(
                """UPDATE oap_workspace_records
                   SET created_at=CURRENT_TIMESTAMP - INTERVAL '91 days'
                   WHERE title=%s""", (commons.PREFIX + aged["proposal_id"],),
            )
            assert not any(item["proposal_id"] == aged["proposal_id"]
                           for item in commons.mine(identity))
            swept = governance.erase_expired(identity)
            assert swept["redacted_count"] == 1
            older = connection.execute(
                """SELECT body,status FROM oap_workspace_records
                   WHERE title=%s""", (commons.PREFIX + aged["proposal_id"],),
            ).fetchone()
            assert older[1] == "archived"
            assert "Old local crossing proposal" not in older[0]
            purge_audit = connection.execute(
                """SELECT COUNT(*) FROM audit_events
                   WHERE action='OAP_COMMONS_RETENTION_REDACTED' AND target=%s""",
                (f"oap_commons:{aged['proposal_id']}",),
            ).fetchone()
            assert int(purge_audit[0]) == 1
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


def test_member_withdrawal_requires_csrf_and_owner_auth(client, csrf, monkeypatch):
    seen = []
    monkeypatch.setattr(governance, "withdraw", lambda member, pid:
                        seen.append((member, pid)) or {
                            "proposal_id": pid, "state": "WITHDRAWN",
                            "content_redacted": True,
                        })
    pid = str(uuid.uuid4())
    url = f"/commons/proposals/{pid}/withdraw"
    denied = client.post(url, json={})
    assert denied.status_code == 403
    assert seen == []
    permitted = client.post(url, json={}, headers={
        "X-OAP-CSRF": csrf["csrf_token"],
    })
    assert permitted.status_code == 200
    assert permitted.get_json()["state"] == "WITHDRAWN"
    assert seen[0][0] == "11111111-1111-4111-8111-111111111111"


def test_member_withdrawn_or_foreign_proposal_returns_404(client, csrf, monkeypatch):
    def missing(*args):
        raise ValueError("commons_proposal_not_found")
    monkeypatch.setattr(governance, "withdraw", missing)
    response = client.post(
        f"/commons/proposals/{uuid.uuid4()}/withdraw", json={},
        headers={"X-OAP-CSRF": csrf["csrf_token"]},
    )
    assert response.status_code == 404


def test_anonymous_cannot_withdraw_or_review(anonymous_client):
    assert anonymous_client.post(
        f"/commons/proposals/{uuid.uuid4()}/withdraw",
    ).status_code == 401
    assert anonymous_client.post(
        "/mission/digital-government/commons/review",
    ).status_code == 401


def test_founder_review_requires_csrf_and_human_note(client, csrf, monkeypatch):
    recorded = []
    monkeypatch.setattr(governance, "review", lambda actor, pid, **kw:
                        recorded.append((actor, pid, kw)) or {
                            "proposal_id": pid, "state": "REVIEWED",
                            "binding": False, "published": False,
                        })
    request = {
        "proposal_id": str(uuid.uuid4()), "outcome": "NOTED",
        "reason": "We will consider the submitted idea.",
    }
    assert client.post(
        "/mission/digital-government/commons/review", json=request,
    ).status_code == 403
    assert recorded == []
    good = client.post(
        "/mission/digital-government/commons/review", json=request,
        headers={"X-OAP-CSRF": csrf["csrf_token"]},
    )
    assert good.status_code == 200
    assert good.get_json()["binding"] is False
    assert recorded[0][0] == "11111111-1111-4111-8111-111111111111"


def test_no_fake_judgment_and_nonfounder_gate(client, csrf, monkeypatch):
    from mission_control import web_security

    monkeypatch.setattr(web_security, "private_authority_allowed",
                        lambda _user: False)
    assert client.post(
        "/mission/digital-government/commons/review",
        json={"proposal_id": str(uuid.uuid4()), "outcome": "NOTED",
              "reason": "Private review only"},
        headers={"X-OAP-CSRF": csrf["csrf_token"]},
    ).status_code == 403
    assert client.post(
        "/mission/digital-government/commons/retention",
        json={}, headers={"X-OAP-CSRF": csrf["csrf_token"]},
    ).status_code == 403


def test_invalid_human_outcomes_fail_without_writes():
    with pytest.raises(ValueError, match="invalid_commons_outcome"):
        governance.review(
            str(uuid.uuid4()), str(uuid.uuid4()),
            outcome="PUBLISH", reason="Not legally permitted",
        )
    with pytest.raises(ValueError, match="invalid_retention_limit"):
        governance.erase_expired(str(uuid.uuid4()), limit=1000)


def test_manual_retention_requires_csrf_and_reports_no_scheduler(client, csrf, monkeypatch):
    monkeypatch.setattr(governance, "erase_expired",
                        lambda founder: {"redacted_count": 2,
                                         "automated_scheduler": False})
    assert client.post(
        "/mission/digital-government/commons/retention",
    ).status_code == 403
    res = client.post(
        "/mission/digital-government/commons/retention", json={},
        headers={"X-OAP-CSRF": csrf["csrf_token"]},
    )
    assert res.status_code == 200
    assert res.get_json()["redacted_count"] == 2
    assert res.get_json()["automated_scheduler"] is False
