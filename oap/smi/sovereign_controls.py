"""Central fail-closed sovereignty controls for the single SMI brain.

These controls define technical ownership and execution boundaries. They do not
create legal or governmental sovereignty, a second brain, or autonomous authority.
Consequential execution remains bound to level-zero Human Authority approval.
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
_LOCAL_PROVIDER_IDS = frozenset({"ollama", "llama_cpp", "vllm_local", "sglang_local"})


class SovereignControlViolation(PermissionError):
    """Raised when a request crosses a locked SMI sovereignty boundary."""


def _enabled(name: str) -> bool:
    return os.getenv(name, "").strip().casefold() in _TRUE_VALUES


def _external_provider_allowlist() -> frozenset[str]:
    raw = os.getenv("OAP_SOVEREIGN_EXTERNAL_PROVIDER_ALLOWLIST", "")
    return frozenset(
        item.strip().casefold()
        for item in raw.split(",")
        if item.strip()
    )


class SovereignControlPlane:
    """Evaluate immutable SMI authority, ownership and execution controls."""

    component = "SMI Sovereign Control Plane"
    policy_version = "smi-sovereign-controls-v1"

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
            "provider_authority": False,
            "agent_authority": False,
            "independent_execution": False,
            "independent_approval": False,
            "emergency_halt_env": "OAP_SOVEREIGN_HALT",
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

    def provider_allowed(self, provider_id: object, *, local: bool = False) -> bool:
        """Allow local providers; external providers require an explicit allowlist."""

        provider = str(provider_id or "").strip().casefold()
        if not provider:
            return False
        if local or provider in _LOCAL_PROVIDER_IDS:
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

        checks: Mapping[str, bool] = {
            "emergency_halt_clear": not self.emergency_halt_active(),
            "action_allowlisted": action in _ALLOWED_FOUNDER_ACTIONS,
            "human_authority": bool(is_human_authority),
            "authority_level_zero": level == 0,
            "signed_receipt": bool(signed_receipt),
            "exact_action_digest": bool(exact_action_digest),
            "receipt_unconsumed": bool(receipt_unconsumed),
            "audit_ready": bool(audit_ready),
        }
        failed = tuple(name for name, passed in checks.items() if not passed)
        return {
            "allowed": not failed,
            "failed_checks": failed,
            "checks": dict(checks),
            "action_type": action,
            "default_execution": "deny",
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
        return {
            "component": self.component,
            "ready": True,
            "policy_version": self.policy_version,
            "policy_fingerprint": self.policy_fingerprint(),
            "brain_count": 0,
            "emergency_halt_active": self.emergency_halt_active(),
            "execution_enabled": not self.emergency_halt_active(),
            "external_provider_allowlist_count": len(external_allowlist),
            "external_provider_egress_default": policy[
                "external_provider_egress_default"
            ],
            "local_first": True,
            "secret_export": False,
            "direct_main_write": False,
            "production_database_mutation": False,
            "independent_execute": False,
            "independent_approval": False,
            "human_authority_final": True,
        }
