"""Coordination, timing and correction checks."""

from __future__ import annotations

from .base import BrainPacket, finding


class Cerebellum:
    organ_id = "cerebellum"

    def analyse(self, packet: BrainPacket):
        complete = bool(packet.signal.task_type and packet.signal.content)
        return finding(
            self.organ_id,
            "Input structure is coordinated for analysis."
            if complete
            else "Input structure requires correction before analysis.",
            0.8 if complete else 0.3,
            "coordination",
            "quality",
        )
