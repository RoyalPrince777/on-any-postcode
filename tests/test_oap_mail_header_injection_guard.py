"""Draft header-bound fields reject CRLF and NUL before any persistence."""
from __future__ import annotations

import pytest

from mission_control import mail_store, public_store


@pytest.mark.parametrize("field,value", [
    ("subject", "hello\r\nBcc: outsider@example.test"),
    ("subject", "hello\nInjected"),
    ("subject", "hello\x00secret"),
    ("correspondent", "user@example.test\r\nBcc: outsider@example.test"),
    ("correspondent", "user@example.test\nInjected"),
    ("correspondent", "user@example.test\x00secret"),
])
def test_header_injection_fails_without_persistence(
    client, csrf, monkeypatch, field, value,
):
    calls = []
    monkeypatch.setattr(public_store, "ensure_authenticated_user",
                        lambda *_args, **_kwargs: calls.append("user"))
    monkeypatch.setattr(mail_store, "save_draft",
                        lambda *_args, **_kwargs: calls.append("draft"))
    response = client.post(
        "/mail/drafts",
        json={"subject": "Private", field: value},
        headers={"X-OAP-CSRF": csrf["csrf_token"]},
    )
    assert response.status_code == 400
    assert response.get_json() == {"error": {"code": "mail_draft_header_invalid"}}
    assert response.headers["Cache-Control"] == "no-store"
    assert calls == []


def test_multiline_message_body_remains_supported():
    assert mail_store.validate_draft_fields(
        subject="Private", body="first line\nsecond line",
    )[1] == "first line\nsecond line"
