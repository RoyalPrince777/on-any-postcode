"""Command Centre scope decisions must be validated and durably read back."""
from pathlib import Path

import pytest

from mission_control import smi_command_scope as scope

ROOT = Path(__file__).resolve().parents[1]

OWNER = "11111111-1111-4111-8111-111111111111"
OTHER = "22222222-2222-4222-8222-222222222222"
RECEIPT_ID = "smi-" + "a" * 32


def valid():
    return {
        "mode": "AUTO", "depth": 21,
        "missions": ["chat", "command"],
        "decision": "APPROVE_NEXT_SCOPE",
    }


def test_recorded_scope_is_not_execution(monkeypatch):
    captured = {}

    def write(kind, payload, *, require_durable=False):
        captured.update(kind=kind, payload=payload, durable=require_durable)
        return {
            "ok": True, "durable": True, "read_back_ok": True,
            "fallback_used": False, "receipt_id": "smi-receipt",
        }

    monkeypatch.setattr(scope.smi_receipt_backend, "write_receipt", write)
    result = scope.record_command_scope(valid(), identity_id=OWNER)
    assert result["recorded"] is True
    assert result["receipt_id"] == "smi-receipt"
    assert result["executed"] is False
    assert result["whole_smi_green"] is False
    assert captured["durable"] is True
    assert captured["payload"]["safe_payload"]["missions"] == ["chat", "command"]
    assert captured["payload"]["safe_payload"]["approval_grants_execution"] is False


@pytest.mark.parametrize("bad", [
    None, {}, {"mode": "AUTO"},
    {**valid(), "mode": "OPENAI"},
    {**valid(), "mode": "AUTO", "depth": True},
    {**valid(), "depth": 100},
    {**valid(), "missions": []},
    {**valid(), "missions": ["chat", "chat"]},
    {**valid(), "missions": ["external"]},
    {**valid(), "decision": "DEPLOY"},
])
def test_invalid_scope_fails_before_receipt(monkeypatch, bad):
    def unexpected(*args, **kwargs):
        raise AssertionError("Receipt must not be called")
    monkeypatch.setattr(scope.smi_receipt_backend, "write_receipt", unexpected)
    with pytest.raises((TypeError, ValueError), match="invalid_command_scope"):
        scope.record_command_scope(bad, identity_id=OWNER)


@pytest.mark.parametrize("receipt", [
    {"ok": True, "durable": False, "read_back_ok": True, "fallback_used": True},
    {"ok": True, "durable": True, "read_back_ok": False, "fallback_used": False},
    {"ok": False, "durable": True, "read_back_ok": True, "fallback_used": False},
])
def test_unconfirmed_receipt_is_never_presented_as_saved(monkeypatch, receipt):
    monkeypatch.setattr(
        scope.smi_receipt_backend, "write_receipt",
        lambda *args, **kwargs: {**receipt, "receipt_id": "unconfirmed"},
    )
    result = scope.record_command_scope(valid(), identity_id=OWNER)
    assert result["recorded"] is False
    assert result["receipt_id"] is None
    assert result["state"] == "durable_receipt_unavailable"


def test_founder_route_and_chat_surface_remain_separated():
    views = (ROOT / "mission_control/views.py").read_text()
    wrapper = (ROOT / "mission_control/templates/ollama_chat.html").read_text()
    command = (ROOT / "mission_control/static/smi_command_centre.js").read_text()
    assert '@bp.post("/command-centre/scope")' in views
    assert "@web_security.login_required(api=True, founder_only=True)" in views
    assert "web_security.csrf_valid(request)" in views
    assert 'commandScopeUrl:{{ url_for(' in wrapper
    assert 'recordMissionScope("SELECT")' in command
    assert 'recordMissionScope("APPROVE_NEXT_SCOPE")' in command
    assert 'credentials:"same-origin"' in command
    assert 'X-OAP-CSRF' in command
    assert "value?.recorded!==true" in command
    assert "no execution granted" in command
    assert "visibleLiveStatus:false" in wrapper


def test_saved_scope_is_bound_to_founder_and_can_reopen_without_execution(monkeypatch):
    captured = {}

    def writer(kind, payload, *, require_durable=False):
        captured["payload"] = payload["safe_payload"]
        return {
            "ok": True, "durable": True, "read_back_ok": True,
            "fallback_used": False, "receipt_id": RECEIPT_ID,
        }

    monkeypatch.setattr(scope.smi_receipt_backend, "write_receipt", writer)
    assert scope.record_command_scope(valid(), identity_id=OWNER)["recorded"] is True
    monkeypatch.setattr(
        scope.smi_receipt_backend, "read_command_scope_receipt",
        lambda receipt_id, owner_digest: (
            {"available": True, "payload": captured["payload"]}
            if owner_digest == captured["payload"]["owner_digest"] else None
        ),
    )
    reopened = scope.load_command_scope(identity_id=OWNER, receipt_id=RECEIPT_ID)
    assert reopened["found"] is True
    assert reopened["mode"] == "AUTO"
    assert reopened["depth"] == 21
    assert reopened["missions"] == ["chat", "command"]
    assert reopened["decision"] == "APPROVE_NEXT_SCOPE"
    assert reopened["executed"] is False
    assert reopened["whole_smi_green"] is False
    assert "owner_digest" not in reopened
    denied = scope.load_command_scope(identity_id=OTHER, receipt_id=RECEIPT_ID)
    assert denied == {"found": False, "state": "not_found", "executed": False}


def test_missing_and_unavailable_scope_do_not_change_mission(monkeypatch):
    monkeypatch.setattr(
        scope.smi_receipt_backend, "read_command_scope_receipt",
        lambda receipt_id, owner_digest: None,
    )
    assert scope.load_command_scope(identity_id=OWNER, receipt_id=RECEIPT_ID)["found"] is False
    monkeypatch.setattr(
        scope.smi_receipt_backend, "read_command_scope_receipt",
        lambda receipt_id, owner_digest: {"available": False},
    )
    assert scope.load_command_scope(identity_id=OWNER, receipt_id=RECEIPT_ID)["state"] == "durable_receipt_unavailable"
    with pytest.raises(ValueError, match="invalid_scope_receipt"):
        scope.load_command_scope(identity_id=OWNER, receipt_id="bad-id")


def test_corrupt_or_unapproved_scope_cannot_reopen(monkeypatch):
    bad = {
        "owner_digest": scope._owner_digest(OWNER),
        "scope_only": True, "executed": True, "approval_grants_execution": False,
        "mode": "AUTO", "depth": 21, "missions": ["chat"],
        "decision": "SELECT",
    }
    monkeypatch.setattr(
        scope.smi_receipt_backend, "read_command_scope_receipt",
        lambda receipt_id, owner_digest: {"available": True, "payload": bad},
    )
    assert scope.load_command_scope(identity_id=OWNER, receipt_id=RECEIPT_ID)["found"] is False


def test_reopen_route_is_founder_only_and_read_only():
    views = (ROOT / "mission_control/views.py").read_text()
    wrapper = (ROOT / "mission_control/templates/ollama_chat.html").read_text()
    command = (ROOT / "mission_control/static/smi_command_centre.js").read_text()
    assert '@bp.get("/command-centre/scope/<receipt_id>")' in views
    assert "identity_id=_chat_identity(), receipt_id=receipt_id" in views
    assert "commandScopeReadUrl:{{ url_for(" in wrapper
    assert "missionLoad.addEventListener" in command
    assert "value?.found!==true||value?.executed!==false" in command
    assert "Saved scope reopened" in command
    assert "no execution granted" in command
