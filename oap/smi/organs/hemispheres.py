"""Logical and creative hemispheres inside SMI."""

from __future__ import annotations

from .base import BrainPacket, finding


class LeftHemisphere:
    organ_id = "left_hemisphere"

    def analyse(self, packet: BrainPacket):
        words = len(packet.signal.content.split())
        return finding(
            self.organ_id,
            f"Structured {packet.signal.task_type} signal contains {words} words.",
            0.78,
            "logic",
            "structure",
        )


class RightHemisphere:
    organ_id = "right_hemisphere"

    def analyse(self, packet: BrainPacket):
        cultural = bool(packet.signal.metadata.get("culture"))
        summary = (
            "Cultural and human-meaning context is present."
            if cultural
            else "Human meaning requires explicit context; none was invented."
        )
        return finding(
            self.organ_id,
            summary,
            0.68 if cultural else 0.52,
            "creativity",
            "human_meaning",
        )
