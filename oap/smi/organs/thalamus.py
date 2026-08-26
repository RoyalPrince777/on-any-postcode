"""Thalamus input filtering and safe OAP CORE routing."""

from __future__ import annotations

from typing import Any

from oap.contracts import FocusedSignal, NexusEnvelope

_PRIVATE_KEYS = {
    "password",
    "secret",
    "token",
    "totp",
    "private_key",
    "recovery_code",
}


def _redact_private_oapcore(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "<REDACTED>"
            if key.casefold() in _PRIVATE_KEYS
            else _redact_private_oapcore(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact_private_oapcore(item) for item in value]
    return value


class Thalamus:
    def receive(self, envelope: NexusEnvelope) -> FocusedSignal:
        request = envelope.request
        oapcore = _redact_private_oapcore(request.oapcore)
        tags = [request.task_type.casefold()]
        if request.high_impact:
            tags.append("high_impact")
        return FocusedSignal(
            request_id=request.request_id,
            identity_id=request.identity_id,
            task_type=request.task_type,
            content=request.content.strip(),
            oapcore=oapcore,
            high_impact=request.high_impact,
            tags=tuple(tags),
        )
