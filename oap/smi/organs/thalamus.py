"""Thalamus input filtering and safe metadata routing."""

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


def _redact_private_metadata(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "<REDACTED>"
            if key.casefold() in _PRIVATE_KEYS
            else _redact_private_metadata(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact_private_metadata(item) for item in value]
    return value


class Thalamus:
    def receive(self, envelope: NexusEnvelope) -> FocusedSignal:
        request = envelope.request
        metadata = _redact_private_metadata(request.metadata)
        tags = [request.task_type.casefold()]
        if request.high_impact:
            tags.append("high_impact")
        return FocusedSignal(
            request_id=request.request_id,
            identity_id=request.identity_id,
            task_type=request.task_type,
            content=request.content.strip(),
            metadata=metadata,
            high_impact=request.high_impact,
            tags=tuple(tags),
        )
