"""Durable first-party SIKA reference journal on canonical OAP stores.

This is a non-monetary software journal. It reuses the existing owner-scoped
SIKA workspace and global audit_events chain. It never creates deposits,
customer funds, bank accounts, or executable payment instructions.
"""
from __future__ import annotations

import json
from decimal import Decimal
from hashlib import sha256
from uuid import UUID, uuid4

from . import postgres_db


class SikaJournalUnavailable(RuntimeError):
    pass


def _owner(value: object) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("canonical_owner_id_required") from exc


def _hash(payload: dict[str, object]) -> str:
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def _read_entries(connection, owner_id: str) -> list[dict[str, object]]:
    rows = connection.execute(
        """SELECT title,body,created_at
           FROM oap_workspace_records
           WHERE identity_id=%s AND workspace_id='sika'
             AND status='active' AND title LIKE 'SIKA-JOURNAL:%%'
           ORDER BY created_at ASC, record_id ASC""",
        (owner_id,),
    ).fetchall()
    entries: list[dict[str, object]] = []
    previous = "GENESIS"
    for row in rows:
        try:
            item = json.loads(str(row[1]))
        except ValueError as exc:
            raise SikaJournalUnavailable("journal_unreadable") from exc
        if (
            not isinstance(item, dict)
            or item.get("owner_id") != owner_id
            or item.get("previous_hash") != previous
            or item.get("digest") != _hash({k: v for k, v in item.items() if k != "digest"})
        ):
            raise SikaJournalUnavailable("journal_tampered_or_forked")
        debit = Decimal(str(item.get("debit_sika")))
        credit = Decimal(str(item.get("credit_sika")))
        if debit != credit or debit <= 0:
            raise SikaJournalUnavailable("journal_unbalanced")
        previous = str(item["digest"])
        entries.append(item)
    return entries


def history(owner_id: object) -> list[dict[str, object]]:
    owner = _owner(owner_id)
    try:
        with postgres_db.connect(readonly=True) as connection:
            return list(reversed(_read_entries(connection, owner)))
    except SikaJournalUnavailable:
        raise
    except Exception as exc:
        raise SikaJournalUnavailable("journal_read_failed") from exc


def post_reference(
    owner_id: object,
    *,
    debit_account: str,
    credit_account: str,
    amount_sika: object,
    memo: str = "",
) -> dict[str, object]:
    owner = _owner(owner_id)
    debit = str(debit_account or "").strip()[:80]
    credit = str(credit_account or "").strip()[:80]
    if not debit or not credit or debit == credit:
        raise ValueError("distinct_debit_and_credit_accounts_required")
    amount = Decimal(str(amount_sika))
    if amount <= 0:
        raise ValueError("positive_amount_required")
    clean_memo = str(memo or "").strip()[:240]
    journal_id = str(uuid4())
    try:
        with postgres_db.connect() as connection:
            connection.execute("SELECT pg_advisory_xact_lock(%s)", (25082508,))
            existing = _read_entries(connection, owner)
            previous = str(existing[-1]["digest"]) if existing else "GENESIS"
            payload = {
                "journal_id": journal_id,
                "owner_id": owner,
                "previous_hash": previous,
                "debit_account": debit,
                "credit_account": credit,
                "debit_sika": f"{amount:.2f}",
                "credit_sika": f"{amount:.2f}",
                "memo": clean_memo,
                "monetary": False,
                "executable": False,
            }
            entry = {**payload, "digest": _hash(payload)}
            body = json.dumps(entry, sort_keys=True, separators=(",", ":"), allow_nan=False)
            row = connection.execute(
                """INSERT INTO oap_workspace_records(
                       identity_id,workspace_id,title,body,status
                   ) VALUES (%s,'sika',%s,%s,'active')
                   RETURNING record_id""",
                (owner, f"SIKA-JOURNAL:{journal_id}", body),
            ).fetchone()
            record_id = str(row[0])

            connection.execute("SELECT pg_advisory_xact_lock(%s)", (25082509,))
            prior_audit = connection.execute(
                "SELECT curr_hash FROM audit_events ORDER BY event_seq DESC LIMIT 1"
            ).fetchone()
            prev_audit_hash = str(prior_audit[0]) if prior_audit else "GENESIS"
            audit_metadata = {
                "workspace_id": "sika",
                "journal_id": journal_id,
                "record_id": record_id,
                "digest": entry["digest"],
                "balanced": True,
                "monetary": False,
                "execution_authorised": False,
            }
            canonical = json.dumps(audit_metadata, sort_keys=True, separators=(",", ":"))
            current_hash = sha256((prev_audit_hash + canonical).encode("utf-8")).hexdigest()
            connection.execute(
                """INSERT INTO audit_events(
                       prev_hash,curr_hash,actor_id,actor_type,authority_level,
                       action,target,reason,correlation_id,metadata
                   ) VALUES (
                       %s,%s,%s,'AUTHENTICATED_USER',NULL,
                       'SIKA_REFERENCE_JOURNAL_POST',%s,
                       'owner_scoped_non_monetary_balanced_reference',%s,%s::jsonb
                   )""",
                (
                    prev_audit_hash,
                    current_hash,
                    owner,
                    f"sika_journal:{journal_id}",
                    journal_id,
                    canonical,
                ),
            )
            connection.commit()
    except (ValueError, SikaJournalUnavailable):
        raise
    except Exception as exc:
        raise SikaJournalUnavailable("journal_write_failed") from exc

    reread = history(owner)
    if not reread or reread[0].get("journal_id") != journal_id:
        raise SikaJournalUnavailable("journal_write_readback_mismatch")
    return {
        "entry": reread[0],
        "record_id": record_id,
        "audit_recorded": True,
        "balanced": True,
        "money_moved": False,
        "executable": False,
    }


def statement(owner_id: object) -> dict[str, object]:
    entries = history(owner_id)
    debits = sum((Decimal(str(e["debit_sika"])) for e in entries), Decimal(0))
    credits = sum((Decimal(str(e["credit_sika"])) for e in entries), Decimal(0))
    return {
        "entries": entries,
        "entry_count": len(entries),
        "total_debits_sika": f"{debits:.2f}",
        "total_credits_sika": f"{credits:.2f}",
        "reconciled": debits == credits,
        "difference_sika": f"{(debits - credits):.2f}",
        "money_claim": False,
        "executable": False,
    }
