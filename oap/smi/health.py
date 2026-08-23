"""Read-only health projection for a wired SMI runtime."""

from __future__ import annotations

from oap.contracts import utc_now
from oap.kernel import LivingKernel

from .smi_core import SMICore


class SMIHealthService:
    def __init__(self, brain: SMICore, kernel: LivingKernel | None = None) -> None:
        self.brain = brain
        self.kernel = kernel

    def check(self) -> dict[str, object]:
        brain = self.brain.status()
        kernel = self.kernel.status() if self.kernel else {
            "component": "Living Kernel",
            "ready": False,
            "reason": "Not wired",
        }
        return {
            "timestamp": utc_now().isoformat(),
            "status": "healthy" if brain["ready"] else "degraded",
            "brain": brain,
            "kernel": kernel,
            "human_approval_final": True,
            "independent_execute": False,
        }
