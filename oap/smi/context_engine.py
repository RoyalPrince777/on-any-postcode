"""Load bounded canonical, historical, graph, HRM and world context for SMI."""

from __future__ import annotations

from oap.contracts import ContextSnapshot, FocusedSignal, utc_now
from oap.hrm import HRMCore
from oap.world import WorldEngine

from .memory_orchestrator import compose_memory


class ContextEngine:
    def __init__(self, hrm: HRMCore, world: WorldEngine) -> None:
        self.hrm = hrm
        self.world = world

    def load(self, signal: FocusedSignal) -> ContextSnapshot:
        """Load governed OAP memory with canonical truth always taking priority."""

        dynamic = self.hrm.retrieve_context(signal.task_type, limit=4)
        return ContextSnapshot(
            memories=compose_memory(
                signal.task_type,
                query=signal.content,
                dynamic=dynamic,
                limit=21,
            ),
            world_state=self.world.snapshot(),
            retrieved_at=utc_now(),
        )
