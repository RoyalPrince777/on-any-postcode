"""Persistent first-party SIKA bank account engine.

Owns account identity and lifecycle state. Accounts are bound to a legal entity,
jurisdiction, currency, owner reference and ledger account. This module does
not create balances, post journals, execute payments or move money.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from . import postgres_db

MIGRATION_VERSION = "sika_account_engine_v1"
SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_sika_accounts (
        account_id TEXT PRIMARY KEY,
        owner_reference TEXT NOT NULL,
        legal_entity TEXT NOT NULL,
        jurisdiction TEXT NOT NULL,
        currency TEXT NOT NULL,
        ledger_account_id TEXT NOT NULL UNIQUE,
        status TEXT NOT NULL CHECK (status IN ('OPEN','FROZEN','CLOSED')),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE INDEX IF NOT EXISTS ix_sika_accounts_owner
       ON oap_sika_accounts(owner_reference)""",
    """CREATE INDEX IF NOT EXISTS ix_sika_accounts_entity_jurisdiction
       ON oap_sika_accounts(legal_entity,jurisdiction)""",
)
MIGRATION_CHECKSUM = hashlib.sha256(
    "\n".join(SCHEMA_STATEMENTS).encode()
).hexdigest()


class AccountEngineError(ValueError):
    """Raised when account identity or lifecycle rules are violated."""


class AccountEngineUnavailable(RuntimeError):
    """Raised when durable account state cannot be accessed safely."""


@dataclass(frozen=True)
class BankAccount:
    account_id: str
    owner_reference: str
    legal_entity: str
    jurisdiction: str
    currency: str
    ledger_account_id: str
    status: str

    @property
    def customer_activity_allowed(self) -> bool:
        return self.status == "OPEN"

    def as_dict(self) -> dict[str, object]:
        return {
            "account_id": self.account_id,
            "owner_reference": self.owner_reference,
            "legal_entity": self.legal_entity,
            "jurisdiction": self.jurisdiction,
            "currency": self.currency,
            "ledger_account_id": self.ledger_account_id,
            "status": self.status,
            "customer_activity_allowed": self.customer_activity_allowed,
        }


def _required(value: object, *, error: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise AccountEngineError(error)
    return text


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
        raise AccountEngineUnavailable("account_engine_schema_init_failed") from exc
    return {
        "migration": MIGRATION_VERSION,
        "checksum": MIGRATION_CHECKSUM,
        "dry_run": False,
        "schema_ready": True,
        "human_authority_final": True,
    }


def create_account(
    *,
    account_id: object,
    owner_reference: object,
    legal_entity: object,
    jurisdiction: object,
    currency: object,
    ledger_account_id: object,
) -> BankAccount:
    account = BankAccount(
        account_id=_required(account_id, error="account_id_required"),
        owner_reference=_required(
            owner_reference,
            error="owner_reference_required",
        ),
        legal_entity=_required(legal_entity, error="legal_entity_required"),
        jurisdiction=_required(jurisdiction, error="jurisdiction_required"),
        currency=_required(currency, error="currency_required").upper(),
        ledger_account_id=_required(
            ledger_account_id,
            error="ledger_account_id_required",
        ),
        status="OPEN",
    )
    try:
        with postgres_db.connect() as connection:
            connection.execute(
                """INSERT INTO oap_sika_accounts(
                       account_id,owner_reference,legal_entity,jurisdiction,
                       currency,ledger_account_id,status
                   ) VALUES (%s,%s,%s,%s,%s,%s,'OPEN')""",
                (
                    account.account_id,
                    account.owner_reference,
                    account.legal_entity,
                    account.jurisdiction,
                    account.currency,
                    account.ledger_account_id,
                ),
            )
            connection.commit()
    except Exception as exc:
        raise AccountEngineUnavailable("account_create_failed") from exc
    return account


def read_account(account_id: object) -> BankAccount | None:
    account_id_value = _required(account_id, error="account_id_required")
    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT account_id,owner_reference,legal_entity,jurisdiction,
                          currency,ledger_account_id,status
                   FROM oap_sika_accounts
                   WHERE account_id=%s""",
                (account_id_value,),
            ).fetchone()
    except Exception as exc:
        raise AccountEngineUnavailable("account_read_failed") from exc
    if row is None:
        return None
    return BankAccount(
        account_id=str(row[0]),
        owner_reference=str(row[1]),
        legal_entity=str(row[2]),
        jurisdiction=str(row[3]),
        currency=str(row[4]),
        ledger_account_id=str(row[5]),
        status=str(row[6]),
    )


def read_owner_accounts(owner_reference: object) -> list[BankAccount]:
    """Return durable accounts owned by one exact authenticated owner reference."""

    owner_value = _required(owner_reference, error="owner_reference_required")
    try:
        with postgres_db.connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT account_id,owner_reference,legal_entity,jurisdiction,
                          currency,ledger_account_id,status
                   FROM oap_sika_accounts
                   WHERE owner_reference=%s
                   ORDER BY created_at,account_id""",
                (owner_value,),
            ).fetchall()
    except Exception as exc:
        raise AccountEngineUnavailable("owner_accounts_read_failed") from exc
    return [
        BankAccount(
            account_id=str(row[0]),
            owner_reference=str(row[1]),
            legal_entity=str(row[2]),
            jurisdiction=str(row[3]),
            currency=str(row[4]),
            ledger_account_id=str(row[5]),
            status=str(row[6]),
        )
        for row in rows
    ]


