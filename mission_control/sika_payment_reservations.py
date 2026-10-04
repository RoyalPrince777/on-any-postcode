"""Durable SIKA payment holds/reservations.

A hold reserves ledger-derived customer value for one payment before provider
submission. Holds do not move money, post journals, or imply settlement.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from . import postgres_db

MIGRATION_VERSION = "sika_payment_reservations_v1"
SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_sika_payment_holds (
        hold_id TEXT PRIMARY KEY,
        payment_id TEXT NOT NULL UNIQUE,
        payer_account_id TEXT NOT NULL,
        amount NUMERIC(24,2) NOT NULL CHECK (amount > 0),
        currency TEXT NOT NULL,
        status TEXT NOT NULL CHECK (status IN ('ACTIVE','RELEASED','CONSUMED')),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE INDEX IF NOT EXISTS ix_sika_payment_holds_account_status
       ON oap_sika_payment_holds(payer_account_id,status)""",
)
MIGRATION_CHECKSUM = hashlib.sha256(
    "\n".join(SCHEMA_STATEMENTS).encode()
).hexdigest()


class ReservationError(ValueError):
    """Raised when a payment hold violates reservation rules."""


class ReservationUnavailable(RuntimeError):
    """Raised when durable hold state cannot be accessed safely."""


@dataclass(frozen=True)
class PaymentHold:
    hold_id: str
    payment_id: str
    payer_account_id: str
    amount: Decimal
    currency: str
    status: str

    @property
    def active(self) -> bool:
        return self.status == "ACTIVE"

    def as_dict(self) -> dict[str, object]:
        return {
            "hold_id": self.hold_id,
            "payment_id": self.payment_id,
            "payer_account_id": self.payer_account_id,
            "amount": f"{self.amount:.2f}",
            "currency": self.currency,
            "status": self.status,
            "active": self.active,
        }


def _required(value: object, error: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ReservationError(error)
    return text


def _amount(value: object) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ReservationError("hold_amount_invalid") from exc
    if not parsed.is_finite() or parsed <= 0:
        raise ReservationError("hold_amount_invalid")
    return parsed.quantize(Decimal("0.01"))


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
        raise ReservationUnavailable("reservation_schema_init_failed") from exc
    return {
        "migration": MIGRATION_VERSION,
        "checksum": MIGRATION_CHECKSUM,
        "dry_run": False,
        "schema_ready": True,
        "human_authority_final": True,
    }


def read_hold(payment_id: object) -> PaymentHold | None:
    payment_id_value = _required(payment_id, "payment_id_required")
    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT hold_id,payment_id,payer_account_id,amount,currency,status
                   FROM oap_sika_payment_holds
                   WHERE payment_id=%s""",
                (payment_id_value,),
            ).fetchone()
    except Exception as exc:
        raise ReservationUnavailable("reservation_read_failed") from exc
    if row is None:
        return None
    return PaymentHold(
        hold_id=str(row[0]),
        payment_id=str(row[1]),
        payer_account_id=str(row[2]),
        amount=Decimal(str(row[3])).quantize(Decimal("0.01")),
        currency=str(row[4]),
        status=str(row[5]),
    )


def transition(*, payment_id: object, target_status: object) -> PaymentHold:
    target = _required(target_status, "hold_target_status_required").upper()
    if target not in {"RELEASED", "CONSUMED"}:
        raise ReservationError("hold_target_status_invalid")
    current = read_hold(payment_id)
    if current is None:
        raise ReservationError("hold_not_found")
    if current.status == target:
        return current
    if current.status != "ACTIVE":
        raise ReservationError("hold_transition_not_allowed")
    try:
        with postgres_db.connect() as connection:
            row = connection.execute(
                """UPDATE oap_sika_payment_holds
                   SET status=%s,updated_at=CURRENT_TIMESTAMP
                   WHERE payment_id=%s AND status='ACTIVE'
                   RETURNING hold_id,payment_id,payer_account_id,amount,currency,status""",
                (target, current.payment_id),
            ).fetchone()
            if row is None:
                raise ReservationError("hold_state_changed")
            connection.commit()
    except ReservationError:
        raise
    except Exception as exc:
        raise ReservationUnavailable("reservation_transition_failed") from exc
    return PaymentHold(
        hold_id=str(row[0]),
        payment_id=str(row[1]),
        payer_account_id=str(row[2]),
        amount=Decimal(str(row[3])).quantize(Decimal("0.01")),
        currency=str(row[4]),
        status=str(row[5]),
    )


def status() -> dict[str, object]:
    return {
        "system": "SIKA Payment Reservations",
        "first_party": True,
        "backend": "postgresql",
        "persistent_holds": True,
        "payment_id_unique": True,
        "active_release_consume_lifecycle": True,
        "prevents_double_allocation_when_used_atomically": True,
        "journal_posting": False,
        "provider_calling": False,
        "settlement_execution": False,
        "money_movement": False,
        "human_authority_final": True,
    }
