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



def test_smi_mail_requires_authentication_and_never_calls_store(
    anonymous_client, monkeypatch,
):
    calls = []
    monkeypatch.setattr(mail_store, "list_items",
                        lambda *_: calls.append(True))
    response = anonymous_client.post(
        "/mail/smi/read", json={"owner_consent": True, "folder": "inbox"},
    )
    assert response.status_code == 401
    assert calls == []


def test_smi_mail_requires_csrf_and_never_calls_store(client, monkeypatch):
    calls = []
    monkeypatch.setattr(mail_store, "list_items",
                        lambda *_: calls.append(True))
    response = client.post(
        "/mail/smi/read", json={"owner_consent": True, "folder": "inbox"},
    )
    assert response.status_code == 403
    assert calls == []


def test_smi_mail_one_call_consent_returns_owner_scoped_read(
    client, csrf, monkeypatch,
):
    calls = []
    def read(actor, owner, folder):
        calls.append((actor, owner, folder))
        return [{"subject": "private"}]
    monkeypatch.setattr(mail_store, "list_items", read)
    response = client.post(
        "/mail/smi/read",
        json={"owner_consent": True, "folder": "inbox"},
        headers={"X-OAP-CSRF": csrf["csrf_token"]},
    )
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    payload = response.get_json()
    assert payload["items"] == [{"subject": "private"}]
    assert payload["execute"] is False
    assert payload["delivery_enabled"] is False
    assert payload["production_approved"] is False
    assert calls and calls[0][0] == calls[0][1]


def test_smi_mail_does_not_remember_consent(client, csrf, monkeypatch):
    calls = []
    monkeypatch.setattr(mail_store, "list_items",
                        lambda *_: calls.append(True) or [])
    headers = {"X-OAP-CSRF": csrf["csrf_token"]}
    accepted = client.post(
        "/mail/smi/read",
        json={"owner_consent": True, "folder": "inbox"},
        headers=headers,
    )
    denied = client.post(
        "/mail/smi/read", json={"folder": "inbox"}, headers=headers,
    )
    assert accepted.status_code == 200
    assert denied.status_code == 403
    assert calls == [True]


def test_smi_mail_refuses_owner_override_and_send(
    client, csrf, monkeypatch,
):
    calls = []
    monkeypatch.setattr(mail_store, "list_items",
                        lambda *_: calls.append(True))
    headers = {"X-OAP-CSRF": csrf["csrf_token"]}
    for extra in ({"owner_id": str(uuid.uuid4())},
                  {"mailbox_owner_id": str(uuid.uuid4())},
                  {"ability": "mail.send"}):
        response = client.post(
            "/mail/smi/read",
            json={"owner_consent": True, "folder": "inbox", **extra},
            headers=headers,
        )
        assert response.status_code == 403
    assert calls == []


def test_smi_mail_store_unavailable_redacts_detail(client, csrf, monkeypatch):
    def unavailable(*_):
        raise mail_store.MailUnavailable("secret-database-host")
    monkeypatch.setattr(mail_store, "list_items", unavailable)
    response = client.post(
        "/mail/smi/read",
        json={"owner_consent": True, "folder": "inbox"},
        headers={"X-OAP-CSRF": csrf["csrf_token"]},
    )
    assert response.status_code == 503
    assert "secret-database-host" not in response.get_data(as_text=True)



def test_chat_tool_alias_reuses_owner_consent_and_read_only_store(
    client, csrf, monkeypatch,
):
    calls = []
    def read(actor, owner, folder):
        calls.append((actor, owner, folder))
        return [{"subject": "owner only"}]
    monkeypatch.setattr(mail_store, "list_items", read)
    response = client.post(
        "/mission/chat/tools/mail/read",
        json={"folder": "inbox", "owner_consent": True},
        headers={"X-OAP-CSRF": csrf["csrf_token"]},
    )
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.get_json()["items"] == [{"subject": "owner only"}]
    assert response.get_json()["execute"] is False
    assert calls and calls[0][0] == calls[0][1]


def test_chat_tool_alias_denies_implicit_consent_and_owner_override(
    client, csrf, monkeypatch,
):
    calls = []
    monkeypatch.setattr(mail_store, "list_items",
                        lambda *_: calls.append(True))
    headers = {"X-OAP-CSRF": csrf["csrf_token"]}
    for payload in (
        {"folder": "inbox"},
        {"folder": "inbox", "owner_consent": True,
         "owner_id": str(uuid.uuid4())},
        {"folder": "inbox", "owner_consent": True,
         "ability": "mail.send"},
    ):
        response = client.post(
            "/mission/chat/tools/mail/read", json=payload,
            headers=headers,
        )
        assert response.status_code == 403
    assert calls == []


def test_chat_tool_alias_requires_authentication(
    anonymous_client, monkeypatch,
):
    calls = []
    monkeypatch.setattr(mail_store, "list_items",
                        lambda *_: calls.append(True))
    response = anonymous_client.post(
        "/mission/chat/tools/mail/read",
        json={"folder": "inbox", "owner_consent": True},
    )
    assert response.status_code == 401
    assert calls == []


def test_chat_tool_alias_requires_csrf(client, monkeypatch):
    calls = []
    monkeypatch.setattr(mail_store, "list_items",
                        lambda *_: calls.append(True))
    response = client.post(
        "/mission/chat/tools/mail/read",
        json={"folder": "inbox", "owner_consent": True},
    )
    assert response.status_code == 403
    assert calls == []



def test_authenticated_smi_and_chat_alias_never_transfer_mail_body(
    client, csrf, monkeypatch,
):
    private = {
        "id": str(uuid.uuid4()),
        "subject": "<safe subject>",
        "body": "PRIVATE_MAIL_BODY_NEVER_TRANSFER",
        "correspondent": "member@example.test",
        "created_at": "private-time",
        "unapproved_field": "PRIVATE_INTERNAL_FIELD",
    }
    calls = []
    def read(actor, owner, folder):
        calls.append((actor, owner, folder))
        return [private]
    monkeypatch.setattr(mail_store, "list_items", read)
    for path in ("/mail/smi/read", "/mission/chat/tools/mail/read"):
        response = client.post(
            path,
            json={"folder": "inbox", "owner_consent": True},
            headers={"X-OAP-CSRF": csrf["csrf_token"]},
        )
        assert response.status_code == 200
        assert response.get_json()["items"] == [{
            "subject": "<safe subject>",
            "correspondent": "member@example.test",
        }]
        assert response.headers["Cache-Control"] == "no-store"
        for forbidden in (
            "PRIVATE_MAIL_BODY_NEVER_TRANSFER", "PRIVATE_INTERNAL_FIELD",
            private["id"], "private-time",
        ):
            assert forbidden not in response.get_data(as_text=True)
    assert len(calls) == 2
    assert all(actor == owner and folder == "inbox"
               for actor, owner, folder in calls)
