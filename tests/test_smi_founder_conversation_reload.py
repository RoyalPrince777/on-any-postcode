"""Founder saved-work reload boundaries, without live account credentials.

These tests establish source-wiring and privacy invariants. They are not a live
browser reload test or proof of a connected production database.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = (ROOT / "mission_control/templates/ollama_chat_base.html").read_text()
CONTROLLER = (ROOT / "mission_control/static/smi_canonical_controller.js").read_text()
CORE = (ROOT / "mission_control/smi_chat_runtime_core.py").read_text()
VIEWS = (ROOT / "mission_control/views.py").read_text()


def test_restore_remembers_opaque_id_only_after_saved_completion():
    assert "const smiActiveConversationKey=" in BASE
    assert "sessionStorage.setItem(smiActiveConversationKey,String(id))" in BASE
    assert "smiConversationUuid.test(String(id||''))" in BASE
    assert "sessionStorage" not in CORE
    assert "conversationId=completeResult.conversation_id;smiRememberActiveConversation(conversationId);" in CONTROLLER
    assert "completeResult.response" in CONTROLLER


def test_reload_requires_server_verified_owned_conversation():
    assert "if(savedId)await openConversation(savedId,{silent:true});" in BASE
    assert "credentials:'same-origin'" in BASE
    assert "if(response.status===404&&smiReadActiveConversation()===id)smiForgetActiveConversation();" in BASE
    assert "if(data.conversation_id!==id||!Array.isArray(data.messages))" in BASE
    assert "if(silent&&(conversationId||activeController||smiReadActiveConversation()!==id))return;" in BASE
    assert "@web_security.login_required(api=True)" in VIEWS
    assert "WHERE conversation_id=%s AND identity_id=%s" in CORE


def test_new_chat_delete_and_transient_errors_do_not_cross_mission_context():
    assert "smiRestoreAttempted=true;smiForgetActiveConversation();conversationId=null" in BASE
    assert "if(smiReadActiveConversation()===id)smiForgetActiveConversation();" in BASE
    assert "if(!silent)add(error.message,'system')" in BASE
    assert "if(!response.ok)" in BASE
    assert "statusEl.textContent='Saved work was not loaded.'" in BASE


def test_no_raw_messages_or_auth_tokens_persisted_in_web_storage():
    assert BASE.count("sessionStorage.setItem(") == 1
    assert "sessionStorage.setItem(smiActiveConversationKey,String(id))" in BASE
    assert "localStorage" not in BASE
    assert "sessionStorage.setItem(" not in CONTROLLER
    assert "smiRememberActiveConversation(conversationId)" in CONTROLLER
