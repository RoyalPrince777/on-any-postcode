"""First-party OAP Banking Intelligence read-only world state.

This module composes existing SIKA, treasury, provider, regulator, permission
and production owners. It does not create a second ledger, execute payments or
move money. Its job is to present one deterministic banking truth snapshot.
"""
from __future__ import annotations

from dataclasses import dataclass

from . import (
    bank_authorisation,
    bank_authorisation_store,
    bank_permission_scope,
    oap_blockchain_accounting_anchor,
    sika_accounting_controls,
    sika_accounting_intelligence,
    sika_alm_forecasting_intelligence,
    sika_closing_retained_earnings,
    sika_double_entry,
    sika_financial_intelligence,
    sika_financial_statements_intelligence,
    sika_fraud_financial_crime_intelligence,
    sika_journal_store,
    sika_multi_currency_revaluation,
    sika_production_evidence_store,
    sika_provider_adapter,
    sika_runtime_reconciliation,
    sika_treasury_controls,
)

GROUP_NAME = "OAP Global Banking Group"
CONTINENTAL_FAMILY = (
    "Africa Crown Bank",
    "Europa Crown Bank",
    "Asia Crown Bank",
    "North America Crown Bank",
    "South America Crown Bank",
    "Pacific Crown Bank",
    "Antarctic Reserve",
)
FIRST_JURISDICTIONS = {
    "Africa Crown Bank": "Ghana",
    "Europa Crown Bank": "United Kingdom",
}


@dataclass(frozen=True)
class BankingWorldState:
    treasury_healthy: bool
    provider_review_ready: bool
    regulator_authorisation_proven: bool
    production_gate_passed: bool
    permission_scope_allows_payments: bool
    may_enter_human_review: bool
    money_moved: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "treasury_healthy": self.treasury_healthy,
            "provider_review_ready": self.provider_review_ready,
            "regulator_authorisation_proven": self.regulator_authorisation_proven,
            "production_gate_passed": self.production_gate_passed,
            "permission_scope_allows_payments": (
                self.permission_scope_allows_payments
            ),
            "may_enter_human_review": self.may_enter_human_review,
            "money_moved": self.money_moved,
        }


def observe(
    *,
    treasury: sika_treasury_controls.TreasurySnapshot,
    provider_evidence: sika_provider_adapter.ProviderEvidence,
) -> BankingWorldState:
    """Compose current banking readiness without authorising execution."""

    treasury_gate = sika_treasury_controls.release_gate(treasury)
    provider_gate = sika_provider_adapter.release_review(provider_evidence)
    regulator = bank_authorisation_store.readiness_status()
    production = sika_production_evidence_store.readiness_status()

    treasury_healthy = bool(treasury_gate["liquidity_healthy"])
    provider_review_ready = bool(provider_gate["may_enter_execution_review"])
    regulator_authorisation_proven = bool(regulator.get("authorised_bank"))
    production_gate_passed = bool(production.get("production_gate_passed"))
    permission_scope_allows_payments = bank_permission_scope.capability_allowed(
        "execute_payments"
    )

    may_enter_human_review = all(
        (
            treasury_healthy,
            provider_review_ready,
            regulator_authorisation_proven,
            production_gate_passed,
            permission_scope_allows_payments,
        )
    )

    return BankingWorldState(
        treasury_healthy=treasury_healthy,
        provider_review_ready=provider_review_ready,
        regulator_authorisation_proven=regulator_authorisation_proven,
        production_gate_passed=production_gate_passed,
        permission_scope_allows_payments=permission_scope_allows_payments,
        may_enter_human_review=may_enter_human_review,
        money_moved=False,
    )


def capability_world_state() -> dict[str, bool]:
    """Expose exact regulated-capability readiness from governed owners."""

    regulator = bank_authorisation_store.readiness_status()
    production = sika_production_evidence_store.readiness_status()
    regulator_proven = bool(regulator.get("authorised_bank"))
    production_proven = bool(production.get("production_gate_passed"))

    return {
        capability: bank_authorisation.capability_allowed(
            capability,
            regulator_authorisation_proven=regulator_proven,
            production_gate_passed=production_proven,
            permission_scope_allows=(
                bank_permission_scope.capability_allowed(capability)
            ),
        )
        for capability in sorted(bank_authorisation.REGULATED_CAPABILITIES)
    }


def status() -> dict[str, object]:
    """Describe the real composition boundary and remaining integration gaps."""

    return {
        "system": "OAP Banking Intelligence OS",
        "banking_group": GROUP_NAME,
        "continental_family": list(CONTINENTAL_FAMILY),
        "first_jurisdictions": dict(FIRST_JURISDICTIONS),
        "mode": "read_only_world_state",
        "first_party": True,
        "composes_sika_treasury": True,
        "composes_provider_evidence": True,
        "composes_regulator_evidence": True,
        "composes_permission_scope": True,
        "composes_production_evidence": True,
        "duplicate_ledger_created": False,
        "payment_execution_enabled": False,
        "money_movement_enabled": False,
        "human_authority_final": True,
        "blockchain_integrity_integrated": bool(
            oap_blockchain_accounting_anchor.status()["first_party"]
        ),
        "bank_grade_double_entry_integrated": bool(
            sika_double_entry.status()["validates_debits_and_credits"]
        ),
        "persistent_journal_store_integrated": bool(
            sika_journal_store.status()["append_only"]
        ),
        "financial_intelligence_integrated": bool(
            sika_financial_intelligence.status()["first_party"]
        ),
        "financial_statements_intelligence_integrated": bool(
            sika_financial_statements_intelligence.status()["first_party"]
        ),
        "multi_currency_revaluation_integrated": bool(
            sika_multi_currency_revaluation.status()["first_party"]
        ),
        "fraud_financial_crime_intelligence_integrated": bool(
            sika_fraud_financial_crime_intelligence.status()["first_party"]
        ),
        "accounting_intelligence_integrated": bool(
            sika_accounting_intelligence.status()["first_party"]
        ),
        "accounting_controls_integrated": bool(
            sika_accounting_controls.status()["closed_period_posting_block"]
        ),
        "alm_forecasting_intelligence_integrated": bool(
            sika_alm_forecasting_intelligence.status()["first_party"]
        ),
        "closing_retained_earnings_integrated": bool(
            sika_closing_retained_earnings.status()["first_party"]
        ),
        "runtime_reconciliation_integrated": bool(
            sika_runtime_reconciliation.status()["first_party"]
        ),
    }
