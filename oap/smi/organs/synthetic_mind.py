"""Synthetic Mind as an internal SMI organ, never another brain."""

from __future__ import annotations

from .base import BrainPacket, finding


class SyntheticMind:
    organ_id = "synthetic_mind"

    def analyse(self, packet: BrainPacket):
        advisors = len(packet.advisors.agent_ids)
        providers = sum(result.available for result in packet.provider_results)
        return finding(
            self.organ_id,
            (
                f"Integrated {advisors} approved advisor(s) and "
                f"{providers} available provider result(s)."
            ),
            0.7 if advisors or providers else 0.5,
            "integration",
            "internal_organ",
        )
