"""Authenticated SMI Mail acceptance through Flask route and read-only SQL.

This uses the application's signed-in test session and a fake PostgreSQL
connection: no live database, migration or message delivery.
"""
from __future__ import annotations

from contextlib import contextmanager

from mission_control import postgres_db

OWNER = "11111111-1111-4111-8111-111111111111"


class _SubjectConnection:
    def __init__(self):
        self.queries = []
        self.readonly = None
        self.committed = False

    def execute(self, sql, params):
        self.queries.append((sql, params))
        return self

    def fetchall(self):
        return [("<private subject>", "member@example.test")]

    def commit(self):
        self.committed = True
        raise AssertionError("read-only Mail acceptance must never commit")


def test_authenticated_smi_page_to_subject_only_mail_route(client, csrf, monkeypatch):
    db = _SubjectConnection()
    opens = []

    @contextmanager
    def fake_connect(*, readonly=False):
        opens.append(readonly)
        db.readonly = readonly
        yield db

    monkeypatch.setattr(postgres_db, "connect", fake_connect)
    page = client.get("/mission/ollama")
    assert page.status_code == 200
    assert page.headers["Cache-Control"] == "no-store"
    html = page.get_data(as_text=True)
    assert "smi_mail_read_control.js" in html
    assert "oap-mail-read-inbox" in html or "smi_mail_read_control.js" in html
    assert "/mission/chat/tools/mail/read" in html
    assert opens == []

    payload = {"folder": "inbox", "owner_consent": True, "ability": "mail.read"}
    route = "/mission/chat/tools/mail/read"
    accepted = client.post(
        route, json=payload,
        headers={"X-OAP-CSRF": csrf["csrf_token"]},
    )
    assert accepted.status_code == 200
    assert accepted.headers["Cache-Control"] == "no-store"
    assert accepted.headers["X-Content-Type-Options"] == "nosniff"
    result = accepted.get_json()
    assert result["items"] == [{
        "subject": "<private subject>",
        "correspondent": "member@example.test",
    }]
    assert result["execute"] is False
    assert result["delivery_enabled"] is False
    assert result["production_approved"] is False
    assert opens == [True]
    assert db.readonly is True
    assert db.committed is False
    assert len(db.queries) == 1
    sql, params = db.queries[0]
    assert sql.split("FROM oap_mail_items", 1)[0].strip() == (
        "SELECT subject,correspondent"
    )
    assert "WHERE owner_id=%s AND folder=%s" in sql
    assert "ORDER BY created_at DESC,id DESC LIMIT 50" in sql
    assert params == (OWNER, "inbox")
    for sensitive in ("body", "created_at", "message_id", "password"):
        assert sensitive not in str(result).lower()

    # Successful one-call consent must not be stored or reused.
    denied = client.post(
        route, json={"folder": "inbox"},
        headers={"X-OAP-CSRF": csrf["csrf_token"]},
    )
    assert denied.status_code == 403
    assert denied.get_json()["error"]["code"] == "mail_smi_access_denied"
    assert opens == [True]
    assert len(db.queries) == 1


def test_authenticated_smi_mail_denials_before_database_open(
    client, csrf, monkeypatch,
):
    calls = []

    @contextmanager
    def forbidden_connect(*, readonly=False):
        calls.append(readonly)
        raise AssertionError("denied Mail access must not open a database")
        yield

    monkeypatch.setattr(postgres_db, "connect", forbidden_connect)
    path = "/mission/chat/tools/mail/read"
    payload = {"folder": "inbox", "owner_consent": True}

    missing_csrf = client.post(path, json=payload)
    assert missing_csrf.status_code == 403
    for extra in (
        {"owner_id": "22222222-2222-4222-8222-222222222222"},
        {"ability": "mail.send"},
        {"folder": "../inbox"},
    ):
        response = client.post(
            path, json={**payload, **extra},
            headers={"X-OAP-CSRF": csrf["csrf_token"]},
        )
        assert response.status_code in (400, 403)
    assert calls == []
