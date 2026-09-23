"""Invalid draft fields cannot create public users or touch the Mail store."""
from __future__ import annotations

import pytest

from mission_control import mail_store, public_store


@pytest.mark.parametrize("payload,code", [
    ({}, "mail_draft_empty"),
    ({"subject": "   ", "body": "  "}, "mail_draft_empty"),
    ({"subject": {"untrusted": "object"}}, "mail_draft_field_invalid"),
    ({"body": ["untrusted"]}, "mail_draft_field_invalid"),
    ({"correspondent": 3, "subject": "draft"}, "mail_draft_field_invalid"),
    ({"subject": "x" * 201}, "mail_draft_too_large"),
    ({"body": "x" * 20001}, "mail_draft_too_large"),
    ({"subject": "draft", "correspondent": "x" * 321}, "mail_draft_too_large"),
])
def test_invalid_draft_has_no_persistence_side_effects(
    client, csrf, monkeypatch, payload, code,
):
    calls = []
    monkeypatch.setattr(public_store, "ensure_authenticated_user",
                        lambda *_args, **_kwargs: calls.append("user"))
    monkeypatch.setattr(mail_store, "save_draft",
                        lambda *_args, **_kwargs: calls.append("draft"))
    response = client.post(
        "/mail/drafts", json=payload,
        headers={"X-OAP-CSRF": csrf["csrf_token"]},
    )
    assert response.status_code == 400
    assert response.get_json() == {"error": {"code": code}}
    assert response.headers["Cache-Control"] == "no-store"
    assert calls == []


def test_valid_fields_are_normalized_without_store_access():
    assert mail_store.validate_draft_fields(
        subject="  Draft  ", body="  Private  ", correspondent="  owner@example.test  ",
    ) == ("Draft", "Private", "owner@example.test")
