"""Private Mail API responses resist caching, indexing, and referrer leakage."""
from __future__ import annotations

import pytest

from mission_control import mail_store


@pytest.mark.parametrize("path", ["/mail/inbox", "/mail/not-a-folder"])
def test_mail_folder_responses_have_private_headers(client, monkeypatch, path):
    monkeypatch.setattr(mail_store, "list_items", lambda *_: [])
    response = client.get(path)
    assert response.status_code in (200, 400)
    _assert_private_headers(response)


@pytest.mark.parametrize("payload", [
    {},
    {"subject": "Private", "owner_id": "another-owner"},
])
def test_draft_denials_have_private_headers(client, csrf, payload):
    response = client.post(
        "/mail/drafts", json=payload,
        headers={"X-OAP-CSRF": csrf["csrf_token"]},
    )
    assert response.status_code in (400, 403)
    _assert_private_headers(response)


def test_smi_consent_denial_has_private_headers(client, csrf):
    response = client.post(
        "/mission/chat/tools/mail/read", json={"folder": "inbox"},
        headers={"X-OAP-CSRF": csrf["csrf_token"]},
    )
    assert response.status_code == 403
    _assert_private_headers(response)


@pytest.mark.parametrize("method,path", [
    ("GET", "/mail/inbox"),
    ("POST", "/mail/drafts"),
    ("POST", "/mail/smi/read"),
    ("POST", "/mission/chat/tools/mail/read"),
])
def test_anonymous_mail_denials_are_private(anonymous_client, method, path):
    response = anonymous_client.open(path, method=method)
    assert response.status_code == 401
    _assert_private_headers(response)


def _assert_private_headers(response):
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["Pragma"] == "no-cache"
    assert response.headers["Vary"] == "Cookie"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert response.headers["X-Robots-Tag"] == "noindex, nofollow, noarchive"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
