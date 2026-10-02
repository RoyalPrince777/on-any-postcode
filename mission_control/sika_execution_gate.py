"""Canonical SIKA execution-readiness gate.

Composes Treasury health, provider evidence, regulator evidence and production
proof. Regulator and production readiness are both derived from governed
durable evidence stores; callers cannot self-assert either state. This module
never executes payments or moves funds.
"""
from __future__ import annotations

from dataclasses import dataclass

from . import (
    bank_authorisation,
    bank_authorisation_store,
    bank_permission_scope,
    sika_production_evidence_store,
    sika_provider_adapter,
    sika_treasury_controls,
)


@dataclass(frozen=True)
class ExecutionReadiness:
    treasury_healthy: bool
    provider_review_ready: bool
    regulator_authorisation_proven: bool
    production_gate_passed: bool
    human_authority_required: bool
    execution_authorised: bool
    money_moved: bool = False

    def as_dict(self) -> dict[str, bool]:
        return {
            "treasury_healthy": self.treasury_healthy,
            "provider_review_ready": self.provider_review_ready,
            "regulator_authorisation_proven": self.regulator_authorisation_proven,
            "production_gate_passed": self.production_gate_passed,
            "human_authority_required": self.human_authority_required,
            "execution_authorised": self.execution_authorised,
            "money_moved": self.money_moved,
        }


def _regulator_authorisation_proven() -> bool:
    readiness = bank_authorisation_store.readiness_status()
    return bool(readiness.get("authorised_bank"))


def _production_gate_passed() -> bool:
    readiness = sika_production_evidence_store.readiness_status()
    return bool(readiness.get("production_gate_passed"))


def assess(
    *,
    treasury: sika_treasury_controls.TreasurySnapshot,
    provider_evidence: sika_provider_adapter.ProviderEvidence,
    human_authority_approved: bool = False,
) -> ExecutionReadiness:
    """Return a governed readiness decision; never execute a payment."""

    treasury_gate = sika_treasury_controls.release_gate(treasury)
    provider_gate = sika_provider_adapter.release_review(provider_evidence)

    treasury_healthy = bool(treasury_gate["liquidity_healthy"])
    provider_ready = bool(provider_gate["may_enter_execution_review"])
    regulator_authorisation_proven = _regulator_authorisation_proven()
    production_gate_passed = _production_gate_passed()

    permission_scope_allows = bank_permission_scope.capability_allowed(
        "execute_payments"
    )
    regulated_capability_allowed = bank_authorisation.capability_allowed(
        "execute_payments",
        regulator_authorisation_proven=regulator_authorisation_proven,
        production_gate_passed=production_gate_passed,
        permission_scope_allows=permission_scope_allows,
    )

    authorised = all(
        (
            treasury_healthy,
            provider_ready,
            regulated_capability_allowed,
            human_authority_approved,
        )
    )

    return ExecutionReadiness(
        treasury_healthy=treasury_healthy,
        provider_review_ready=provider_ready,
        regulator_authorisation_proven=regulator_authorisation_proven,
        production_gate_passed=production_gate_passed,
        human_authority_required=True,
        execution_authorised=authorised,
        money_moved=False,
    )


def capability_matrix() -> dict[str, bool]:
    """Expose regulated capability readiness from governed evidence stores."""

    regulator_authorisation_proven = _regulator_authorisation_proven()
    production_gate_passed = _production_gate_passed()
    return {
        capability: bank_authorisation.capability_allowed(
            capability,
            regulator_authorisation_proven=regulator_authorisation_proven,
            production_gate_passed=production_gate_passed,
            permission_scope_allows=bank_permission_scope.capability_allowed(capability),
        )
        for capability in sorted(bank_authorisation.REGULATED_CAPABILITIES)
    }


def status() -> dict[str, object]:
    return {
        "system": "SIKA Execution Readiness Gate",
        "composes_treasury": True,
        "composes_provider_adapter": True,
        "composes_bank_authorisation": True,
        "composes_permission_scope": True,
        "composes_production_evidence": True,
        "regulator_authorisation_source": "durable_governed_evidence_store",
        "production_readiness_source": "durable_governed_evidence_store",
        "permission_scope_source": "accepted_part4a_permission_scope",
        "caller_regulator_override_allowed": False,
        "caller_production_override_allowed": False,
        "payment_execution_enabled": False,
        "money_movement_enabled": False,
        "regulator_evidence_required": True,
        "production_gate_required": True,
        "human_authority_required": True,
        "bypass_path_available": False,
    }
