"""Persistent first-party SIKA card controls.

Owns card-to-account binding, lifecycle and spending-control policy. It records
settlement/dispute references but does not issue network cards, call schemes,
authorise live transactions, settle funds, or move money.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from . import postgres_db, sika_account_engine

MIGRATION_VERSION = "sika_card_controls_v1"
SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_sika_cards (
        card_id TEXT PRIMARY KEY,
        account_id TEXT NOT NULL,
        owner_reference TEXT NOT NULL,
        status TEXT NOT NULL CHECK (
            status IN ('ISSUED','ACTIVE','FROZEN','CLOSED')
        ),
        single_transaction_limit NUMERIC(24,2),
        daily_limit NUMERIC(24,2),
        settlement_reference TEXT,
        dispute_id TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE INDEX IF NOT EXISTS ix_sika_cards_account
       ON oap_sika_cards(account_id)""",
)
MIGRATION_CHECKSUM = hashlib.sha256(
    "\n".join(SCHEMA_STATEMENTS).encode()
).hexdigest()


class CardControlError(ValueError):
    """Raised when card lifecycle or spending rules are violated."""


class CardControlUnavailable(RuntimeError):
    """Raised when durable card state cannot be accessed safely."""


def _required(value: object, *, error: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise CardControlError(error)
    return text


def _limit(value: object | None, *, error: str) -> Decimal | None:
    if value is None:
        return None
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise CardControlError(error) from exc
    if not parsed.is_finite() or parsed <= 0:
        raise CardControlError(error)
    return parsed.quantize(Decimal("0.01"))


@dataclass(frozen=True)
class CardAccount:
    card_id: str
    account_id: str
    owner_reference: str
    status: str
    single_transaction_limit: Decimal | None
    daily_limit: Decimal | None
    settlement_reference: str | None = None
    dispute_id: str | None = None

    @property
    def may_enter_authorisation_review(self) -> bool:
        return self.status == "ACTIVE"


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
        raise CardControlUnavailable("card_controls_schema_init_failed") from exc
    return {
        "migration": MIGRATION_VERSION,
        "checksum": MIGRATION_CHECKSUM,
        "dry_run": False,
        "schema_ready": True,
        "human_authority_final": True,
    }


def create_card(
    *,
    card_id: object,
    account: sika_account_engine.BankAccount,
    single_transaction_limit: object | None = None,
    daily_limit: object | None = None,
) -> CardAccount:
    if not account.customer_activity_allowed:
        raise CardControlError("account_not_open")
    card = CardAccount(
        card_id=_required(card_id, error="card_id_required"),
        account_id=account.account_id,
        owner_reference=account.owner_reference,
        status="ISSUED",
        single_transaction_limit=_limit(
            single_transaction_limit,
            error="single_transaction_limit_invalid",
        ),
        daily_limit=_limit(daily_limit, error="daily_limit_invalid"),
    )
    try:
        with postgres_db.connect() as connection:
            connection.execute(
                """INSERT INTO oap_sika_cards(
                       card_id,account_id,owner_reference,status,
                       single_transaction_limit,daily_limit
                   ) VALUES (%s,%s,%s,'ISSUED',%s,%s)""",
                (
                    card.card_id,
                    card.account_id,
                    card.owner_reference,
                    card.single_transaction_limit,
                    card.daily_limit,
                ),
            )
            connection.commit()
    except Exception as exc:
        raise CardControlUnavailable("card_create_failed") from exc
    return card


def amount_within_controls(*, card: CardAccount, amount: object) -> bool:
    if not card.may_enter_authorisation_review:
        return False
    try:
        parsed = Decimal(str(amount)).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise CardControlError("card_amount_invalid") from exc
    if not parsed.is_finite() or parsed <= 0:
        raise CardControlError("card_amount_invalid")
    if card.single_transaction_limit is not None and parsed > card.single_transaction_limit:
        return False
    return True


def status() -> dict[str, object]:
    return {
        "system": "SIKA Card Controls",
        "first_party": True,
        "backend": "postgresql",
        "card_account_binding": True,
        "lifecycle_states": ["ISSUED", "ACTIVE", "FROZEN", "CLOSED"],
        "spending_controls": True,
        "settlement_reference_binding": True,
        "dispute_linkage": True,
        "live_network_issuing": False,
        "live_authorisation_processing": False,
        "scheme_connectivity": False,
        "settlement_execution": False,
        "money_movement": False,
        "human_authority_final": True,
    }
