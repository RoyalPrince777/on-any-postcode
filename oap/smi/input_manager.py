"""SMI input manager delegates filtering to the Thalamus."""

from __future__ import annotations

from oap.contracts import FocusedSignal, NexusEnvelope

from .organs import Thalamus


class InputManager:
    def __init__(self, thalamus: Thalamus | None = None) -> None:
        self.thalamus = thalamus or Thalamus()

    def receive(self, envelope: NexusEnvelope) -> FocusedSignal:
        return self.thalamus.receive(envelope)
