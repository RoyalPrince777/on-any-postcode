"""Production-evidence adapter for bounded SMI autonomy cycles.

The local ``build_smi`` factory is SQLite-backed and is not the production web
runtime. This adapter therefore observes the live Mission Control 3x7/21-gate
SMI health projection and feeds those reported states into the same
``SMIAutonomyEngine`` used by ``SMICore``. It performs no provider completion,
creates no recommendation, records no HRM memory and has no execution authority.
"""

from __future__ import annotations

from typing import Any

from oap.smi.autonomy import SMIAutonomyEngine
from oap.smi.coherence import CoherenceEngine
from oap.smi.self_model import SelfModel

from . import smi_chat_runtime


def status() -> dict[str, Any]:
    """Describe the worker-safe SMI autonomy boundary without probing runtime."""

    base = SMIAutonomyEngine().status()
    return {
        **base,
        "component": "SMI Production Autonomy",
        "evidence_source": "3x7_21_gate_production_health",
        "health_probe_on_status": False,
        "provider_completion_performed": False,
        "hrm_record_created": False,
        "consequential_action": False,
    }


def _components(health: dict[str, Any]) -> tuple[dict[str, object], ...]:
    checks = health.get("checks")
    if not isinstance(checks, dict):
        checks = {}
    return tuple(
        {
            "component": f"SMI 21 Gate: {name}",
            "ready": bool(value),
            "mode": "production_health_evidence",
            "coherence_claims": {
                "human_authority_final": True,
                "independent_execution": False,
            },
        }
        for name, value in checks.items()
    )


def _evolution_evidence(health: dict[str, Any]) -> dict[str, object]:
    """Require real governance evidence before calling improvement controls ready."""

    checks = health.get("checks")
    if not isinstance(checks, dict):
        checks = {}
    ready = all(
        checks.get(name) is True
        for name in ("audit", "human_authority", "approval_receipt")
    )
    return {
        "component": "Controlled Self-Improvement Runtime Gate",
        "ready": ready,
        "mode": "proposal_sandbox_human_approval",
        "sandbox_required": True,
        "human_approval_required": True,
        "living_kernel_required": True,
        "independent_apply": False,
    }


def run_cycle() -> dict[str, Any]:
    """Run one read-only SMI autonomy cycle from live production health evidence."""

    health = smi_chat_runtime.health()
    components = _components(health)
    self_model = SelfModel().observe(components)
    coherence = CoherenceEngine().evaluate(components)
    cycle = SMIAutonomyEngine().run_cycle(
        components=components,
        self_model=self_model.as_dict(),
        coherence=coherence.as_dict(),
        evolution=_evolution_evidence(health),
    )
    checks = health.get("checks") if isinstance(health.get("checks"), dict) else {}
    return {
        **cycle,
        "source": "production_3x7_21_gate_health",
        "health_status": str(health.get("status") or "degraded"),
        "gates_green": sum(value is True for value in checks.values()),
        "gates_total": len(checks),
        "production_invariants": {
            "execution_locked": bool(
                health.get("invariants", {}).get("execution_locked")
            ),
            "human_authority_final": bool(
                health.get("invariants", {}).get("human_authority_final")
            ),
        },
        "self_model": self_model.as_dict(),
        "coherence_report": coherence.as_dict(),
        "controlled_self_improvement_runtime": _evolution_evidence(health),
        "provider_completion_performed": False,
        "hrm_record_created": False,
        "consequential_action": False,
    }
