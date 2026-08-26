"""Priority, urgency and resource balance."""

from __future__ import annotations

from oap.contracts import SignalLevel

from .base import BrainPacket, finding


class Hypothalamus:
    organ_id = "hypothalamus"

    def analyse(self, packet: BrainPacket):
        urgent = packet.signal.high_impact or bool(packet.signal.oapcore.get("urgent"))
        return finding(
            self.organ_id,
            "Elevated priority requires resource and human review."
            if urgent
            else "Normal priority; no resource urgency declared.",
            0.76,
            "priority",
            "resources",
            signal_level=SignalLevel.YELLOW if urgent else SignalLevel.GREEN,
        )
