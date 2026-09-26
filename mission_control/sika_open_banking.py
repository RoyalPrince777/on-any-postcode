"""SIKA Open Banking evidence adapter.

Read-only trial/sandbox integration boundary. This module never moves money,
creates deposits, issues e-money, or treats SIKA reference balances as bank funds.
"""
from __future__ import annotations

import os
from typing import Any


def status() -> dict[str, Any]:
    mode = os.environ.get("SIKA_BANK_MODE", "sandbox").strip().lower()
    client_id = bool(os.environ.get("SIKA_OB_CLIENT_ID"))
    certificate = bool(os.environ.get("SIKA_OB_CERTIFICATE"))
    endpoint = bool(os.environ.get("SIKA_OB_BASE_URL"))
    consent_ref = bool(os.environ.get("SIKA_OB_CONSENT_REF"))
    regulatory_ref = bool(os.environ.get("SIKA_OB_REGULATORY_REF"))

    sandbox = mode == "sandbox"
    production = mode == "production"
    connector_configured = client_id and certificate and endpoint
    production_ready = bool(
        production and connector_configured and consent_ref and regulatory_ref
    )
    return {
        "mode": mode,
        "sandbox_mode": sandbox,
        "production_mode": production,
        "connector_configured": connector_configured,
        "client_id_present": client_id,
        "certificate_present": certificate,
        "base_url_present": endpoint,
        "consent_reference_present": consent_ref,
        "regulatory_reference_present": regulatory_ref,
        "read_only_account_information": True,
        "payment_initiation_enabled": False,
        "customer_funds_held": False,
        "sika_reference_balance_is_bank_money": False,
        "sandbox_trial_ready": sandbox,
        "real_bank_read_ready": production_ready,
        "real_payment_ready": False,
        "execution_enabled": False,
        "reason": (
            "production_evidence_and_credentials_required"
            if production and not production_ready
            else "read_only_sandbox_evidence_mode"
            if sandbox
            else "read_only_connector_ready"
        ),
    }


def trial_snapshot() -> dict[str, Any]:
    state = status()
    if not state["sandbox_mode"]:
        return {
            "available": False,
            "reason": "sandbox_mode_required_for_dummy_trial",
            "money_moved": False,
            "execution_enabled": False,
        }
    return {
        "available": True,
        "source": "open_banking_sandbox_contract",
        "account": {
            "account_id": "sandbox-demo-account",
            "currency": "GBP",
            "balance": "100.00",
            "balance_type": "dummy_data",
        },
        "sika_view": {
            "reference_sika": "100.00",
            "anchor": "1 SIKA = 1 GBP target",
            "bank_money_claim": False,
        },
        "money_moved": False,
        "execution_enabled": False,
        "lawful_evidence_class": "sandbox_dummy_data_only",
    }
