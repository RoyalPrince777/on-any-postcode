"""Spatial and postcode context."""

from __future__ import annotations

from .base import BrainPacket, finding


class ParietalLobe:
    organ_id = "parietal_lobe"

    def analyse(self, packet: BrainPacket):
        location = packet.signal.metadata.get("postcode") or packet.signal.metadata.get(
            "location"
        )
        summary = (
            "Spatial context supplied for bounded analysis."
            if location
            else "No postcode or location context supplied; none was inferred."
        )
        return finding(
            self.organ_id,
            summary,
            0.72 if location else 0.48,
            "spatial",
            "postcode",
        )
