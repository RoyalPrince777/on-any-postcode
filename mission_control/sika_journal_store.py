"""Durable append-only PostgreSQL store for SIKA journals.

Posting inserts an already-balanced journal and its lines atomically. Posted
rows are immutable at the database layer: UPDATE and DELETE are rejected.
Reversal creates a new compensating journal linked to the original.
"""
from __future__ import annotations

import hashlib

from . import postgres_db, sika_double_entry

MIGRATION_VERSION = "sika_journal_store_v1"
SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_sika_journals (
        journal_id TEXT PRIMARY KEY,
        reference TEXT NOT NULL,
        reversal_of TEXT REFERENCES oap_sika_journals(journal_id),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS oap_sika_journal_lines (
        journal_id TEXT NOT NULL REFERENCES oap_sika_journals(journal_id),
        line_no INTEGER NOT NULL CHECK (line_no > 0),
        account_id TEXT NOT NULL,
        side TEXT NOT NULL CHECK (side IN ('debit','credit')),
        amount NUMERIC(30,2) NOT NULL CHECK (amount > 0),
        currency TEXT NOT NULL,
        PRIMARY KEY (journal_id, line_no)
    )""",
    """CREATE OR REPLACE FUNCTION oap_reject_sika_journal_mutation()
       RETURNS trigger AS $$
       BEGIN
           RAISE EXCEPTION 'sika_journal_is_immutable';
       END;
       $$ LANGUAGE plpgsql""",
    """DROP TRIGGER IF EXISTS trg_oap_sika_journals_immutable
       ON oap_sika_journals""",
    """CREATE TRIGGER trg_oap_sika_journals_immutable
       BEFORE UPDATE OR DELETE ON oap_sika_journals
       FOR EACH ROW EXECUTE FUNCTION oap_reject_sika_journal_mutation()""",
    """DROP TRIGGER IF EXISTS trg_oap_sika_journal_lines_immutable
       ON oap_sika_journal_lines""",
    """CREATE TRIGGER trg_oap_sika_journal_lines_immutable
       BEFORE UPDATE OR DELETE ON oap_sika_journal_lines
       FOR EACH ROW EXECUTE FUNCTION oap_reject_sika_journal_mutation()""",
    """CREATE INDEX IF NOT EXISTS ix_oap_sika_journals_created
       ON oap_sika_journals(created_at DESC)""",
)
MIGRATION_CHECKSUM = hashlib.sha256(
    "\n".join(SCHEMA_STATEMENTS).encode()
).hexdigest()


class JournalStoreUnavailable(RuntimeError):
    """Raised when the durable journal store cannot be safely used."""


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
        raise JournalStoreUnavailable("sika_journal_schema_init_failed") from exc
    state = schema_status()
    if not state["schema_ready"]:
        raise JournalStoreUnavailable("sika_journal_schema_verification_failed")
    return {
        **state,
        "migration": MIGRATION_VERSION,
        "checksum": MIGRATION_CHECKSUM,
        "dry_run": False,
        "human_authority_final": True,
    }


def schema_status() -> dict[str, object]:
    result: dict[str, object] = {
        "database_reachable": False,
        "journal_table_ready": False,
        "line_table_ready": False,
        "schema_ready": False,
        "error": None,
    }
    try:
        with postgres_db.connect(readonly=True) as connection:
            result["database_reachable"] = True
            rows = connection.execute(
                """SELECT table_name
                   FROM information_schema.tables
                   WHERE table_schema='public'
                     AND table_name IN (
                        'oap_sika_journals',
                        'oap_sika_journal_lines'
                     )"""
            ).fetchall()
            tables = {str(row[0]) for row in rows}
            result["journal_table_ready"] = "oap_sika_journals" in tables
            result["line_table_ready"] = "oap_sika_journal_lines" in tables
            result["schema_ready"] = all(
                (
                    result["journal_table_ready"],
                    result["line_table_ready"],
                )
            )
    except Exception:  # noqa: BLE001
        result["error"] = "sika_journal_store_unavailable"
    return result


def post_batch(
    batch: sika_double_entry.JournalBatch,
    *,
    reversal_of: str | None = None,
) -> dict[str, object]:
    """Persist one validated balanced journal atomically."""

    if not batch.balanced:
        raise sika_double_entry.LedgerError("journal_not_balanced")
    try:
        with postgres_db.connect() as connection:
            connection.execute(
                """INSERT INTO oap_sika_journals(
                       journal_id,reference,reversal_of
                   ) VALUES (%s,%s,%s)""",
                (batch.journal_id, batch.reference, reversal_of),
            )
            for index, item in enumerate(batch.lines, start=1):
                connection.execute(
                    """INSERT INTO oap_sika_journal_lines(
                           journal_id,line_no,account_id,side,amount,currency
                       ) VALUES (%s,%s,%s,%s,%s,%s)""",
                    (
                        batch.journal_id,
                        index,
                        item.account_id,
                        item.side.value,
                        item.amount,
                        item.currency,
                    ),
                )
            row = connection.execute(
                """SELECT created_at
                   FROM oap_sika_journals
                   WHERE journal_id=%s""",
                (batch.journal_id,),
            ).fetchone()
            connection.commit()
    except Exception as exc:
        raise JournalStoreUnavailable("sika_journal_post_failed") from exc
    return {
        "journal_id": batch.journal_id,
        "reference": batch.reference,
        "reversal_of": reversal_of,
        "balanced": True,
        "posted": True,
        "created_at": row[0].isoformat(),
        "money_moved": False,
    }


def read_batch(journal_id: object) -> sika_double_entry.JournalBatch | None:
    journal_id_value = str(journal_id or "").strip()
    if not journal_id_value:
        raise sika_double_entry.LedgerError("journal_id_required")
    try:
        with postgres_db.connect(readonly=True) as connection:
            header = connection.execute(
                """SELECT journal_id,reference
                   FROM oap_sika_journals
                   WHERE journal_id=%s""",
                (journal_id_value,),
            ).fetchone()
            if header is None:
                return None
            rows = connection.execute(
                """SELECT account_id,side,amount,currency
                   FROM oap_sika_journal_lines
                   WHERE journal_id=%s
                   ORDER BY line_no""",
                (journal_id_value,),
            ).fetchall()
    except Exception as exc:
        raise JournalStoreUnavailable("sika_journal_read_failed") from exc
    return sika_double_entry.validate_batch(
        journal_id=str(header[0]),
        reference=str(header[1]),
        lines=[
            sika_double_entry.line(
                account_id=row[0],
                side=str(row[1]),
                amount=row[2],
                currency=row[3],
            )
            for row in rows
        ],
    )


def reverse_posted_batch(
    *,
    original_journal_id: object,
    reversal_journal_id: object,
    reference: object,
) -> dict[str, object]:
    original = read_batch(original_journal_id)
    if original is None:
        raise sika_double_entry.LedgerError("original_journal_not_found")
    reversal = sika_double_entry.reversal_batch(
        original=original,
        journal_id=reversal_journal_id,
        reference=reference,
    )
    return post_batch(reversal, reversal_of=original.journal_id)


def status() -> dict[str, object]:
    return {
        "system": "SIKA Journal Store",
        "backend": "postgresql",
        "append_only": True,
        "database_mutation_protection": True,
        "supports_compensating_reversals": True,
        "in_place_update_allowed": False,
        "in_place_delete_allowed": False,
        "settlement_execution": False,
        "external_money_movement": False,
        "human_authority_final": True,
    }
