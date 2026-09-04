"""Bounded autonomous review for Sovereign Megaverse Intelligence.

SMI may observe its own reported component state, check coherence, verify the
Founder-approved canonical memory manifest, identify recovery attention and
propose controlled improvements without waiting for a user request. It never
gains independent authority to approve, execute, promote, deploy or perform
consequential real-world actions.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from .canonical_memory import status as canonical_memory_status

AUTONOMY_MODE = "BOUNDED_AUTONOMOUS"
BLOCKED_ACTIONS = (
    "approve_recommendation",
    "self_promote",
    "self_apply_improvement",
    "deploy",
    "publish_external",
    "payment_capture",
    "money_transfer",
    "driver_dispatch",
    "permission_change",
    "role_change",
    "production_migration",
    "esim_activation",
    "carrier_switch",
    "public_precise_tracking",
)


class SMIAutonomyEngine:
    """Run non-consequential SMI review cycles from observed state."""

    def status(self) -> dict[str, Any]:
        memory = canonical_memory_status()
        return {
            "component": "SMI Autonomy",
            "mode": AUTONOMY_MODE,
            "configured": True,
            "automatic_observation": True,
            "automatic_coherence_review": True,
            "automatic_memory_integrity_review": True,
            "automatic_recovery_review": True,
            "automatic_improvement_proposals": True,
            "canonical_memory_ready": bool(memory.get("ready")),
            "canonical_memory_revision": memory.get("revision"),
            "canonical_memory_digest": memory.get("digest"),
            "independent_execution": False,
            "independent_approval": False,
            "independent_apply": False,
            "human_authority_final": True,
            "blocked_actions": BLOCKED_ACTIONS,
        }

    def observe(
        self,
        components: Iterable[Mapping[str, object]],
        self_model: Mapping[str, object],
    ) -> dict[str, Any]:
        records = tuple(components)
        degraded = tuple(str(item) for item in self_model.get("degraded_components", ()))
        unknown = tuple(str(item) for item in self_model.get("unknown_components", ()))
        ready_count = sum(item.get("ready") is True for item in records)
        return {
            "kind": "smi_autonomous_observation",
            "components_checked": len(records),
            "components_ready": ready_count,
            "overall_ready": bool(self_model.get("overall_ready")),
            "degraded_components": degraded,
            "unknown_components": unknown,
            "read_only": True,
            "sentience_claimed": False,
            "consciousness_claimed": False,
            "consequential_action": False,
        }

    def memory_review(self) -> dict[str, Any]:
        """Verify manifest integrity/provenance without mutating HRM or code."""

        memory = canonical_memory_status()
        return {
            "kind": "smi_autonomous_memory_review",
            "ready": bool(memory.get("ready")),
            "revision": memory.get("revision"),
            "record_count": int(memory.get("record_count", 0) or 0),
            "digest": memory.get("digest"),
            "latest_founder_correction_wins": bool(
                memory.get("latest_founder_correction_wins")
            ),
            "private_chain_of_thought_included": bool(
                memory.get("private_chain_of_thought_included")
            ),
            "credentials_or_secrets_included": bool(
                memory.get("credentials_or_secrets_included")
            ),
            "read_only": True,
            "consequential_action": False,
        }

    def coherence_review(self, coherence: Mapping[str, object]) -> dict[str, Any]:
        conflicts = tuple(coherence.get("conflicts", ()))
        return {
            "kind": "smi_autonomous_coherence_review",
            "coherent": bool(coherence.get("coherent")),
            "checked_components": int(coherence.get("checked_components", 0) or 0),
            "uncertainty": float(coherence.get("uncertainty", 0.0) or 0.0),
            "conflict_count": len(conflicts),
            "human_review_required": bool(coherence.get("human_review_required")),
            "review_only": True,
            "consequential_action": False,
        }

    def recovery_review(self, observation: Mapping[str, object]) -> dict[str, Any]:
        degraded = tuple(observation.get("degraded_components", ()))
        unknown = tuple(observation.get("unknown_components", ()))
        return {
            "kind": "smi_autonomous_recovery_review",
            "recovery_attention": bool(degraded or unknown),
            "safe_actions": (
                "reobserve_component_state",
                "recheck_coherence",
                "verify_canonical_memory_digest",
                "retry_nonconsequential_analysis",
            ),
            "destructive_recovery_allowed": False,
            "authority_change_allowed": False,
            "consequential_action": False,
        }

    def improvement_proposal(
        self,
        observation: Mapping[str, object],
        coherence: Mapping[str, object],
        evolution: Mapping[str, object],
        memory: Mapping[str, object] | None = None,
    ) -> dict[str, Any]:
        issues: list[str] = []
        for component in observation.get("degraded_components", ()):
            issues.append(f"degraded:{component}")
        for component in observation.get("unknown_components", ()):
            issues.append(f"unknown:{component}")
        if not coherence.get("coherent"):
            issues.append("coherence_conflict")
        if memory is not None and not memory.get("ready"):
            issues.append("canonical_memory_integrity")

        proposed = tuple(f"review:{issue}" for issue in issues[:16])
        if not proposed:
            proposed = ("maintain_current_configuration",)

        return {
            "kind": "smi_autonomous_improvement_proposal",
            "evidence": tuple(issues[:16]),
            "proposed_actions": proposed,
            "controlled_self_improvement_ready": bool(evolution.get("ready")),
            "requires_human_approval": True,
            "sandbox_required": True,
            "reversibility_required": True,
            "independent_apply": False,
            "consequential_action": False,
        }

    def run_cycle(
        self,
        *,
        components: Iterable[Mapping[str, object]],
        self_model: Mapping[str, object],
        coherence: Mapping[str, object],
        evolution: Mapping[str, object],
    ) -> dict[str, Any]:
        records = tuple(components)
        observation = self.observe(records, self_model)
        memory = self.memory_review()
        coherence_result = self.coherence_review(coherence)
        recovery = self.recovery_review(observation)
        proposal = self.improvement_proposal(
            observation,
            coherence_result,
            evolution,
            memory,
        )
        return {
            "kind": "smi_autonomy_cycle",
            "mode": AUTONOMY_MODE,
            "observation": observation,
            "memory": memory,
            "coherence": coherence_result,
            "recovery": recovery,
            "proposal": proposal,
            "human_authority_final": True,
            "independent_approval": False,
            "independent_execution": False,
            "independent_apply": False,
            "consequential_action": False,
        }
