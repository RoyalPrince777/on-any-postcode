"""Draft owner authority comes exclusively from the authenticated session."""
from __future__ import annotations

import uuid

from mission_control import mail_store, public_store


def test_draft_owner_override_denied_before_user_or_mail_write(
    client, csrf, monkeypatch,
):
    calls = []
    monkeypatch.setattr(
        public_store, "ensure_authenticated_user",
        lambda *_args, **_kwargs: calls.append("user_write"),
    )
    monkeypatch.setattr(
        mail_store, "save_draft",
        lambda *_args, **_kwargs: calls.append("draft_write"),
    )
    headers = {"X-OAP-CSRF": csrf["csrf_token"]}
    for owner_field in ("owner_id", "mailbox_owner_id"):
        response = client.post(
            "/mail/drafts",
            json={"subject": "Unsent", owner_field: str(uuid.uuid4())},
            headers=headers,
        )
        assert response.status_code == 403
        assert response.get_json() == {
            "error": {"code": "mail_owner_override_forbidden"}
        }
        assert response.headers["Cache-Control"] == "no-store"
        assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert calls == []
