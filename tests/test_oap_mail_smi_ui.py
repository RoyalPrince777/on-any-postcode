"""SMI Mail is a deliberate UI read, not inferred from chat messages."""
from pathlib import Path

WRAPPER = Path("mission_control/templates/ollama_chat.html")
CONTROL = Path("mission_control/static/smi_mail_read_control.js")


def test_chat_renders_server_generated_mail_url_and_keeps_existing_tools():
    html = WRAPPER.read_text(encoding="utf-8")
    assert "url_for('oap_mail_private.smi_read_owner_folder')" in html
    assert "smi_mail_read_control.js" in html
    assert "smi_command_centre.js" in html
    assert "smi_chat_final.js" in html


def test_mail_ui_requires_fresh_explicit_click_and_csrf():
    js = CONTROL.read_text(encoding="utf-8")
    assert 'button.addEventListener("click",async ()=>{' in js
    assert "window.confirm(" in js
    assert '"owner_consent":true' not in js  # do not use alternative hidden wire format
    assert "owner_consent:true" in js
    assert '"X-OAP-CSRF":cfg.csrfToken' in js
    assert "credentials:\"same-origin\"" in js
    assert "cfg.mailReadUrl" in js


def test_mail_ui_no_auto_model_context_or_send():
    js = CONTROL.read_text(encoding="utf-8")
    assert "fetch(cfg.mailReadUrl" in js
    assert "document.body.append(dialog)" in js
    assert "messages.append(" not in js
    assert "dialog.replaceChildren()" in js
    assert "controller.abort()" in js
    assert "dialog.close()" in js
    assert "dialog.showModal()" in js
    assert "messageInput.value" not in js
    assert "form.submit(" not in js
    assert "mail.send" not in js
    assert "item.body" not in js
    assert "entry.textContent=subject" in js
    assert "item.body" not in js
    assert "innerHTML" not in js
    assert "payload.execute!==false" in js
    assert "payload.delivery_enabled!==false" in js
