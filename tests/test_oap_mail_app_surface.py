"""First-party Mail UI does not expand authority or manufacture delivery."""
from __future__ import annotations

from pathlib import Path


def test_private_mail_app_requires_login(anonymous_client):
    response = anonymous_client.get("/mail/app")
    assert response.status_code in (302, 303)
    assert response.headers["Cache-Control"] == "no-store"


def test_authenticated_mail_app_does_not_read_or_write_on_page_load(
    client, monkeypatch,
):
    from mission_control import mail_store, public_store
    calls = []
    monkeypatch.setattr(mail_store, "list_items",
                        lambda *_: calls.append("read"))
    monkeypatch.setattr(mail_store, "save_draft",
                        lambda *_args, **_kwargs: calls.append("write"))
    monkeypatch.setattr(public_store, "ensure_authenticated_user",
                        lambda *_args, **_kwargs: calls.append("user"))
    response = client.get("/mail/app")
    page = response.get_data(as_text=True)
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert "OAP Mail" in page
    assert "No email delivery" in page
    assert "Saving a draft does not send a message" in page
    assert "Store installation remains release pending" in page
    assert "oap_mail_app.js" in page
    assert "/mail/drafts" in page
    assert "/mail/__FOLDER__" in page
    assert calls == []


def test_mail_app_script_is_explicit_user_action_and_text_safe():
    script = Path("mission_control/static/oap_mail_app.js").read_text(
        encoding="utf-8"
    )
    assert 'button.addEventListener("click",async()=>{' in script
    assert 'form.addEventListener("submit",async event=>{' in script
    assert 'credentials:"same-origin"' in script
    assert 'cache:"no-store"' in script
    assert '"X-OAP-CSRF":csrf' in script
    assert "body.textContent=item.body" in script
    assert "heading.textContent=item.subject" in script
    assert "controller.abort()" not in script  # active reads cleared on navigation
    assert "active.abort()" in script
    assert "innerHTML" not in script
    assert "mail.send" not in script
