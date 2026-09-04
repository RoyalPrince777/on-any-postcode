"""Load bounded canonical, HRM and world context for SMI."""

from __future__ import annotations

from oap.contracts import ContextSnapshot, FocusedSignal, utc_now
from oap.hrm import HRMCore
from oap.world import WorldEngine

from .canonical_memory import canonical_memory_items


class ContextEngine:
    def __init__(self, hrm: HRMCore, world: WorldEngine) -> None:
        self.hrm = hrm
        self.world = world

    def load(self, signal: FocusedSignal) -> ContextSnapshot:
        """Load canonical Founder-approved memory plus recent audited HRM context."""

        canonical = canonical_memory_items(signal.task_type, limit=14)
        dynamic = self.hrm.retrieve_context(signal.task_type, limit=7)
        return ContextSnapshot(
            memories=(canonical + dynamic)[:21],
            world_state=self.world.snapshot(),
            retrieved_at=utc_now(),
        )
