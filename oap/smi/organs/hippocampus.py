"""Contextual memory awareness through HRM."""

from __future__ import annotations

from .base import BrainPacket, finding


class Hippocampus:
    organ_id = "hippocampus"

    def analyse(self, packet: BrainPacket):
        count = len(packet.context.memories)
        summary = (
            f"HRM supplied {count} relevant contextual memory record(s)."
            if count
            else "No relevant HRM memory found; no history was invented."
        )
        return finding(
            self.organ_id,
            summary,
            0.72 if count else 0.5,
            "memory",
            "context",
        )
