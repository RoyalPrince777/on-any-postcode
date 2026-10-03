"""First-party intelligence projections for OAP Pay.

This module analyses canonical SIKA account/payment state. It does not mutate
accounts, authorize regulated activity, call providers, post journals, settle
funds, or move money.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from . import (
    market_sika_pod_runtime,
    prince_sovereign_bank,
    sika_account_engine,
    sika_journal_store,
    sika_payment_disputes,
    sika_payment_orchestrator,
    sika_payment_submission_evidence,
    sika_rights_decision_record,
)

PAYMENT_TRANSITIONS = {
    "DRAFT": frozenset({"REVIEW", "CANCELLED"}),
    "REVIEW": frozenset({"AUTHORISED", "CANCELLED"}),
    "AUTHORISED": frozenset({"SUBMITTED", "CANCELLED"}),
    "SUBMITTED": frozenset({"SETTLED", "FAILED"}),
    "SETTLED": frozenset(),
    "FAILED": frozenset(),
    "CANCELLED": frozenset(),
}

ACCOUNT_TRANSITIONS = {
    "OPEN": frozenset({"FROZEN", "CLOSED"}),
    "FROZEN": frozenset({"OPEN", "CLOSED"}),
    "CLOSED": frozenset(),
}


def transition_intelligence(
    *,
    current_status: object,
    target_status: object,
) -> dict[str, Any]:
    current = str(current_status or "").strip().upper()
    target = str(target_status or "").strip().upper()
    if current not in PAYMENT_TRANSITIONS:
        return {
            "valid": False,
            "reason": "unknown_current_payment_state",
            "execution_granted": False,
        }
    if target == current:
        return {
            "valid": True,
            "reason": "idempotent_same_state",
            "execution_granted": False,
        }
    valid = target in PAYMENT_TRANSITIONS[current]
    return {
        "valid": valid,
        "reason": None if valid else "payment_transition_not_allowed",
        "from": current,
        "to": target,
        "terminal_from_state": not bool(PAYMENT_TRANSITIONS[current]),
        "execution_granted": False,
    }


def wallet_intelligence(account: object) -> dict[str, Any]:
    if not isinstance(account, sika_account_engine.BankAccount):
        return {
            "valid": False,
            "reason": "wallet_account_required",
            "balance_known": False,
            "money_movement": False,
        }
    allowed_next = tuple(sorted(ACCOUNT_TRANSITIONS.get(account.status, frozenset())))
    return {
        "valid": True,
        "account_id": account.account_id,
        "status": account.status,
        "currency": account.currency,
        "jurisdiction": account.jurisdiction,
        "customer_activity_allowed": account.customer_activity_allowed,
        "allowed_next_states": allowed_next,
        "balance_known": False,
        "balance_fabricated": False,
        "money_movement": False,
    }


def payment_intelligence(intent: object) -> dict[str, Any]:
    if not isinstance(intent, sika_payment_orchestrator.PaymentIntent):
        return {
            "valid": False,
            "reason": "payment_intent_required",
            "execution_granted": False,
        }
    next_states = tuple(sorted(PAYMENT_TRANSITIONS.get(intent.status, frozenset())))
    return {
        "valid": True,
        "payment_id": intent.payment_id,
        "status": intent.status,
        "payer_account_id": intent.payer_account_id,
        "payee_reference": intent.payee_reference,
        "amount": f"{intent.amount:.2f}",
        "currency": intent.currency,
        "jurisdiction": intent.jurisdiction,
        "next_states": next_states,
        "terminal": intent.terminal,
        "may_submit_to_provider": intent.may_submit_to_provider,
        "execution_granted": False,
        "money_movement": False,
    }


def request_intelligence(request: object) -> dict[str, Any]:
    if not isinstance(request, Mapping):
        return {
            "valid": False,
            "reason": "payment_request_required",
            "creates_debt": False,
            "execution_granted": False,
        }
    request_id = str(request.get("request_id") or "").strip()
    requester = str(request.get("requester_reference") or "").strip()
    recipient = str(request.get("recipient_reference") or "").strip()
    amount = str(request.get("amount") or "").strip()
    currency = str(request.get("currency") or "").strip().upper()
    complete = bool(request_id and requester and recipient and amount and currency)
    return {
        "valid": complete,
        "reason": None if complete else "payment_request_incomplete",
        "request_id": request_id or None,
        "requester_reference": requester or None,
        "recipient_reference": recipient or None,
        "amount": amount or None,
        "currency": currency or None,
        "recipient_approval_required": True,
        "creates_debt": False,
        "execution_granted": False,
        "money_movement": False,
    }



def merchant_intelligence(merchant: object) -> dict[str, Any]:
    if not isinstance(merchant, Mapping):
        return {
            "valid": False,
            "reason": "merchant_record_required",
            "execution_granted": False,
        }
    merchant_reference = str(merchant.get("merchant_reference") or "").strip()
    certified = merchant.get("certified") is True
    checkout_reference = str(merchant.get("checkout_reference") or "").strip()
    complete = bool(merchant_reference and checkout_reference)
    return {
        "valid": complete,
        "reason": None if complete else "merchant_record_incomplete",
        "merchant_reference": merchant_reference or None,
        "checkout_reference": checkout_reference or None,
        "certified": certified,
        "payment_acceptance_advised": complete and certified,
        "execution_granted": False,
        "money_movement": False,
    }


def activity_intelligence(
    *,
    payment_intent: object,
    submission_evidence: object | None = None,
    dispute: object | None = None,
) -> dict[str, Any]:
    payment = payment_intelligence(payment_intent)
    if not payment.get("valid"):
        return {
            "valid": False,
            "reason": "payment_intent_required",
            "timeline": (),
            "money_movement": False,
        }

    timeline = [str(payment["status"])]
    provider_submission_proven = False
    if isinstance(submission_evidence, sika_payment_submission_evidence.SubmissionEvidence):
        if submission_evidence.payment_id != payment["payment_id"]:
            return {
                "valid": False,
                "reason": "submission_evidence_payment_mismatch",
                "timeline": tuple(timeline),
                "money_movement": False,
            }
        timeline.append(f"PROVIDER_{submission_evidence.outcome}")
        provider_submission_proven = submission_evidence.outcome == "ACCEPTED"

    dispute_open = False
    if isinstance(dispute, sika_payment_disputes.DisputeCase):
        if dispute.payment_id != payment["payment_id"]:
            return {
                "valid": False,
                "reason": "dispute_payment_mismatch",
                "timeline": tuple(timeline),
                "money_movement": False,
            }
        timeline.append(f"DISPUTE_{dispute.status}")
        dispute_open = dispute.status not in {"RESOLVED", "CLOSED"}

    return {
        "valid": True,
        "payment_id": payment["payment_id"],
        "timeline": tuple(timeline),
        "provider_submission_proven": provider_submission_proven,
        "dispute_open": dispute_open,
        "money_movement": False,
        "human_authority_final": True,
    }


def settlement_intelligence(
    *,
    payment_intent: object,
    submission_evidence: object | None,
    journal_batch: object | None,
) -> dict[str, Any]:
    payment = payment_intelligence(payment_intent)
    if not payment.get("valid"):
        return {
            "valid": False,
            "reason": "payment_intent_required",
            "settlement_proven": False,
            "money_movement": False,
        }

    submission = None
    if isinstance(submission_evidence, sika_payment_submission_evidence.SubmissionEvidence):
        submission = {
            "payment_id": submission_evidence.payment_id,
            "provider_reference": submission_evidence.provider_reference,
            "outcome": submission_evidence.outcome,
        }
    gate = market_sika_pod_runtime.payment_submission_receipt_gate(
        payment_intent={
            "payment_id": payment["payment_id"],
            "status": payment["status"],
        },
        submission_evidence=submission,
    )
    journal_present = isinstance(journal_batch, sika_journal_store.sika_double_entry.JournalBatch)
    settlement_proven = bool(
        gate.get("settlement_proven")
        and journal_present
        and getattr(journal_batch, "balanced", False)
    )
    return {
        "valid": True,
        "payment_id": payment["payment_id"],
        "provider_submission_proven": bool(gate.get("proven")),
        "journal_present": journal_present,
        "journal_balanced": bool(getattr(journal_batch, "balanced", False)),
        "settlement_proven": settlement_proven,
        "external_money_movement_proven": False,
        "execution_granted": False,
        "money_movement": False,
    }



def fraud_intelligence(signals: object) -> dict[str, Any]:
    if not isinstance(signals, Mapping):
        return {
            "valid": False,
            "reason": "fraud_signals_required",
            "recommended_action": "REVIEW",
            "guilt_determined": False,
            "execution_granted": False,
        }
    duplicate = signals.get("duplicate_submission") is True
    account_mismatch = signals.get("account_mismatch") is True
    payment_mismatch = signals.get("payment_mismatch") is True
    authority_missing = signals.get("customer_authority_missing") is True
    rights_not_allow = signals.get("rights_not_allow") is True
    suspicious = any(
        (duplicate, account_mismatch, payment_mismatch, authority_missing, rights_not_allow)
    )
    return {
        "valid": True,
        "recommended_action": "REVIEW" if suspicious else "ALLOW_TO_CONTINUE_REVIEW",
        "risk_flags": tuple(
            name
            for name, flagged in (
                ("duplicate_submission", duplicate),
                ("account_mismatch", account_mismatch),
                ("payment_mismatch", payment_mismatch),
                ("customer_authority_missing", authority_missing),
                ("rights_not_allow", rights_not_allow),
            )
            if flagged
        ),
        "guilt_determined": False,
        "automatic_confiscation": False,
        "automatic_permanent_blacklist": False,
        "execution_granted": False,
        "money_movement": False,
    }


def rights_remedy_intelligence(record: object) -> dict[str, Any]:
    check = sika_rights_decision_record.verify_decision_record(record)
    if not check.get("verified") or not isinstance(record, Mapping):
        return {
            "valid": False,
            "reason": "rights_record_integrity_failed",
            "execution_ready": False,
            "remedy_available": False,
            "execution_granted": False,
        }
    gate = sika_rights_decision_record.execution_gate(record)
    return {
        "valid": True,
        "decision": record.get("decision"),
        "execution_ready": bool(gate.get("ready")),
        "remedy_reference": record.get("remedy_reference"),
        "explanation_reference": record.get("explanation_reference"),
        "remedy_available": bool(record.get("remedy_reference")),
        "human_authority_final": bool(record.get("human_authority_final")),
        "automatic_confiscation": bool(
            record.get("automatic_confiscation_enabled")
        ),
        "automatic_permanent_blacklist": bool(
            record.get("automatic_permanent_blacklist_enabled")
        ),
        "execution_granted": False,
        "money_movement": False,
    }


def currency_sika_intelligence() -> dict[str, Any]:
    bank = prince_sovereign_bank.status()
    currency = dict(bank.get("currency") or {})
    return {
        "valid": True,
        "name": currency.get("name"),
        "subunit": currency.get("subunit"),
        "subunits_per_unit": currency.get("subunits_per_unit"),
        "value_classes": tuple(currency.get("value_classes") or ()),
        "recognition_to_fiat_enabled": bool(
            currency.get("recognition_to_fiat_enabled")
        ),
        "recognition_to_currency_enabled": bool(
            currency.get("recognition_to_currency_enabled")
        ),
        "fiat_to_currency_enabled": bool(currency.get("fiat_to_currency_enabled")),
        "rewards_are_money": bool(currency.get("rewards_are_money")),
        "legal_tender": bool(currency.get("proposed_currency_is_legal_tender")),
        "balance_known": False,
        "conversion_rate_claimed": False,
        "issuance_enabled": False,
        "execution_granted": False,
        "money_movement": False,
    }


def status() -> dict[str, Any]:
    return {
        "system": "OAP Pay Intelligence",
        "first_party": True,
        "transition_intelligence": True,
        "wallet_intelligence": True,
        "payment_intelligence": True,
        "request_intelligence": True,
        "merchant_intelligence": True,
        "settlement_intelligence": True,
        "fraud_intelligence": True,
        "rights_remedy_intelligence": True,
        "currency_sika_intelligence": True,
        "activity_intelligence": True,
        "liquidity_intelligence": False,
        "guardian_intelligence": False,
        "smi_pay_intelligence": False,
        "advisory_only": True,
        "provider_calling": False,
        "journal_posting": False,
        "settlement_execution": False,
        "money_movement": False,
        "human_authority_final": True,
    }
