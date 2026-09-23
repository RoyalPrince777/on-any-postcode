from __future__ import annotations

import pytest

from mission_control import matrix_founder_decisions as decisions
from mission_control import matrix_signal_bus, smi_receipt_backend


def _signal():
    return matrix_signal_bus.route_signal(
        sender="Morpheus",
        topic="Potential false green",
        evidence=("unverified CI claim",),
        consequential=True,
    )


def _record(signal=None, decision="HOLD", reason="Insufficient independent evidence"):
    return decisions.record_hold(
        identity_id="founder-123",
        signal=_signal() if signal is None else signal,
        decision=decision,
        reason=reason,
    )


def test_only_canonical_authority_can_write(monkeypatch):
    monkeypatch.setattr(decisions.authority, "identity_is_authority", lambda _id: False)
    monkeypatch.setattr(
        smi_receipt_backend, "write_receipt",
        lambda *_args, **_kwargs: pytest.fail("unauthorised receipt write"),
    )
    with pytest.raises(PermissionError, match="human_authority_required"):
        _record()


@pytest.mark.parametrize("decision", ["APPROVE", "PASS", "YES", ""])
def test_producer_cannot_approve(monkeypatch, decision):
    monkeypatch.setattr(decisions.authority, "identity_is_authority", lambda _id: True)
    with pytest.raises(ValueError, match="Only HOLD or BLOCK"):
        _record(decision=decision)


def test_invalid_review_envelope_fails_before_receipt(monkeypatch):
    monkeypatch.setattr(decisions.authority, "identity_is_authority", lambda _id: True)
    monkeypatch.setattr(
        smi_receipt_backend, "write_receipt",
        lambda *_args, **_kwargs: pytest.fail("invalid review wrote a receipt"),
    )
    signal = _signal()
    signal["execution_granted"] = True
    with pytest.raises(ValueError):
        _record(signal=signal)


def test_durable_hold_records_real_founder_action_without_votes(monkeypatch):
    monkeypatch.setattr(decisions.authority, "identity_is_authority", lambda _id: True)
    calls = []

    def write(kind, payload, *, require_durable=False):
        calls.append((kind, payload, require_durable))
        return {
            "ok": True, "read_back_ok": True, "durable": True,
            "fallback_used": False, "receipt_kind": "war_room_live_proof_receipt",
        }

    monkeypatch.setattr(smi_receipt_backend, "write_receipt", write)
    result = _record()
    assert result["state"] == "founder_hold_recorded"
    assert result["actual_agent_votes"] == ()
    assert result["evidence_verified"] is False
    assert result["founder_approved"] is False
    assert result["matrix_update_allowed"] is False
    assert result["execution_granted"] is False
    assert result["full_green"] is False
    assert calls[0][0] == "war_room_live_proof_receipt"
    assert calls[0][1]["command"] == "matrix_founder_hold"
    assert calls[0][1]["safe_payload"]["founder_identity_id"] == "founder-123"
    assert calls[0][1]["safe_payload"]["founder_approved"] is False
    assert calls[0][2] is True


@pytest.mark.parametrize("bad_receipt", [
    {"ok": True, "read_back_ok": True, "durable": False, "fallback_used": False, "receipt_kind": "war_room_live_proof_receipt"},
    {"ok": True, "read_back_ok": False, "durable": True, "fallback_used": False, "receipt_kind": "war_room_live_proof_receipt"},
    {"ok": True, "read_back_ok": True, "durable": True, "fallback_used": True, "receipt_kind": "war_room_live_proof_receipt"},
])
def test_receipt_failure_never_claims_founder_hold(monkeypatch, bad_receipt):
    monkeypatch.setattr(decisions.authority, "identity_is_authority", lambda _id: True)
    monkeypatch.setattr(
        smi_receipt_backend, "write_receipt", lambda *_args, **_kwargs: bad_receipt
    )
    result = _record(decision="BLOCK")
    assert result["state"] == "founder_hold_unproven"
    assert result["decision"] is None
    assert result["full_green"] is False


def test_private_route_requires_authenticated_session(anonymous_client):
    response = anonymous_client.post(
        "/mission/matrix-decisions/hold",
        json={"decision": "HOLD", "reason": "unverified", "signal": _signal()},
    )
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "authentication_required"


def test_private_route_rejects_missing_csrf(client):
    response = client.post(
        "/mission/matrix-decisions/hold",
        json={"decision": "HOLD", "reason": "unverified", "signal": _signal()},
    )
    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "csrf_failed"
