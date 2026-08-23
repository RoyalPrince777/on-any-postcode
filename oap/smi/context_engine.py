"""Load bounded HRM and world context for SMI."""

from __future__ import annotations

from oap.contracts import ContextSnapshot, FocusedSignal, utc_now
from oap.hrm import HRMCore
from oap.world import WorldEngine


class ContextEngine:
    def __init__(self, hrm: HRMCore, world: WorldEngine) -> None:
        self.hrm = hrm
        self.world = world

    def load(self, signal: FocusedSignal) -> ContextSnapshot:
        return ContextSnapshot(
            memories=self.hrm.retrieve_context(signal.task_type),
            world_state=self.world.snapshot(),
            retrieved_at=utc_now(),
        )
