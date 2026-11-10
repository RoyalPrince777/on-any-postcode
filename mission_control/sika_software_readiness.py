"""Canonical software-only readiness view for SIKA.

This module answers one narrow question: is the first-party SIKA software stack
present and internally wired, independent of external licensing, provider
contracts, reserves, live settlement access, or regulator authorisation?

It never authorises payments, weakens execution controls, moves funds, or
changes the regulated execution gate. External evidence remains owned by the
existing governed execution path.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from . import (
    sika_account_engine,
    sika_accounting_controls,
    sika_atomic_payment,
    sika_balance_engine,
    sika_card_controls,
    sika_customer_view,
    sika_double_entry,
    sika_journal_store,
    sika_payment_disputes,
    sika_payment_orchestrator,
    sika_payment_reservations,
    sika_payment_submission_evidence,
    sika_reconciliation_exception_store,
    sika_refund_intent,
    sika_runtime_reconciliation,
    sika_treasury_controls,
)


@dataclass(frozen=True)
class SoftwareReadiness:
    checks: dict[str, bool]
    ready: bool
    percent: int
    external_execution_ready: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "checks": dict(self.checks),
            "ready": self.ready,
            "percent": self.percent,
            "external_execution_ready": self.external_execution_ready,
            "scope": "software_only",
            "money_movement_enabled": False,
        }


def _check(fn: Callable[[], dict[str, object]], key: str) -> bool:
    return bool(fn().get(key))


def assess() -> SoftwareReadiness:
    """Assess first-party software components without external proof."""

    checks = {
        "account_engine": _check(
            sika_account_engine.status, "persistent_account_identity"
        ),
        "account_owner_resolution": _check(
            sika_account_engine.status, "owner_resolution"
        ),
        "accounting_controls": _check(
            sika_accounting_controls.status, "closed_period_posting_block"
        ),
        "canonical_balance_engine": _check(
            sika_balance_engine.status, "ledger_derived"
        ),
        "payment_reservations": _check(
            sika_payment_reservations.status, "persistent_holds"
        ),
        "atomic_payment_creation": _check(
            sika_atomic_payment.status, "single_database_transaction"
        ),
        "double_entry": _check(
            sika_double_entry.status, "validates_debits_and_credits"
        ),
        "journal_store": _check(sika_journal_store.status, "append_only"),
        "payment_orchestrator": _check(
            sika_payment_orchestrator.status, "persistent_payment_intent"
        ),
        "terminal_hold_lifecycle": _check(
            sika_payment_orchestrator.status, "terminal_hold_lifecycle_sync"
        ),
        "authenticated_customer_view": _check(
            sika_customer_view.status, "owner_scoped"
        ),
        "payment_disputes": _check(
            sika_payment_disputes.status, "persistent_dispute_cases"
        ),
        "submission_evidence": _check(
            sika_payment_submission_evidence.status,
            "durable_submission_receipts",
        ),
        "refund_intent": _check(
            sika_refund_intent.status, "persistent_refund_intent"
        ),
        "runtime_reconciliation": _check(
            sika_runtime_reconciliation.status, "first_party"
        ),
        "reconciliation_exceptions": _check(
            sika_reconciliation_exception_store.status,
            "persistent_exception_cases",
        ),
        "card_controls": _check(sika_card_controls.status, "card_account_binding"),
        "treasury_controls": bool(sika_treasury_controls.status().get("first_party")),
    }
    passed = sum(1 for value in checks.values() if value)
    percent = round((passed / len(checks)) * 100) if checks else 0
    return SoftwareReadiness(
        checks=checks,
        ready=all(checks.values()),
        percent=percent,
        external_execution_ready=False,
    )


def status() -> dict[str, object]:
    result = assess()
    return {
        "system": "SIKA Software Readiness",
        "first_party": True,
        "scope": "software_only",
        "software_ready": result.ready,
        "software_percent": result.percent,
        "external_responsibilities_excluded_from_score": [
            "licensing_and_regulatory_authorisation",
            "payment_provider_contracts",
            "reserves_and_funding",
            "live_settlement_access",
            "external_bank_or_rail_activation",
        ],
        "execution_gate_bypassed": False,
        "payment_execution_enabled": False,
        "money_movement_enabled": False,
        "human_authority_final": True,
    }
