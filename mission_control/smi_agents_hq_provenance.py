"""SMI HQ agent-origin envelope verification; no worker or transport created.

An independent, trusted runtime must provide distinct agent keys and durable
replay protection before this component may be used to admit real messages.
"""
from __future__ import annotations

import hashlib
import hmac
import json
from collections.abc import Mapping
from typing import Any

from mission_control import agents


def verify_agent_envelope(
    envelope: Mapping[str, Any],
    *,
    trusted_keys: Mapping[str, bytes],
    replay_guard: Any,
) -> dict[str, Any]:
    """Fail closed unless passport, key, MAC and independent replay check pass.

    The caller MUST source keys and replay_guard from an authenticated runtime,
    never from user-provided JSON. This verifies origin to the keyholder, not
    independent AI inference or live transmission.
    """
    if not isinstance(envelope, Mapping):
        raise TypeError("invalid_agent_envelope")
    if not isinstance(trusted_keys, Mapping) or not callable(replay_guard):
        raise PermissionError("trusted_agent_runtime_required")
    if set(envelope) != {"agent_id", "message", "nonce", "signature"}:
        raise ValueError("invalid_agent_envelope")
    agent_id, message, nonce, signature = (
        envelope["agent_id"], envelope["message"], envelope["nonce"],
        envelope["signature"],
    )
    if not all(isinstance(x, str) for x in (agent_id, message, nonce, signature)):
        raise ValueError("invalid_agent_envelope")
    if not agent_id or not message.strip() or len(message) > 2000:
        raise ValueError("invalid_agent_message")
    if len(nonce) < 16 or len(nonce) > 128 or len(signature) != 64:
        raise ValueError("invalid_agent_signature_format")
    matched = [a for a in agents.AGENT_REGISTRY if a.get("agent_id") == agent_id]
    if len(matched) != 1 or matched[0].get("registry_status") != "ACTIVE":
        raise PermissionError("active_unique_passport_required")
    key = trusted_keys.get(agent_id)
    if not isinstance(key, bytes) or len(key) < 32:
        raise PermissionError("agent_key_unavailable")
    signed = json.dumps(
        {"agent_id": agent_id, "message": message, "nonce": nonce},
        sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode("utf-8")
    expected = hmac.new(key, signed, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise PermissionError("invalid_agent_mac")
    # Independent persistent atomic insert-if-absent: MUST fail closed.
    if replay_guard(agent_id, nonce) is not True:
        raise PermissionError("replayed_or_unverified_agent_nonce")
    return {
        "speaker": {"agent_id": agent_id, "name": matched[0]["name"],
                    "type": "authenticated_keyholder"},
        "message": message,
        "signature_valid": True,
        "nonce_accepted": True,
        "model_inference_proven": False,
        "agent_to_agent_delivery_proven": False,
        "execution_authorised": False,
        "vote_recorded": False,
        "career_star_awarded": False,
        "founder_final": True,
    }
