"""Rapid internal threat sensing before AEGIS and Guardian."""

from __future__ import annotations

from oap.contracts import SignalLevel

from .base import BrainPacket, finding

_RAPID_RISK_TERMS = ("bypass", "override", "delete", "secret", "execute")


class Amygdala:
    organ_id = "amygdala"

    def analyse(self, packet: BrainPacket):
        detected = tuple(
            term for term in _RAPID_RISK_TERMS if term in packet.signal.content.casefold()
        )
        return finding(
            self.organ_id,
            "Rapid risk language detected for AEGIS review."
            if detected
            else "No rapid risk term detected.",
            0.82,
            "risk",
            *detected,
            signal_level=SignalLevel.YELLOW if detected else SignalLevel.GREEN,
        )
