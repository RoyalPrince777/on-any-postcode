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

def test_saved_mission_anchor_recovers_after_many_short_signals():
    from mission_control import smi_founder_workflow as workflow

    latest_first = [
        "🟣", "🟢", "🟣🟢", "continue", "next",
        "🟣", "🟣", "🟢", "🟣", "🟣",
        "Review SMI memory recovery with War Room judges.",
    ]
    anchor = workflow.latest_substantive_user_turn(latest_first)
    assert anchor == "Review SMI memory recovery with War Room judges."
    short_history = [
        {"role": "user", "content": "🟣"},
        {"role": "assistant", "content": "Only a continuation response."},
    ] * 6
    assert workflow.resolve_turn("🟣", short_history)["review_may_continue"] is False
    recovered = [{"role": "user", "content": anchor}, *short_history[-11:]]
    resumed = workflow.resolve_turn("🟣", recovered)
    assert resumed["review_may_continue"] is True
    assert resumed["war_room_requested"] is True
    assert resumed["execution_granted"] is False


def test_saved_mission_anchor_never_invents_empty_or_old_control_only_context():
    from mission_control import smi_founder_workflow as workflow

    assert workflow.latest_substantive_user_turn(
        ["🟣", "🟢", "🟣🟢", "next", "continue", "  "]
    ) is None


def test_foreign_and_missing_chat_ids_are_rejected_without_mission_switch():
    import pytest

    from mission_control import smi_chat_runtime_core as core

    owner = "11111111-1111-4111-8111-111111111111"
    other = "22222222-2222-4222-8222-222222222222"
    core._require_owned_conversation("", None, owner)  # A brand-new chat.
    core._require_owned_conversation("existing", (owner,), owner)
    with pytest.raises(ValueError, match="conversation_not_found"):
        core._require_owned_conversation("existing", (other,), owner)
    with pytest.raises(ValueError, match="conversation_not_found"):
        core._require_owned_conversation("deleted", None, owner)


def test_mission_anchor_database_query_scoped_to_authenticated_owner():
    core = (ROOT / "mission_control/smi_chat_runtime_core.py").read_text()
    assert "latest_substantive_user_turn" in core
    assert "LIMIT 200" in core
    assert "WHERE c.conversation_id=%s AND c.identity_id=%s" in core
    assert "(conversation, identity)" in core
    assert "owned_saved_mission_anchor" in core
    assert '_require_owned_conversation(supplied_conversation, owner, identity)' in core


def test_owner_scoped_saved_conversation_load_blocks_other_identity(monkeypatch):
    """Exercise actual DB ownership query with two controlled identities."""
    from contextlib import nullcontext
    from datetime import datetime, timezone

    import pytest

    from mission_control import smi_chat_runtime_core

    founder = "11111111-1111-4111-8111-111111111111"
    other = "22222222-2222-4222-8222-222222222222"
    conversation = "33333333-3333-4333-8333-333333333333"
    now = datetime(2026, 9, 21, tzinfo=timezone.utc)
    message_reads = []

    class Result:
        def __init__(self, rows):
            self.rows = rows

        def fetchone(self):
            return self.rows[0] if self.rows else None

        def fetchall(self):
            return self.rows

    class Store:
        def execute(self, query, params):
            if "SELECT title,updated_at" in query:
                return Result(
                    [("Founder private work", now)] if params[1] == founder else []
                )
            if "SELECT message_id,role,content" in query:
                message_reads.append(params)
                return Result([
                    (
                        "44444444-4444-4444-8444-444444444444",
                        "user", "Founder-only War Room mission", None, None,
                        "PASSED", now,
                    )
                ])
            raise AssertionError("Unexpected conversation query")

    monkeypatch.setattr(
        smi_chat_runtime_core.postgres_db,
        "connect",
        lambda readonly=False: nullcontext(Store()),
    )

    with pytest.raises(ValueError, match="conversation_not_found"):
        smi_chat_runtime_core.get_conversation(other, conversation)
    assert message_reads == []

    allowed = smi_chat_runtime_core.get_conversation(founder, conversation)
    assert allowed["messages"][0]["content"] == "Founder-only War Room mission"
    assert message_reads == [(conversation,)]
