"""Language and conversational context."""

from __future__ import annotations

from .base import BrainPacket, finding


class TemporalLobe:
    organ_id = "temporal_lobe"

    def analyse(self, packet: BrainPacket):
        has_question = "?" in packet.signal.content
        summary = (
            "Language signal includes a direct question."
            if has_question
            else "Language signal is an instruction or statement."
        )
        return finding(
            self.organ_id,
            summary,
            0.74,
            "language",
            "conversation",
        )
