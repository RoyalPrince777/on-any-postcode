"""Payment-specific customer authority receipts for SIKA Pay.

Receipts are explicit, hash-bound and append-only when persisted. This module
does not authenticate a customer by itself, execute payments, or move money.
"""
from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

MIGRATION_VERSION = "sika_customer_payment_authority_v1"
SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_sika_customer_payment_authority (
        receipt_hash TEXT PRIMARY KEY,
        payment_id TEXT NOT NULL,
        payer_account_id TEXT NOT NULL,
        payee_reference TEXT NOT NULL,
        amount TEXT NOT NULL,
        currency TEXT NOT NULL,
        jurisdiction TEXT NOT NULL,
        authority_reference TEXT NOT NULL,
        authorised_at TIMESTAMPTZ NOT NULL,
        expires_at TIMESTAMPTZ NOT NULL,
        revoked BOOLEAN NOT NULL DEFAULT FALSE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE INDEX IF NOT EXISTS ix_sika_customer_authority_payment
       ON oap_sika_customer_payment_authority(payment_id, created_at DESC)""",
)


class CustomerAuthorityError(ValueError):
    pass


def _required(value: object, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise CustomerAuthorityError(f"{field}_required")
    return text


def _iso(value: object, field: str) -> str:
    text = _required(value, field)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise CustomerAuthorityError(f"{field}_invalid") from exc
    if parsed.tzinfo is None:
        raise CustomerAuthorityError(f"{field}_timezone_required")
    return parsed.astimezone(UTC).isoformat().replace("+00:00", "Z")


def build_receipt(
    *,
    payment_id: object,
    payer_account_id: object,
    payee_reference: object,
    amount: object,
    currency: object,
    jurisdiction: object,
    authority_reference: object,
    authorised_at: object,
    expires_at: object,
) -> dict[str, object]:
    payload = {
        "payment_id": _required(payment_id, "payment_id"),
        "payer_account_id": _required(payer_account_id, "payer_account_id"),
        "payee_reference": _required(payee_reference, "payee_reference"),
        "amount": _required(amount, "amount"),
        "currency": _required(currency, "currency").upper(),
        "jurisdiction": _required(jurisdiction, "jurisdiction"),
        "authority_reference": _required(authority_reference, "authority_reference"),
        "authorised_at": _iso(authorised_at, "authorised_at"),
        "expires_at": _iso(expires_at, "expires_at"),
        "revoked": False,
    }
    authorised = datetime.fromisoformat(payload["authorised_at"].replace("Z", "+00:00"))
    expires = datetime.fromisoformat(payload["expires_at"].replace("Z", "+00:00"))
    if expires <= authorised:
        raise CustomerAuthorityError("expires_at_must_follow_authorised_at")
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return {
        **payload,
        "receipt_hash": hashlib.sha256(canonical.encode()).hexdigest(),
        "customer_authority_final": True,
        "money_movement": False,
    }


def verify_receipt(
    receipt: object,
    *,
    now: datetime | None = None,
) -> dict[str, object]:
    if not isinstance(receipt, dict):
        return {"verified": False, "reason": "receipt_invalid"}
    expected = build_receipt(
        payment_id=receipt.get("payment_id"),
        payer_account_id=receipt.get("payer_account_id"),
        payee_reference=receipt.get("payee_reference"),
        amount=receipt.get("amount"),
        currency=receipt.get("currency"),
        jurisdiction=receipt.get("jurisdiction"),
        authority_reference=receipt.get("authority_reference"),
        authorised_at=receipt.get("authorised_at"),
        expires_at=receipt.get("expires_at"),
    )
    if receipt.get("receipt_hash") != expected["receipt_hash"]:
        return {"verified": False, "reason": "receipt_hash_mismatch"}
    if receipt.get("revoked") is True:
        return {"verified": False, "reason": "receipt_revoked"}
    current = now or datetime.now(UTC)
    expires = datetime.fromisoformat(str(receipt["expires_at"]).replace("Z", "+00:00"))
    if current >= expires:
        return {"verified": False, "reason": "receipt_expired"}
    return {
        "verified": True,
        "reason": None,
        "receipt_hash": receipt["receipt_hash"],
        "customer_authority_final": True,
        "money_movement": False,
    }


def matches_payment(receipt: object, payment: object) -> bool:
    if not isinstance(receipt, dict) or not isinstance(payment, dict):
        return False
    fields = (
        "payment_id",
        "payer_account_id",
        "payee_reference",
        "amount",
        "currency",
        "jurisdiction",
    )
    return all(str(receipt.get(field) or "") == str(payment.get(field) or "") for field in fields)


def status() -> dict[str, Any]:
    return {
        "system": "SIKA Customer Payment Authority",
        "payment_specific": True,
        "hash_bound": True,
        "expiry_required": True,
        "revocation_supported": True,
        "append_only_schema": True,
        "customer_authority_required": True,
        "provider_calling": False,
        "money_movement": False,
    }
