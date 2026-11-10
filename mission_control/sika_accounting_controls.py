"""Persistent accounting control plane for SIKA.

Provides chart-of-accounts persistence and accounting-period locks.
It does not generate statutory accounts, post settlement instructions, or move money.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date

from . import postgres_db, sika_double_entry

MIGRATION_VERSION = "sika_accounting_controls_v1"
SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_sika_chart_accounts (
        account_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        account_class TEXT NOT NULL CHECK (
            account_class IN ('asset','liability','equity','income','expense')
        ),
        currency TEXT NOT NULL,
        jurisdiction TEXT NOT NULL,
        active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS oap_sika_accounting_periods (
        period_id TEXT PRIMARY KEY,
        jurisdiction TEXT NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        status TEXT NOT NULL CHECK (status IN ('OPEN','CLOSED')),
        closed_by TEXT NOT NULL DEFAULT '',
        closed_at TIMESTAMPTZ,
        CHECK (end_date >= start_date),
        CHECK (
            (status='OPEN' AND closed_by='' AND closed_at IS NULL)
            OR
            (status='CLOSED' AND closed_by<>'' AND closed_at IS NOT NULL)
        )
    )""",
    """CREATE INDEX IF NOT EXISTS ix_sika_periods_jurisdiction_dates
       ON oap_sika_accounting_periods(jurisdiction,start_date,end_date)""",
)
MIGRATION_CHECKSUM = hashlib.sha256(
    "\n".join(SCHEMA_STATEMENTS).encode()
).hexdigest()


class AccountingControlsUnavailable(RuntimeError):
    """Raised when durable accounting controls are unavailable."""


@dataclass(frozen=True)
class PeriodState:
    period_id: str
    jurisdiction: str
    start_date: date
    end_date: date
    status: str

    @property
    def posting_allowed(self) -> bool:
        return self.status == "OPEN"


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
        raise AccountingControlsUnavailable("accounting_controls_schema_init_failed") from exc
    return {
        "migration": MIGRATION_VERSION,
        "checksum": MIGRATION_CHECKSUM,
        "dry_run": False,
        "schema_ready": True,
        "human_authority_final": True,
    }


def record_account(account: sika_double_entry.Account) -> dict[str, object]:
    try:
        with postgres_db.connect() as connection:
            connection.execute(
                """INSERT INTO oap_sika_chart_accounts(
                       account_id,name,account_class,currency,jurisdiction
                   ) VALUES (%s,%s,%s,%s,%s)
                   ON CONFLICT (account_id) DO NOTHING""",
                (
                    account.account_id,
                    account.name,
                    account.account_class.value,
                    account.currency,
                    account.jurisdiction,
                ),
            )
            connection.commit()
    except Exception as exc:
        raise AccountingControlsUnavailable("chart_account_write_failed") from exc
    return {
        "account_id": account.account_id,
        "recorded": True,
        "money_moved": False,
    }


def create_period(
    *,
    period_id: str,
    jurisdiction: str,
    start_date: date,
    end_date: date,
) -> PeriodState:
    if not period_id.strip():
        raise ValueError("period_id_required")
    if not jurisdiction.strip():
        raise ValueError("period_jurisdiction_required")
    if end_date < start_date:
        raise ValueError("period_date_range_invalid")
    try:
        with postgres_db.connect() as connection:
            connection.execute(
                """INSERT INTO oap_sika_accounting_periods(
                       period_id,jurisdiction,start_date,end_date,status
                   ) VALUES (%s,%s,%s,%s,'OPEN')""",
                (period_id, jurisdiction, start_date, end_date),
            )
            connection.commit()
    except Exception as exc:
        raise AccountingControlsUnavailable("accounting_period_create_failed") from exc
    return PeriodState(period_id, jurisdiction, start_date, end_date, "OPEN")


def close_period(*, period_id: str, closed_by: str) -> PeriodState:
    if not closed_by.strip():
        raise ValueError("closed_by_required")
    try:
        with postgres_db.connect() as connection:
            row = connection.execute(
                """UPDATE oap_sika_accounting_periods
                   SET status='CLOSED',closed_by=%s,closed_at=CURRENT_TIMESTAMP
                   WHERE period_id=%s AND status='OPEN'
                   RETURNING period_id,jurisdiction,start_date,end_date,status""",
                (closed_by, period_id),
            ).fetchone()
            if row is None:
                raise ValueError("accounting_period_not_open")
            connection.commit()
    except ValueError:
        raise
    except Exception as exc:
        raise AccountingControlsUnavailable("accounting_period_close_failed") from exc
    return PeriodState(
        period_id=str(row[0]),
        jurisdiction=str(row[1]),
        start_date=row[2],
        end_date=row[3],
        status=str(row[4]),
    )


def posting_allowed(*, jurisdiction: str, posting_date: date) -> bool:
    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT status
                   FROM oap_sika_accounting_periods
                   WHERE jurisdiction=%s
                     AND %s BETWEEN start_date AND end_date
                   ORDER BY start_date DESC
                   LIMIT 1""",
                (jurisdiction, posting_date),
            ).fetchone()
    except Exception as exc:
        raise AccountingControlsUnavailable("accounting_period_read_failed") from exc
    return bool(row is not None and str(row[0]) == "OPEN")


def status() -> dict[str, object]:
    return {
        "system": "SIKA Accounting Controls",
        "chart_of_accounts_persistent": True,
        "accounting_periods_persistent": True,
        "closed_period_posting_block": True,
        "statutory_accounts_generated": False,
        "settlement_execution": False,
        "money_movement": False,
        "human_authority_final": True,
    }
