"""Durable first-party OAP Pay payment requests and share links.

Creates payment requests that are safe to share before any payment execution.
Public links use high-entropy bearer tokens stored only as SHA-256 hashes. This
module does not create debt, collect card data, authorize a payment, call a
provider, settle funds, or move money.
"""
from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime

from . import postgres_db

MIGRATION_VERSION = "oap_pay_requests_v1"
SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_pay_requests (
        request_id TEXT PRIMARY KEY,
        token_hash TEXT NOT NULL UNIQUE,
        payee_reference TEXT NOT NULL,
        amount NUMERIC(24,2) NOT NULL CHECK (amount > 0),
        currency TEXT NOT NULL,
        jurisdiction TEXT NOT NULL,
        surface TEXT NOT NULL,
        note TEXT,
        status TEXT NOT NULL CHECK (status IN ('OPEN','CANCELLED')),
        expires_at TIMESTAMPTZ,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE INDEX IF NOT EXISTS ix_oap_pay_requests_payee
       ON oap_pay_requests(payee_reference,created_at DESC)""",
    """CREATE INDEX IF NOT EXISTS ix_oap_pay_requests_status
       ON oap_pay_requests(status,created_at DESC)""",
)
MIGRATION_CHECKSUM = hashlib.sha256("\n".join(SCHEMA_STATEMENTS).encode()).hexdigest()


class PaymentRequestError(ValueError):
    """Raised when a payment request is malformed."""


class PaymentRequestUnavailable(RuntimeError):
    """Raised when durable request state cannot be accessed."""


@dataclass(frozen=True)
class PaymentRequest:
    request_id: str
    payee_reference: str
    amount: str
    currency: str
    jurisdiction: str
    surface: str
    note: str | None
    status: str
    expires_at: str | None

    @property
    def recipient_approval_required(self) -> bool:
        return True

    @property
    def creates_debt(self) -> bool:
        return False


def _required(value: object, error: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise PaymentRequestError(error)
    return text


def _amount(value: object) -> str:
    from decimal import Decimal, InvalidOperation
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise PaymentRequestError("amount_invalid") from exc
    if not parsed.is_finite() or parsed <= 0:
        raise PaymentRequestError("amount_invalid")
    return f"{parsed.quantize(Decimal('0.01')):.2f}"


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def init_schema(*, assume_yes: bool = False, dry_run: bool = False) -> dict[str, object]:
    if not assume_yes:
        raise RuntimeError("Explicit human approval required: pass --yes")
    if dry_run:
        return {
            "migration": MIGRATION_VERSION,
            "checksum": MIGRATION_CHECKSUM,
            "dry_run": True,
            "schema_ready": False,
            "human_authority_final": True,
        }
    try:
        with postgres_db.connect() as connection:
            for statement in SCHEMA_STATEMENTS:
                connection.execute(statement)
            connection.commit()
    except Exception as exc:
        raise PaymentRequestUnavailable("oap_pay_request_schema_init_failed") from exc
    return {
        "migration": MIGRATION_VERSION,
        "checksum": MIGRATION_CHECKSUM,
        "dry_run": False,
        "schema_ready": True,
        "human_authority_final": True,
    }


def create_request(
    *,
    request_id: object,
    payee_reference: object,
    amount: object,
    currency: object,
    jurisdiction: object,
    surface: object,
    note: object | None = None,
    expires_at: object | None = None,
) -> dict[str, object]:
    token = secrets.token_urlsafe(24)
    expires_value = None
    if expires_at is not None:
        raw = _required(expires_at, "expires_at_invalid")
        parsed = datetime.fromisoformat(raw)
        if parsed.tzinfo is None:
            raise PaymentRequestError("expires_at_invalid")
        if parsed <= datetime.now(UTC):
            raise PaymentRequestError("expires_at_must_be_future")
        expires_value = parsed.isoformat()
    note_value = None if note is None else str(note).strip() or None
    request = PaymentRequest(
        request_id=_required(request_id, "request_id_required"),
        payee_reference=_required(payee_reference, "payee_reference_required"),
        amount=_amount(amount),
        currency=_required(currency, "currency_required").upper(),
        jurisdiction=_required(jurisdiction, "jurisdiction_required"),
        surface=_required(surface, "surface_required"),
        note=note_value,
        status="OPEN",
        expires_at=expires_value,
    )
    try:
        with postgres_db.connect() as connection:
            connection.execute(
                """INSERT INTO oap_pay_requests(
                       request_id,token_hash,payee_reference,amount,currency,
                       jurisdiction,surface,note,status,expires_at
                   ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'OPEN',%s)""",
                (
                    request.request_id,
                    _token_hash(token),
                    request.payee_reference,
                    request.amount,
                    request.currency,
                    request.jurisdiction,
                    request.surface,
                    request.note,
                    request.expires_at,
                ),
            )
            connection.commit()
    except Exception as exc:
        raise PaymentRequestUnavailable("oap_pay_request_create_failed") from exc
    return {
        "request": request,
        "share_token": token,
        "share_path": f"/pay/r/{token}",
        "qr_ready": True,
        "recipient_approval_required": True,
        "creates_debt": False,
        "payment_authorised": False,
        "money_movement": False,
    }


def read_public_request(token: object) -> dict[str, object] | None:
    token_value = _required(token, "share_token_required")
    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT request_id,payee_reference,amount,currency,jurisdiction,
                          surface,note,status,expires_at
                   FROM oap_pay_requests
                   WHERE token_hash=%s""",
                (_token_hash(token_value),),
            ).fetchone()
    except Exception as exc:
        raise PaymentRequestUnavailable("oap_pay_request_read_failed") from exc
    if row is None:
        return None
    expired = row[8] is not None and row[8] <= datetime.now(UTC)
    return {
        "request_id": str(row[0]),
        "payee_reference": str(row[1]),
        "amount": f"{row[2]:.2f}",
        "currency": str(row[3]),
        "jurisdiction": str(row[4]),
        "surface": str(row[5]),
        "note": None if row[6] is None else str(row[6]),
        "status": str(row[7]),
        "expired": expired,
        "payable": str(row[7]) == "OPEN" and not expired,
        "recipient_approval_required": True,
        "creates_debt": False,
        "payment_authorised": False,
        "money_movement": False,
    }


def cancel_request(*, request_id: object) -> bool:
    request_id_value = _required(request_id, "request_id_required")
    try:
        with postgres_db.connect() as connection:
            row = connection.execute(
                """UPDATE oap_pay_requests
                   SET status='CANCELLED',updated_at=CURRENT_TIMESTAMP
                   WHERE request_id=%s AND status='OPEN'
                   RETURNING request_id""",
                (request_id_value,),
            ).fetchone()
            connection.commit()
    except Exception as exc:
        raise PaymentRequestUnavailable("oap_pay_request_cancel_failed") from exc
    return row is not None


def status() -> dict[str, object]:
    return {
        "system": "OAP Pay Requests",
        "first_party": True,
        "persistent_requests": True,
        "opaque_share_tokens": True,
        "share_tokens_stored_plaintext": False,
        "qr_ready_share_path": True,
        "recipient_approval_required": True,
        "creates_debt": False,
        "card_data_collection": False,
        "provider_calling": False,
        "payment_authorisation": False,
        "settlement_execution": False,
        "money_movement": False,
        "human_authority_final": True,
    }
