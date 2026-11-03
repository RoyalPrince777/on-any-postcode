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
        """Never mark the organism healthy with an unwired or degraded heart."""
        try:
            brain = self.brain.status()
            if not isinstance(brain, dict):
                brain = {"ready": False, "reason": "invalid_status"}
        except Exception:  # noqa: BLE001 - a health probe must fail closed.
            brain = {"ready": False, "reason": "status_unavailable"}

        if self.kernel is None:
            kernel = {
                "component": "Living Kernel",
                "ready": False,
                "reason": "Not wired",
            }
        else:
            try:
                kernel = self.kernel.status()
                if not isinstance(kernel, dict):
                    kernel = {"ready": False, "reason": "invalid_status"}
            except Exception:  # noqa: BLE001 - a health probe must fail closed.
                kernel = {"ready": False, "reason": "status_unavailable"}

        healthy = brain.get("ready") is True and kernel.get("ready") is True
        return {
            "timestamp": utc_now().isoformat(),
            "status": "healthy" if healthy else "degraded",
            "brain": brain,
            "kernel": kernel,
            "human_approval_final": True,
            "independent_execute": False,
        }