def resolve_owned_account(
    *,
    account_id: object,
    owner_reference: object,
) -> BankAccount:
    """Resolve one exact account and prove it belongs to the supplied owner."""

    account = read_account(account_id)
    if account is None:
        raise AccountEngineError("account_not_found")
    owner_value = _required(owner_reference, error="owner_reference_required")
    if account.owner_reference != owner_value:
        raise AccountEngineError("account_owner_mismatch")
    if not account.customer_activity_allowed:
        raise AccountEngineError("account_not_open")
    return account


def transition(
    *,
    account_id: object,
    target_status: object,
) -> BankAccount:
    target = _required(target_status, error="target_status_required").upper()
    if target not in {"OPEN", "FROZEN", "CLOSED"}:
        raise AccountEngineError("target_status_invalid")

    current = read_account(account_id)
    if current is None:
        raise AccountEngineError("account_not_found")

    allowed = {
        "OPEN": {"FROZEN", "CLOSED"},
        "FROZEN": {"OPEN", "CLOSED"},
        "CLOSED": set(),
    }
    if target == current.status:
        return current
    if target not in allowed[current.status]:
        raise AccountEngineError("account_transition_not_allowed")

    try:
        with postgres_db.connect() as connection:
            row = connection.execute(
                """UPDATE oap_sika_accounts
                   SET status=%s,updated_at=CURRENT_TIMESTAMP
                   WHERE account_id=%s AND status=%s
                   RETURNING account_id,owner_reference,legal_entity,
                             jurisdiction,currency,ledger_account_id,status""",
                (target, current.account_id, current.status),
            ).fetchone()
            if row is None:
                raise AccountEngineError("account_state_changed")
            connection.commit()
    except AccountEngineError:
        raise
    except Exception as exc:
        raise AccountEngineUnavailable("account_transition_failed") from exc

    return BankAccount(
        account_id=str(row[0]),
        owner_reference=str(row[1]),
        legal_entity=str(row[2]),
        jurisdiction=str(row[3]),
        currency=str(row[4]),
        ledger_account_id=str(row[5]),
        status=str(row[6]),
    )


def status() -> dict[str, object]:
    return {
        "system": "SIKA Account Engine",
        "first_party": True,
        "backend": "postgresql",
        "persistent_account_identity": True,
        "owner_binding": True,
        "owner_resolution": True,
        "owner_scoped_account_listing": True,
        "legal_entity_binding": True,
        "jurisdiction_binding": True,
        "currency_binding": True,
        "ledger_account_binding": True,
        "lifecycle_states": ["OPEN", "FROZEN", "CLOSED"],
        "closed_account_reopen_allowed": False,
        "balance_fabrication": False,
        "journal_posting": False,
        "payment_execution": False,
        "money_movement": False,
        "human_authority_final": True,
    }
