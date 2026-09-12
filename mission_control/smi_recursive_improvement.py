"""Live, governed recursive-improvement projection for Personal SMI.

The loop reads current production evidence, compares the SMI, OAP CORE and
whole-organism views, and prepares a deterministic reversible candidate when
weaknesses are present.  It never writes memory, calls a provider, approves a
candidate or applies a change.  Promotion remains on the signed level-zero
Human Authority + Living Kernel path.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Callable, Iterable, Mapping
from datetime import datetime, timezone
from typing import Any

from . import (
    oap_core_autonomy,
    organism_autonomy,
    smi_completion_contract,
    smi_runtime_autonomy,
)

MODE = "GOVERNED_RECURSIVE_REVIEW"
LOOP_STAGES = (
    "SENSE",
    "THINK",
    "REMEMBER",
    "RECOMMEND",
    "APPROVE",
    "ACT",
    "LOG",
)
HARD_LOCKS = (
    "self_approval",
    "self_apply_improvement",
    "self_deploy",
    "permission_change",
    "constitution_change",
    "unregistered_agent_creation",
    "production_migration",
    "secret_export",
    "payment_or_value_transfer",
    "real_world_dispatch",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_cycle(
    reader: Callable[[], Mapping[str, Any]], *, error_code: str
) -> dict[str, Any]:
    """Read one evidence layer and turn any failure into explicit unknown state."""

    try:
        result = reader()
    except Exception:  # noqa: BLE001 - improvement truth must fail closed.
        return {
            "available": False,
            "error": error_code,
            "consequential_action": False,
        }
    if not isinstance(result, Mapping):
        return {
            "available": False,
            "error": error_code,
            "consequential_action": False,
        }
    return {"available": True, **dict(result)}


def _values(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,) if value.strip() else ()
    if not isinstance(value, Iterable) or isinstance(value, (bytes, Mapping)):
        return ()
    return tuple(str(item).strip() for item in value if str(item).strip())


def _collect_weaknesses(
    smi: Mapping[str, Any],
    core: Mapping[str, Any],
    organism: Mapping[str, Any],
    completion: Mapping[str, Any],
) -> tuple[str, ...]:
    weaknesses: list[str] = []

    for label, snapshot in (
        ("smi", smi),
        ("oap_core", core),
        ("organism", organism),
        ("completion", completion),
    ):
        if snapshot.get("available") is not True:
            weaknesses.append(f"unknown:{label}_evidence")

    smi_proposal = smi.get("proposal")
    if isinstance(smi_proposal, Mapping):
        weaknesses.extend(_values(smi_proposal.get("evidence")))

    core_coherence = core.get("coherence")
    if isinstance(core_coherence, Mapping):
        weaknesses.extend(_values(core_coherence.get("issues")))

    organism_coherence = organism.get("coherence")
    if isinstance(organism_coherence, Mapping):
        weaknesses.extend(_values(organism_coherence.get("issues")))

    for gate in completion.get("missing_proof_gates", ()) or ():
        if isinstance(gate, Mapping):
            gate_id = str(gate.get("id") or "").strip()
            if gate_id:
                weaknesses.append(f"proof_required:{gate_id}")

    # Preserve the strongest first-seen signal, deduplicate, and bound scope.
    return tuple(dict.fromkeys(weaknesses))[:21]


def status() -> dict[str, Any]:
    """Return the stable authority contract without running a live probe."""

    return {
        "component": "SMI Governed Recursive Improvement",
        "configured": True,
        "mode": MODE,
        "loop": LOOP_STAGES,
        "automatic_observation": True,
        "automatic_weakness_detection": True,
        "automatic_candidate_preparation": True,
        "automatic_approval": False,
        "automatic_apply": False,
        "automatic_deploy": False,
        "sandbox_required": True,
        "reversibility_required": True,
        "signed_human_approval_required": True,
        "living_kernel_required": True,
        "hard_locks": HARD_LOCKS,
        "human_authority_final": True,
        "no_fake_green": True,
    }


def run_cycle() -> dict[str, Any]:
    """Run one live evidence review and prepare, but never apply, a candidate."""

    smi = _safe_cycle(
        smi_runtime_autonomy.run_cycle,
        error_code="smi_runtime_evidence_unavailable",
    )
    core = _safe_cycle(
        oap_core_autonomy.run_cycle,
        error_code="oap_core_evidence_unavailable",
    )
    organism = _safe_cycle(
        organism_autonomy.run_cycle,
        error_code="organism_evidence_unavailable",
    )
    completion = _safe_cycle(
        smi_completion_contract.completion_status,
        error_code="completion_evidence_unavailable",
    )
    weaknesses = _collect_weaknesses(smi, core, organism, completion)

    baseline = str(
        os.environ.get("RENDER_GIT_COMMIT")
        or os.environ.get("OAP_ENV_REVISION")
        or "unknown"
    )[:120]
    fingerprint_material = {
        "baseline": baseline,
        "weaknesses": weaknesses,
        "mode": MODE,
    }
    canonical = json.dumps(
        fingerprint_material,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    evidence_digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    core_observation = core.get("observation")
    if not isinstance(core_observation, Mapping):
        core_observation = {}
    smi_gate = smi.get("controlled_self_improvement_runtime")
    if not isinstance(smi_gate, Mapping):
        smi_gate = {}

    candidate: dict[str, Any] | None = None
    if weaknesses:
        candidate = {
            "candidate_id": f"rsi-{evidence_digest[:12]}",
            "baseline_version": baseline,
            "candidate_version": f"candidate-{evidence_digest[12:24]}",
            "evidence_digest": evidence_digest,
            "review_targets": weaknesses,
            "scope": "proposal_only",
            "reversible": True,
            "sandbox_passed": False,
            "promotion_ready": False,
        }

    continuous_cycle_proven = bool(core_observation.get("runtime_worker_fresh"))
    governance_evidence_ready = bool(smi_gate.get("ready"))
    live_green = bool(
        not weaknesses and continuous_cycle_proven and governance_evidence_ready
    )

    return {
        "kind": "smi_governed_recursive_improvement_cycle",
        "generated_at": _now(),
        "mode": MODE,
        "light": "green" if live_green else "orange",
        "output_state": "SYSTEM_LOG_ONLY" if live_green else "REVIEW_REQUIRED",
        "baseline_version": baseline,
        "evidence_digest": evidence_digest,
        "weaknesses": weaknesses,
        "candidate": candidate,
        "proof": {
            "live_cycle_ran": True,
            "smi_gates_green": int(smi.get("gates_green", 0) or 0),
            "smi_gates_total": int(smi.get("gates_total", 0) or 0),
            "production_store_reachable": bool(
                completion.get("runtime_evidence", {}).get("store_reachable")
                if isinstance(completion.get("runtime_evidence"), Mapping)
                else False
            ),
            "continuous_cycle_proven": continuous_cycle_proven,
            "governance_evidence_ready": governance_evidence_ready,
            "sandbox_passed": False,
            "signed_approval_recorded": False,
            "promotion_executed": False,
            "hrm_record_created_by_this_view": False,
        },
        "layers": {
            "smi": smi,
            "oap_core": core,
            "organism": organism,
            "completion": completion,
        },
        "loop": LOOP_STAGES,
        "hard_locks": HARD_LOCKS,
        "recommendation": (
            "Review the evidence-bound candidate, run an isolated sandbox and issue "
            "a signed level-zero approval before any Living Kernel promotion."
            if candidate
            else "Maintain the current configuration and continue evidence observation."
        ),
        "human_authority_final": True,
        "independent_approval": False,
        "independent_execution": False,
        "independent_apply": False,
        "consequential_action": False,
        "no_fake_green": True,
    }
