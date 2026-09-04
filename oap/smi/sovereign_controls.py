"""Central fail-closed sovereignty controls for the single SMI brain.

These controls define technical ownership and execution boundaries. They do not
create legal or governmental sovereignty, a second brain, achieved AGI or
autonomous authority. Consequential execution remains bound to level-zero Human
Authority approval.

Master Full Sovereignty is evidence-based. The control plane only reports it as
active when every required custody, infrastructure, egress, recovery and supply-
chain attestation is present. Hosted dependencies therefore cannot silently turn
a sovereignty claim green.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Mapping
from typing import Any

_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})
_ALLOWED_FOUNDER_ACTIONS = frozenset(
    {
        "github.branch.create",
        "github.file.write",
        "github.pr.create",
    }
)
_LOCAL_PROVIDER_IDS = frozenset(
    {"ollama", "llama_cpp", "vllm_local", "sglang_local"}
)
_MASTER_ATTESTATION_ENV: tuple[tuple[str, str], ...] = (
    ("key_custody_local", "OAP_SOVEREIGN_KEYS_LOCAL"),
    ("data_custody_self_hosted", "OAP_SOVEREIGN_DATA_SELF_HOSTED"),
    ("model_custody_local", "OAP_SOVEREIGN_MODEL_LOCAL"),
    ("source_custody_self_hosted", "OAP_SOVEREIGN_SOURCE_SELF_HOSTED"),
    ("infrastructure_self_hosted", "OAP_SOVEREIGN_INFRA_SELF_HOSTED"),
    ("full_network_egress_controlled", "OAP_SOVEREIGN_NETWORK_EGRESS_CONTROLLED"),
    ("recovery_restore_proven", "OAP_SOVEREIGN_RECOVERY_PROVEN"),
    (
        "observability_first_party",
        "OAP_SOVEREIGN_OBSERVABILITY_FIRST_PARTY",
    ),
    ("supply_chain_attested", "OAP_SOVEREIGN_SUPPLY_CHAIN_ATTESTED"),
)


class SovereignControlViolation(PermissionError):
    """Raised when a request crosses a locked SMI sovereignty boundary."""


def _enabled(name: str) -> bool:
    return os.getenv(name, "").strip().casefold() in _TRUE_VALUES


def _external_provider_allowlist() -> frozenset[str]:
    raw = os.getenv("OAP_SOVEREIGN_EXTERNAL_PROVIDER_ALLOWLIST", "")
    return frozenset(
        item.strip().casefold() for item in raw.split(",") if item.strip()
    )


class SovereignControlPlane:
    """Evaluate immutable SMI authority, ownership and execution controls."""

    component = "SMI Master Sovereign Control Plane"
    policy_version = "smi-master-sovereignty-v2"

    def policy(self) -> dict[str, Any]:
        return {
            "policy_version": self.policy_version,
            "brain_count_added": 0,
            "human_authority_final": True,
            "human_authority_level_required": 0,
            "default_execution": "deny",
            "local_first": True,
            "signed_approval_receipt_required": True,
            "exact_action_digest_required": True,
            "single_use_receipt_required": True,
            "append_only_audit_required": True,
            "action_allowlist": tuple(sorted(_ALLOWED_FOUNDER_ACTIONS)),
            "direct_main_write": False,
            "pr_merge": False,
            "render_deploy": False,
            "production_database_mutation": False,
            "secret_export": False,
            "external_provider_egress_default": "deny",
            "master_mode_external_provider_egress": "local_only",
            "provider_authority": False,
            "agent_authority": False,
            "independent_execution": False,
            "independent_approval": False,
            "emergency_halt_env": "OAP_SOVEREIGN_HALT",
            "master_mode_env": "OAP_MASTER_SOVEREIGN_MODE",
            "master_full_sovereignty_is_evidence_based": True,
            "master_attestation_fields": tuple(
                name for name, _ in _MASTER_ATTESTATION_ENV
            ),
        }

    def policy_fingerprint(self) -> str:
        payload = json.dumps(
            self.policy(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def emergency_halt_active(self) -> bool:
        return _enabled("OAP_SOVEREIGN_HALT")

    def master_mode_requested(self) -> bool:
        return _enabled("OAP_MASTER_SOVEREIGN_MODE")

    def master_attestation(self) -> dict[str, Any]:
        runtime_checks: dict[str, bool] = {
            name: _enabled(env_name)
            for name, env_name in _MASTER_ATTESTATION_ENV
        }
        code_checks: dict[str, bool] = {
            "single_smi_brain_boundary": True,
            "level_zero_human_authority": True,
            "default_deny_execution": True,
            "signed_exact_single_use_approval": True,
            "append_only_audit_boundary": True,
            "provider_router_egress_default_deny": True,
            "emergency_execution_halt": True,
            "provider_and_agent_authority_disabled": True,
        }
        failed_runtime = tuple(
            name for name, passed in runtime_checks.items() if not passed
        )
        runtime_ready = not failed_runtime
        requested = self.master_mode_requested()
        return {
            "architecture_ready": all(code_checks.values()),
            "runtime_ready": runtime_ready,
            "requested": requested,
            "active": bool(requested and runtime_ready),
            "code_checks": code_checks,
            "runtime_checks": runtime_checks,
            "runtime_gap_count": len(failed_runtime),
            "runtime_gaps": failed_runtime,
            "full_sovereignty_claim": bool(requested and runtime_ready),
            "truth_boundary": (
                "Master Full Sovereignty is only active when all custody, local model, "
                "self-hosted infrastructure, complete egress, recovery, first-party "
                "observability and supply-chain evidence is explicitly attested."
            ),
        }

    def provider_allowed(self, provider_id: object, *, local: bool = False) -> bool:
        """Allow local providers; external providers are stricter in master mode."""

        provider = str(provider_id or "").strip().casefold()
        if not provider:
            return False
        is_local = bool(local or provider in _LOCAL_PROVIDER_IDS)
        if self.master_mode_requested():
            return is_local
        if is_local:
            return True
        return provider in _external_provider_allowlist()

    def execution_review(
        self,
        *,
        action_type: object,
        is_human_authority: bool,
        authority_level: object,
        signed_receipt: bool,
        exact_action_digest: bool,
        receipt_unconsumed: bool,
        audit_ready: bool,
    ) -> dict[str, Any]:
        action = str(action_type or "").strip()
        try:
            level = int(authority_level)
        except (TypeError, ValueError):
            level = -1

        master = self.master_attestation()
        master_gate = bool(
            not self.master_mode_requested() or master["runtime_ready"]
        )
        checks: Mapping[str, bool] = {
            "emergency_halt_clear": not self.emergency_halt_active(),
            "action_allowlisted": action in _ALLOWED_FOUNDER_ACTIONS,
            "human_authority": bool(is_human_authority),
            "authority_level_zero": level == 0,
            "signed_receipt": bool(signed_receipt),
            "exact_action_digest": bool(exact_action_digest),
            "receipt_unconsumed": bool(receipt_unconsumed),
            "audit_ready": bool(audit_ready),
            "master_sovereignty_ready_if_requested": master_gate,
        }
        failed = tuple(name for name, passed in checks.items() if not passed)
        return {
            "allowed": not failed,
            "failed_checks": failed,
            "checks": dict(checks),
            "action_type": action,
            "default_execution": "deny",
            "master_mode_requested": self.master_mode_requested(),
            "master_sovereignty_active": master["active"],
            "human_authority_final": True,
        }

    def require_execution(self, **kwargs: Any) -> dict[str, Any]:
        review = self.execution_review(**kwargs)
        if not review["allowed"]:
            failures = ",".join(review["failed_checks"])
            raise SovereignControlViolation(
                f"SMI sovereign execution gate blocked: {failures}"
            )
        return review

    def status(self) -> dict[str, Any]:
        policy = self.policy()
        external_allowlist = _external_provider_allowlist()
        master = self.master_attestation()
        if master["active"]:
            sovereignty_grade = "MASTER_FULL"
        elif master["architecture_ready"]:
            sovereignty_grade = "CONTROLLED_HOSTED_OR_UNPROVEN"
        else:
            sovereignty_grade = "NOT_READY"
        return {
            "component": self.component,
            "ready": bool(master["architecture_ready"]),
            "policy_version": self.policy_version,
            "policy_fingerprint": self.policy_fingerprint(),
            "brain_count": 0,
            "emergency_halt_active": self.emergency_halt_active(),
            "execution_enabled": not self.emergency_halt_active(),
            "master_mode_requested": master["requested"],
            "master_full_sovereignty_ready": master["runtime_ready"],
            "master_full_sovereignty_active": master["active"],
            "master_runtime_gap_count": master["runtime_gap_count"],
            "master_runtime_gaps": master["runtime_gaps"],
            "full_sovereignty_claim": master["full_sovereignty_claim"],
            "sovereignty_grade": sovereignty_grade,
            "external_provider_allowlist_count": len(external_allowlist),
            "external_provider_egress_default": policy[
                "external_provider_egress_default"
            ],
            "master_mode_external_provider_egress": policy[
                "master_mode_external_provider_egress"
            ],
            "local_first": True,
            "secret_export": False,
            "direct_main_write": False,
            "production_database_mutation": False,
            "independent_execute": False,
            "independent_approval": False,
            "human_authority_final": True,
            "master_attestation": master,
        }
