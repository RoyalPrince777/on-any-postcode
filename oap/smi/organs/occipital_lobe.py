"""Visual-input awareness without inventing image content."""

from __future__ import annotations

from .base import BrainPacket, finding


class OccipitalLobe:
    organ_id = "occipital_lobe"

    def analyse(self, packet: BrainPacket):
        try:
            visual_count = int(packet.signal.oapcore.get("visual_count", 0) or 0)
        except (TypeError, ValueError):
            visual_count = 0
        visual_count = min(max(visual_count, 0), 1_000)
        summary = (
            f"{visual_count} declared visual input(s) require approved inspection."
            if visual_count
            else "No visual input declared; no visual facts were inferred."
        )
        return finding(
            self.organ_id,
            summary,
            0.7 if visual_count else 0.5,
            "vision",
        )
