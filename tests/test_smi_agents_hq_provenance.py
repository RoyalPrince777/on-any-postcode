"""Agent origin is never inferred from an agent name."""
import hashlib
import hmac
import json

import pytest

from mission_control.smi_agents_hq_provenance import verify_agent_envelope

KEY = b"k" * 32
NONCE = "nonce-unique-12345678"


def _signed(message="Evidence reviewed", agent_id="NEO-001"):
    data = {"agent_id": agent_id, "message": message, "nonce": NONCE}
    raw = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return {**data, "signature": hmac.new(KEY, raw, hashlib.sha256).hexdigest()}


def test_authenticated_passport_message_is_not_claimed_to_be_live_ai():
    receipt = verify_agent_envelope(
        _signed(), trusted_keys={"NEO-001": KEY}, replay_guard=lambda a, n: True
    )
    assert receipt["signature_valid"] and receipt["nonce_accepted"]
    assert receipt["speaker"]["name"] == "Neo"
    assert not receipt["model_inference_proven"]
    assert not receipt["agent_to_agent_delivery_proven"]
    assert not receipt["execution_authorised"]


def test_tampered_message_rejected():
    envelope = _signed()
    envelope["message"] = "I approve everything"
    with pytest.raises(PermissionError, match="invalid_agent_mac"):
        verify_agent_envelope(
            envelope, trusted_keys={"NEO-001": KEY},
            replay_guard=lambda a, n: True,
        )


def test_unknown_agent_rejected_even_with_valid_mac():
    with pytest.raises(PermissionError, match="active_unique_passport_required"):
        verify_agent_envelope(
            _signed(agent_id="UNKNOWN-001"),
            trusted_keys={"UNKNOWN-001": KEY},
            replay_guard=lambda a, n: True,
        )


def test_replay_guard_must_exist_and_accept_nonce():
    with pytest.raises(PermissionError, match="trusted_agent_runtime_required"):
        verify_agent_envelope(_signed(), trusted_keys={"NEO-001": KEY}, replay_guard=None)
    with pytest.raises(PermissionError, match="replayed_or_unverified_agent_nonce"):
        verify_agent_envelope(
            _signed(), trusted_keys={"NEO-001": KEY}, replay_guard=lambda a, n: False
        )


def test_wrong_or_short_trusted_key_rejected():
    with pytest.raises(PermissionError, match="agent_key_unavailable"):
        verify_agent_envelope(
            _signed(), trusted_keys={"NEO-001": b"short"},
            replay_guard=lambda a, n: True,
        )


def test_no_client_supplied_permission_or_execution_field():
    envelope = _signed()
    envelope["execute"] = True
    with pytest.raises(ValueError, match="invalid_agent_envelope"):
        verify_agent_envelope(
            envelope, trusted_keys={"NEO-001": KEY},
            replay_guard=lambda a, n: True,
        )
