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
    sika_account_engine,
    sika_journal_store,
    sika_payment_disputes,
    sika_payment_orchestrator,
    sika_payment_submission_evidence,
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
        "fraud_intelligence": False,
        "rights_remedy_intelligence": False,
        "currency_sika_intelligence": False,
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
