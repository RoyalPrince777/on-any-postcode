"""Authenticated owner-scoped SIKA customer projections.

This module composes canonical account, balance and payment state for one
verified OAP identity reference. It is read-only and never authorizes or moves
money.
"""
from __future__ import annotations

from typing import Any

from . import postgres_db, sika_account_engine, sika_balance_engine


class CustomerViewUnavailable(RuntimeError):
    """Raised when canonical owner-scoped SIKA state cannot be read safely."""


def _founder_binding(owner: str) -> dict[str, object]:
    """Read the persisted Founder binding for exactly one authenticated owner."""
    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT account_id,sika_number
                   FROM oap_sika_founder_accounts
                   WHERE owner_reference=%s""",
                (owner,),
            ).fetchone()
    except Exception as exc:
        raise CustomerViewUnavailable("founder_binding_read_failed") from exc
    if row is None:
        return {"provisioned": False, "sika_number": None, "account_id": None}
    return {
        "provisioned": True,
        "sika_number": str(row[1]),
        "account_id": str(row[0]),
    }


def snapshot(owner_reference: object) -> dict[str, Any]:
    owner = str(owner_reference or "").strip()
    if not owner:
        raise ValueError("owner_reference_required")
    accounts = sika_account_engine.read_owner_accounts(owner)
    items = []
    for account in accounts:
        balance = None
        if account.customer_activity_allowed:
            balance = sika_balance_engine.project(account).as_dict()
        items.append(
            {
                "account_id": account.account_id,
                "legal_entity": account.legal_entity,
                "jurisdiction": account.jurisdiction,
                "currency": account.currency,
                "status": account.status,
                "customer_activity_allowed": account.customer_activity_allowed,
                "balance": balance,
            }
        )
    founder = _founder_binding(owner)
    return {
        "accounts": items,
        "account_count": len(items),
        "founder": founder,
        "owner_scoped": True,
        "balance_source": "canonical_ledger_and_holds",
        "provider_calling": False,
        "money_movement": False,
    }


def activity(owner_reference: object, *, limit: int = 50) -> dict[str, Any]:
    owner = str(owner_reference or "").strip()
    if not owner:
        raise ValueError("owner_reference_required")
    accounts = sika_account_engine.read_owner_accounts(owner)
    account_ids = [account.account_id for account in accounts]
    if not account_ids:
        return {
            "items": [],
            "owner_scoped": True,
            "source": "canonical_payment_intents",
            "money_movement": False,
        }

    bounded_limit = max(1, min(int(limit), 100))
    try:
        with postgres_db.connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT payment_id,payer_account_id,payee_reference,amount,
                          currency,jurisdiction,status,provider_reference,
                          created_at,updated_at
                   FROM oap_sika_payment_intents
                   WHERE payer_account_id = ANY(%s)
                   ORDER BY created_at DESC,payment_id DESC
                   LIMIT %s""",
                (account_ids, bounded_limit),
            ).fetchall()
    except Exception as exc:
        raise CustomerViewUnavailable("customer_activity_read_failed") from exc

    return {
        "items": [
            {
                "payment_id": str(row[0]),
                "payer_account_id": str(row[1]),
                "payee_reference": str(row[2]),
                "amount": f"{row[3]:.2f}",
                "currency": str(row[4]),
                "jurisdiction": str(row[5]),
                "status": str(row[6]),
                "provider_reference": None if row[7] is None else str(row[7]),
                "created_at": row[8].isoformat(),
                "updated_at": row[9].isoformat(),
            }
            for row in rows
        ],
        "owner_scoped": True,
        "source": "canonical_payment_intents",
        "money_movement": False,
    }


def status() -> dict[str, object]:
    return {
        "system": "SIKA Authenticated Customer View",
        "first_party": True,
        "owner_scoped": True,
        "verified_identity_reference_required": True,
        "canonical_account_source": True,
        "ledger_balance_source": True,
        "canonical_payment_activity": True,
        "read_only": True,
        "provider_calling": False,
        "money_movement": False,
        "human_authority_final": True,
    }
