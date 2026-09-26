"""SIKA intelligence bridge.

Reuses existing Alignment Intelligence and Bank Intelligence owners.
Read-only composition only; no regulated execution or customer-money action.
"""
from __future__ import annotations

from typing import Any

from . import alignment_check, bank_body_integration, prince_sovereign_bank


def alignment_intelligence() -> dict[str, Any]:
    status = alignment_check.status()
    signals = alignment_check.thinking_signals()
    return {
        "name": "Alignment Intelligence",
        "source": "existing_alignment_bridge",
        "status": status,
        "signals": signals,
        "sika_focus": {
            "one_sika": True,
            "one_ledger_direction": True,
            "first_party_core": True,
            "human_authority_final": True,
            "regulated_execution_separate": True,
        },
        "read_only": True,
        "executable": False,
    }


def bank_intelligence() -> dict[str, Any]:
    body = bank_body_integration.status()
    master = prince_sovereign_bank.status()
    return {
        "name": "Bank Intelligence",
        "source": "existing_oap_bank_contracts",
        "banking_family": body["banking_family"],
        "technical_rail_id": body["technical_rail_id"],
        "mind": master["mind"],
        "body": master["body"],
        "soul": master["soul"],
        "integrations": master["integrations"],
        "operational_bank": body["operational_bank"],
        "accounts_enabled": body["accounts_enabled"],
        "ledger_posting_enabled": body["ledger_posting_enabled"],
        "payment_execution_enabled": body["payment_execution_enabled"],
        "sika_money_issuance_enabled": body["sika_money_issuance_enabled"],
        "licence_verified": master["licence_verified"],
        "read_only": True,
        "executable": False,
    }
