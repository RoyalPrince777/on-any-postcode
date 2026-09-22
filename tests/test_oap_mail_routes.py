"""OAP Mail routes: authenticated, owner-scoped, no delivery or public projections."""
from __future__ import annotations

import uuid

from mission_control import mail_store, public_store


def test_mail_folder_get_is_owner_scoped_and_no_store(client, monkeypatch):
    calls = []
    def list_items(actor, owner, folder):
        calls.append((actor, owner, folder))
        return []
    monkeypatch.setattr(mail_store, "list_items", list_items)
    response = client.get("/mail/inbox")
    assert response.status_code == 200
    assert response.get_json() == {"items": [], "delivery_enabled": False}
    assert response.headers["Cache-Control"] == "no-store"
    assert calls and calls[0][0] == calls[0][1]
    assert calls[0][2] == "inbox"


def test_mail_invalid_folder_does_not_read_store(client, monkeypatch):
    calls = []
    monkeypatch.setattr(mail_store, "list_items",
                        lambda *_: calls.append(True))
    response = client.get("/mail/not-a-mailbox")
    assert response.status_code == 400
    assert calls == []


def test_mail_unavailable_fails_closed(client, monkeypatch):
    def unavailable(*_args):
        raise mail_store.MailUnavailable("private-detail")
    monkeypatch.setattr(mail_store, "list_items", unavailable)
    response = client.get("/mail/inbox")
    assert response.status_code == 503
    assert "private-detail" not in response.get_data(as_text=True)


def test_draft_requires_csrf(client, monkeypatch):
    called = []
    monkeypatch.setattr(mail_store, "save_draft",
                        lambda *_args, **_kwargs: called.append(True))
    response = client.post("/mail/drafts", json={"body": "private"})
    assert response.status_code == 403
    assert called == []


def test_draft_write_returns_unsent_receipt(client, csrf, monkeypatch):
    draft_id = str(uuid.uuid4())
    calls = []
    monkeypatch.setattr(public_store, "ensure_authenticated_user",
                        lambda *_args, **_kwargs: None)
    def save(actor, owner, **fields):
        calls.append((actor, owner, fields))
        return draft_id
    monkeypatch.setattr(mail_store, "save_draft", save)
    response = client.post(
        "/mail/drafts",
        json={"subject": "Private", "body": "Unsent"},
        headers={"X-OAP-CSRF": csrf["csrf_token"]},
    )
    assert response.status_code == 201
    assert response.get_json() == {"draft_id": draft_id, "sent": False}
    assert response.headers["Cache-Control"] == "no-store"
    assert calls and calls[0][0] == calls[0][1]


def test_mail_migration_is_explicit_and_separate():
    from pathlib import Path
    sql = Path("migrations/0006_oap_mail_items.sql").read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS oap_mail_items" in sql
    assert "owner_id UUID NOT NULL REFERENCES users(id)" in sql
    assert "ON oap_mail_items(owner_id,folder,created_at DESC)" in sql
    assert "CREATE TABLE IF NOT EXISTS messages" not in sql
