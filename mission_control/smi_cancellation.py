"""Process-scoped cooperative cancellation for active SMI response streams.

The HTTP stream owns the token. Closing the stream (including Human STOP in the
browser) cancels the same in-process worker that is producing that stream. This
module never grants execution authority and stores no prompt, response, secret or
private reasoning content.
"""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


class SMIRequestCancelled(RuntimeError):
    """Raised when Human Authority or stream teardown cancels active SMI work."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class CancellationToken:
    control_id: str
    identity_id: str
    created_at: str
    _event: threading.Event = field(default_factory=threading.Event, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    _reason: str = field(default="", repr=False)
    _cancelled_at: str = field(default="", repr=False)

    @property
    def cancelled(self) -> bool:
        return self._event.is_set()

    def cancel(self, reason: str = "human_stop") -> bool:
        """Cancel once; repeated STOP remains safe and idempotent."""
        clean_reason = str(reason or "human_stop").strip()[:80] or "human_stop"
        with self._lock:
            first = not self._event.is_set()
            if first:
                self._reason = clean_reason
                self._cancelled_at = _now()
                self._event.set()
            return first

    def raise_if_cancelled(self) -> None:
        if self._event.is_set():
            raise SMIRequestCancelled("smi_request_cancelled")

    def snapshot(self) -> dict[str, Any]:
        """Return only secret-safe cancellation state."""
        return {
            "control_id": self.control_id,
            "cancelled": self.cancelled,
            "reason": self._reason if self.cancelled else "",
            "created_at": self.created_at,
            "cancelled_at": self._cancelled_at if self.cancelled else "",
            "human_authority_final": True,
            "execution_authority_expanded": False,
            "private_reasoning_stored": False,
        }


def new_token(identity_id: object) -> CancellationToken:
    identity = str(identity_id or "").strip()
    if not identity:
        raise ValueError("identity_id_required")
    return CancellationToken(
        control_id=f"smi-stop-{uuid4().hex}",
        identity_id=identity,
        created_at=_now(),
    )
