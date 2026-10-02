"""Canonical SIKA execution-readiness gate.

Composes Treasury health, provider evidence and regulator/production proof.
This module never executes payments or moves funds.
"""
from __future__ import annotations

from dataclasses import dataclass

from . import bank_authorisation, sika_provider_adapter, sika_treasury_controls


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


def assess(
    *,
    treasury: sika_treasury_controls.TreasurySnapshot,
    provider_evidence: sika_provider_adapter.ProviderEvidence,
    regulator_authorisation_proven: bool = False,
    production_gate_passed: bool = False,
    human_authority_approved: bool = False,
) -> ExecutionReadiness:
    """Return a deterministic readiness decision; never execute a payment."""

    treasury_gate = sika_treasury_controls.release_gate(treasury)
    provider_gate = sika_provider_adapter.release_review(provider_evidence)

    treasury_healthy = bool(treasury_gate["liquidity_healthy"])
    provider_ready = bool(provider_gate["may_enter_execution_review"])

    regulated_capability_allowed = bank_authorisation.capability_allowed(
        "execute_payments",
        regulator_authorisation_proven=regulator_authorisation_proven,
        production_gate_passed=production_gate_passed,
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
        regulator_authorisation_proven=bool(regulator_authorisation_proven),
        production_gate_passed=bool(production_gate_passed),
        human_authority_required=True,
        execution_authorised=authorised,
        money_moved=False,
    )


def capability_matrix(
    *,
    regulator_authorisation_proven: bool = False,
    production_gate_passed: bool = False,
) -> dict[str, bool]:
    """Expose regulated capabilities without creating an execution path."""

    return {
        capability: bank_authorisation.capability_allowed(
            capability,
            regulator_authorisation_proven=regulator_authorisation_proven,
            production_gate_passed=production_gate_passed,
        )
        for capability in sorted(bank_authorisation.REGULATED_CAPABILITIES)
    }


def status() -> dict[str, object]:
    return {
        "system": "SIKA Execution Readiness Gate",
        "composes_treasury": True,
        "composes_provider_adapter": True,
        "composes_bank_authorisation": True,
        "payment_execution_enabled": False,
        "money_movement_enabled": False,
        "regulator_evidence_required": True,
        "production_gate_required": True,
        "human_authority_required": True,
        "bypass_path_available": False,
    }
