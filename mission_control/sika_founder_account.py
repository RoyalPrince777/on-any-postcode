"""Founder SIKA account provisioning.

Adds a durable public SIKA Number to the existing canonical account engine without
granting payment, balance, journal or Treasury authority. Provisioning is atomic:
the account identity and Founder binding either both persist or neither does.
"""
from __future__ import annotations

import secrets
from dataclasses import dataclass

from . import authority, postgres_db, sika_account_engine

MIGRATION_VERSION = "sika_founder_account_v1"
SIKA_NUMBER_PREFIX = "SIKA-777-"
SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_sika_founder_accounts (
        owner_reference TEXT PRIMARY KEY,
        account_id TEXT NOT NULL UNIQUE REFERENCES oap_sika_accounts(account_id),
        sika_number TEXT NOT NULL UNIQUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE UNIQUE INDEX IF NOT EXISTS ux_sika_founder_number
       ON oap_sika_founder_accounts(sika_number)""",
)


class FounderProvisioningError(ValueError):
    """Raised when Founder provisioning rules are violated."""


class FounderProvisioningUnavailable(RuntimeError):
    """Raised when durable Founder provisioning cannot be completed safely."""


@dataclass(frozen=True)
class FounderAccount:
    account: sika_account_engine.BankAccount
    sika_number: str

    def as_dict(self) -> dict[str, object]:
        return {
            "account": self.account.as_dict(),
            "sika_number": self.sika_number,
            "founder": True,
            "treasury_authority": False,
        }


def _required(value: object, error: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise FounderProvisioningError(error)
    return text


def generate_sika_number() -> str:
    """Generate a public Founder namespace number without encoding personal data."""
    return f"{SIKA_NUMBER_PREFIX}{secrets.randbelow(10**12):012d}"


def init_schema(*, assume_yes: bool = False, dry_run: bool = False) -> dict[str, object]:
    if not assume_yes:
        raise RuntimeError("Explicit human approval required: pass --yes")
    if dry_run:
        return {
            "migration": MIGRATION_VERSION,
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
        raise FounderProvisioningUnavailable("founder_schema_init_failed") from exc
    return {
        "migration": MIGRATION_VERSION,
        "dry_run": False,
        "schema_ready": True,
        "human_authority_final": True,
    }


def provision(
    *,
    account_id: object,
    owner_reference: object,
    legal_entity: object,
    jurisdiction: object,
    currency: object,
    ledger_account_id: object,
    sika_number: object | None = None,
) -> FounderAccount:
    """Provision exactly one Founder financial identity for one owner."""
    owner = _required(owner_reference, "owner_reference_required")
    account = sika_account_engine.BankAccount(
        account_id=_required(account_id, "account_id_required"),
        owner_reference=owner,
        legal_entity=_required(legal_entity, "legal_entity_required"),
        jurisdiction=_required(jurisdiction, "jurisdiction_required"),
        currency=_required(currency, "currency_required").upper(),
        ledger_account_id=_required(ledger_account_id, "ledger_account_id_required"),
        status="OPEN",
    )
    number = str(sika_number or generate_sika_number()).strip().upper()
    if not number.startswith(SIKA_NUMBER_PREFIX):
        raise FounderProvisioningError("founder_sika_number_namespace_required")

    try:
        with postgres_db.connect() as connection:
            # The owner must be the canonical authenticated level-zero Human Authority.
            # This rejects recovery/non-authority identities before any SIKA row is created.
            try:
                authority.require_human_authority(connection, owner)
            except (ValueError, PermissionError) as exc:
                raise FounderProvisioningError("human_authority_owner_required") from exc

            existing = connection.execute(
                """SELECT f.sika_number,a.account_id,a.owner_reference,a.legal_entity,
                          a.jurisdiction,a.currency,a.ledger_account_id,a.status
                   FROM oap_sika_founder_accounts f
                   JOIN oap_sika_accounts a ON a.account_id=f.account_id
                   WHERE f.owner_reference=%s
                   FOR UPDATE""",
                (owner,),
            ).fetchone()
            if existing is not None:
                persisted = sika_account_engine.BankAccount(
                    account_id=str(existing[1]),
                    owner_reference=str(existing[2]),
                    legal_entity=str(existing[3]),
                    jurisdiction=str(existing[4]),
                    currency=str(existing[5]),
                    ledger_account_id=str(existing[6]),
                    status=str(existing[7]),
                )
                return FounderAccount(account=persisted, sika_number=str(existing[0]))

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
            connection.execute(
                """INSERT INTO oap_sika_founder_accounts(
                       owner_reference,account_id,sika_number
                   ) VALUES (%s,%s,%s)""",
                (owner, account.account_id, number),
            )
            connection.commit()
    except FounderProvisioningError:
        raise
    except Exception as exc:
        raise FounderProvisioningUnavailable("founder_account_provision_failed") from exc

    return FounderAccount(account=account, sika_number=number)


def status() -> dict[str, object]:
    return {
        "system": "SIKA Founder Account Provisioning",
        "first_party": True,
        "one_founder_account_per_owner": True,
        "public_sika_number": True,
        "sika_number_namespace": SIKA_NUMBER_PREFIX,
        "atomic_provisioning": True,
        "creates_balance": False,
        "journal_posting": False,
        "payment_execution": False,
        "treasury_authority": False,
        "human_authority_final": True,
    }
