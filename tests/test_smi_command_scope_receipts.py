"""Command Centre scope decisions must be validated and durably read back."""
from pathlib import Path

import pytest

from mission_control import smi_command_scope as scope

ROOT = Path(__file__).resolve().parents[1]


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
    result = scope.record_command_scope(valid())
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
    with pytest.raises(ValueError, match="invalid_command_scope"):
        scope.record_command_scope(bad)


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
    result = scope.record_command_scope(valid())
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
