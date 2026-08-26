"""NEXUS carries validated signals; it never decides their outcome."""

from __future__ import annotations

import json
import re

from oap.contracts import BrainRequest, NexusEnvelope, utc_now

_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_SAFE_TASK = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _.-]{0,63}$")


def _oapcore_keys_are_text(value: object) -> bool:
    if isinstance(value, dict):
        return all(
            isinstance(key, str) and _oapcore_keys_are_text(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return all(_oapcore_keys_are_text(item) for item in value)
    return True


class SignalValidationError(ValueError):
    """Raised when an incoming signal cannot safely enter the nervous system."""


class NexusRouter:
    MAX_CONTENT_LENGTH = 20_000
    MAX_OAPCORE_FIELDS = 40
    MAX_OAPCORE_BYTES = 50_000

    def receive(self, request: BrainRequest) -> NexusEnvelope:
        if not isinstance(request.request_id, str) or not _SAFE_ID.fullmatch(
            request.request_id
        ):
            raise SignalValidationError("Invalid request identifier")
        if not isinstance(request.identity_id, str) or not _SAFE_ID.fullmatch(
            request.identity_id
        ):
            raise SignalValidationError("Invalid identity identifier")
        if not isinstance(request.content, str):
            raise SignalValidationError("Signal content must be text")
        if not isinstance(request.task_type, str) or not _SAFE_TASK.fullmatch(
            request.task_type
        ):
            raise SignalValidationError("Invalid task type")
        if not isinstance(request.oapcore, dict):
            raise SignalValidationError("Signal OAP CORE must be an object")
        if not isinstance(request.high_impact, bool):
            raise SignalValidationError("High-impact flag must be boolean")
        if not request.content.strip():
            raise SignalValidationError("Signal content is required")
        if len(request.content) > self.MAX_CONTENT_LENGTH:
            raise SignalValidationError("Signal content exceeds the safe limit")
        if len(request.oapcore) > self.MAX_OAPCORE_FIELDS:
            raise SignalValidationError("Signal OAP CORE exceeds the safe limit")
        if not _oapcore_keys_are_text(request.oapcore):
            raise SignalValidationError("Signal OAP CORE keys must be text")
        try:
            oapcore_json = json.dumps(
                request.oapcore,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            )
        except (RecursionError, TypeError, ValueError) as exc:
            raise SignalValidationError("Signal OAP CORE is not valid JSON") from exc
        if len(oapcore_json.encode("utf-8")) > self.MAX_OAPCORE_BYTES:
            raise SignalValidationError("Signal OAP CORE exceeds the safe limit")

        return NexusEnvelope(
            request=request,
            route=("SP Signals", "NEXUS", "SMI"),
            received_at=utc_now(),
        )

    def status(self) -> dict[str, object]:
        return {
            "component": "NEXUS",
            "ready": True,
            "role": "transport_only",
            "decision_authority": False,
            "context_language": "OAP CORE",
        }
