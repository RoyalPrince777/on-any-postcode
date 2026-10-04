"""Canonical ledger-derived customer balance projection for SIKA.

Balances are calculated from immutable journal lines and durable payment holds.
No display balance is stored or fabricated.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from . import postgres_db, sika_account_engine


class BalanceEngineError(ValueError):
    """Raised when a customer balance cannot be projected safely."""


class BalanceEngineUnavailable(RuntimeError):
    """Raised when canonical ledger/hold state is unavailable."""


@dataclass(frozen=True)
class BalanceProjection:
    account_id: str
    ledger_account_id: str
    currency: str
    cleared: Decimal
    pending: Decimal
    reserved: Decimal
    available: Decimal

    def as_dict(self) -> dict[str, str]:
        return {
            "account_id": self.account_id,
            "ledger_account_id": self.ledger_account_id,
            "currency": self.currency,
            "cleared": f"{self.cleared:.2f}",
            "pending": f"{self.pending:.2f}",
            "reserved": f"{self.reserved:.2f}",
            "available": f"{self.available:.2f}",
        }


def _decimal(value: object) -> Decimal:
    return Decimal(str(value or "0")).quantize(Decimal("0.01"))


def project(account: sika_account_engine.BankAccount) -> BalanceProjection:
    if not isinstance(account, sika_account_engine.BankAccount):
        raise BalanceEngineError("account_required")
    if not account.customer_activity_allowed:
        raise BalanceEngineError("account_not_open")

    try:
        with postgres_db.connect(readonly=True) as connection:
            journal = connection.execute(
                """SELECT
                       COALESCE(SUM(CASE WHEN side='credit' THEN amount ELSE 0 END),0),
                       COALESCE(SUM(CASE WHEN side='debit' THEN amount ELSE 0 END),0)
                   FROM oap_sika_journal_lines
                   WHERE account_id=%s AND currency=%s""",
                (account.ledger_account_id, account.currency),
            ).fetchone()
            holds = connection.execute(
                """SELECT COALESCE(SUM(amount),0)
                   FROM oap_sika_payment_holds
                   WHERE payer_account_id=%s
                     AND currency=%s
                     AND status='ACTIVE'""",
                (account.account_id, account.currency),
            ).fetchone()
            pending = connection.execute(
                """SELECT COALESCE(SUM(amount),0)
                   FROM oap_sika_payment_intents
                   WHERE payer_account_id=%s
                     AND currency=%s
                     AND status IN ('REVIEW','AUTHORISED','SUBMITTED')""",
                (account.account_id, account.currency),
            ).fetchone()
    except Exception as exc:
        raise BalanceEngineUnavailable("canonical_balance_projection_failed") from exc

    credits = _decimal(journal[0])
    debits = _decimal(journal[1])
    cleared = credits - debits
    reserved = _decimal(holds[0])
    pending_value = _decimal(pending[0])
    available = max(cleared - reserved, Decimal("0.00")).quantize(Decimal("0.01"))

    return BalanceProjection(
        account_id=account.account_id,
        ledger_account_id=account.ledger_account_id,
        currency=account.currency,
        cleared=cleared,
        pending=pending_value,
        reserved=reserved,
        available=available,
    )


def status() -> dict[str, object]:
    return {
        "system": "SIKA Canonical Balance Engine",
        "first_party": True,
        "ledger_derived": True,
        "display_balance_stored": False,
        "cleared_balance": True,
        "pending_balance": True,
        "reserved_balance": True,
        "available_balance": True,
        "active_holds_reduce_available": True,
        "provider_calling": False,
        "money_movement": False,
        "human_authority_final": True,
    }
