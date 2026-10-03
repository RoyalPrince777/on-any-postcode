"""Durable append-only evidence receipts for the 700-cell Company Intelligence registry.

Receipts are owner-scoped, hash-chained and read-only when projected into SMI.
Persistence records evidence state; it never grants execution, legal authority,
regulatory permission, deployment, payment authority or Founder Final.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any
from uuid import UUID, uuid4

from . import company_intelligence_evidence_registry, postgres_db

GENESIS_HASH = "0" * 64
MIGRATION_VERSION = "oap_company_intelligence_700_evidence_v1"
MAX_REF = 500
MAX_TEXT = 500

SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_company_intelligence_evidence_receipts (
        receipt_id UUID PRIMARY KEY,
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        check_id TEXT NOT NULL,
        state TEXT NOT NULL CHECK (state IN ('PASS','FAIL','CONFLICTING','UNKNOWN','N/A')),
        evidence_reference TEXT NOT NULL,
        failure_reason TEXT NOT NULL DEFAULT '',
        recovery_requirement TEXT NOT NULL DEFAULT '',
        previous_receipt_hash TEXT NOT NULL CHECK (length(previous_receipt_hash)=64),
        receipt_hash TEXT NOT NULL UNIQUE CHECK (length(receipt_hash)=64),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE INDEX IF NOT EXISTS ix_company_intelligence_evidence_owner_check_created
       ON oap_company_intelligence_evidence_receipts(
           owner_identity_id,check_id,created_at,receipt_id
       )""",
)
MIGRATION_CHECKSUM = hashlib.sha256("\n".join(SCHEMA_STATEMENTS).encode()).hexdigest()


class CompanyIntelligenceEvidenceUnavailable(RuntimeError):
    """Raised when durable 700-cell evidence cannot be read or written."""


def _uuid(value: object, name: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"invalid_{name}") from exc


def _text(value: object, name: str, *, limit: int, optional: bool = False) -> str:
    cleaned = " ".join(str(value or "").split())[:limit]
    if not cleaned and not optional:
        raise ValueError(f"invalid_{name}")
    return cleaned


def _hash(value: object, name: str) -> str:
    text = str(value or "")
    if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
        raise ValueError(f"invalid_{name}")
    return text


def _known_check_ids() -> set[str]:
    return {cell["check_id"] for cell in company_intelligence_evidence_registry.cell_catalogue()}


def canonical_receipt_payload(
    *,
    receipt_id: str,
    owner_identity_id: str,
    check_id: str,
    state: str,
    evidence_reference: str,
    failure_reason: str,
    recovery_requirement: str,
    previous_receipt_hash: str,
) -> bytes:
    payload = {
        "check_id": check_id,
        "evidence_reference": evidence_reference,
        "failure_reason": failure_reason,
        "owner_identity_id": owner_identity_id,
        "previous_receipt_hash": previous_receipt_hash,
        "receipt_id": receipt_id,
        "recovery_requirement": recovery_requirement,
        "state": state,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()


def build_receipt(
    *,
    owner_identity_id: object,
    check_id: object,
    state: object,
    evidence_reference: object,
    failure_reason: object = "",
    recovery_requirement: object = "",
    previous_receipt_hash: object = GENESIS_HASH,
    receipt_id: object = None,
) -> dict[str, str]:
    owner = _uuid(owner_identity_id, "owner_identity_id")
    rid = _uuid(receipt_id or str(uuid4()), "receipt_id")
    check = str(check_id or "").strip().upper()
    if check not in _known_check_ids():
        raise ValueError("invalid_check_id")
    state_value = str(state or "").strip().upper()
    if state_value not in company_intelligence_evidence_registry.CELL_STATES:
        raise ValueError("invalid_state")
    reference = _text(evidence_reference, "evidence_reference", limit=MAX_REF)
    failure = _text(failure_reason, "failure_reason", limit=MAX_TEXT, optional=True)
    recovery = _text(
        recovery_requirement,
        "recovery_requirement",
        limit=MAX_TEXT,
        optional=True,
    )
    previous = _hash(previous_receipt_hash, "previous_receipt_hash")
    body = canonical_receipt_payload(
        receipt_id=rid,
        owner_identity_id=owner,
        check_id=check,
        state=state_value,
        evidence_reference=reference,
        failure_reason=failure,
        recovery_requirement=recovery,
        previous_receipt_hash=previous,
    )
    return {
        "receipt_id": rid,
        "owner_identity_id": owner,
        "check_id": check,
        "state": state_value,
        "evidence_reference": reference,
        "failure_reason": failure,
        "recovery_requirement": recovery,
        "previous_receipt_hash": previous,
        "receipt_hash": hashlib.sha256(body).hexdigest(),
    }


def verify_receipt_chain(receipts: object) -> dict[str, object]:
    rows = receipts if isinstance(receipts, list) else []
    previous = GENESIS_HASH
    checked = 0
    verified = True
    for row in rows:
        if not isinstance(row, Mapping):
            verified = False
            break
        try:
            rid = _uuid(row.get("receipt_id"), "receipt_id")
            owner = _uuid(row.get("owner_identity_id"), "owner_identity_id")
            check = str(row.get("check_id") or "").strip().upper()
            if check not in _known_check_ids():
                raise ValueError("invalid_check_id")
            state = str(row.get("state") or "").strip().upper()
            if state not in company_intelligence_evidence_registry.CELL_STATES:
                raise ValueError("invalid_state")
            reference = _text(
                row.get("evidence_reference"),
                "evidence_reference",
                limit=MAX_REF,
            )
            failure = _text(
                row.get("failure_reason"),
                "failure_reason",
                limit=MAX_TEXT,
                optional=True,
            )
            recovery = _text(
                row.get("recovery_requirement"),
                "recovery_requirement",
                limit=MAX_TEXT,
                optional=True,
            )
            prev = _hash(row.get("previous_receipt_hash"), "previous_receipt_hash")
            claimed = _hash(row.get("receipt_hash"), "receipt_hash")
        except (TypeError, ValueError):
            verified = False
            break
        if prev != previous:
            verified = False
            break
        actual = hashlib.sha256(
            canonical_receipt_payload(
                receipt_id=rid,
                owner_identity_id=owner,
                check_id=check,
                state=state,
                evidence_reference=reference,
                failure_reason=failure,
                recovery_requirement=recovery,
                previous_receipt_hash=prev,
            )
        ).hexdigest()
        if actual != claimed:
            verified = False
            break
        previous = claimed
        checked += 1
    return {
        "chain_verified": verified and checked == len(rows),
        "receipt_count": checked,
        "head_hash": previous if checked else GENESIS_HASH,
        "execution_authority_granted": False,
        "human_authority_final": True,
    }


def schema_status() -> dict[str, object]:
    result: dict[str, object] = {
        "database_reachable": False,
        "evidence_table_ready": False,
        "schema_ready": False,
        "error": None,
    }
    try:
        with postgres_db.connect(readonly=True) as connection:
            result["database_reachable"] = True
            row = connection.execute(
                """SELECT 1 FROM information_schema.tables
                   WHERE table_schema='public'
                     AND table_name='oap_company_intelligence_evidence_receipts'
                   LIMIT 1"""
            ).fetchone()
            result["evidence_table_ready"] = row is not None
            result["schema_ready"] = row is not None
    except Exception:  # noqa: BLE001
        result["error"] = "company_intelligence_evidence_store_unavailable"
    return result


class CompanyIntelligenceEvidenceStore:
    """Append and read owner-scoped 700-cell evidence receipts."""

    def append_receipt(
        self,
        *,
        owner_identity_id: object,
        check_id: object,
        state: object,
        evidence_reference: object,
        failure_reason: object = "",
        recovery_requirement: object = "",
    ) -> dict[str, str]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        with postgres_db.connect() as connection:
            previous_row = connection.execute(
                """SELECT receipt_hash
                   FROM oap_company_intelligence_evidence_receipts
                   WHERE owner_identity_id=%s
                   ORDER BY created_at DESC,receipt_id DESC
                   LIMIT 1 FOR UPDATE""",
                (owner,),
            ).fetchone()
            previous = str(previous_row[0]) if previous_row else GENESIS_HASH
            receipt = build_receipt(
                owner_identity_id=owner,
                check_id=check_id,
                state=state,
                evidence_reference=evidence_reference,
                failure_reason=failure_reason,
                recovery_requirement=recovery_requirement,
                previous_receipt_hash=previous,
            )
            connection.execute(
                """INSERT INTO oap_company_intelligence_evidence_receipts(
                       receipt_id,owner_identity_id,check_id,state,evidence_reference,
                       failure_reason,recovery_requirement,previous_receipt_hash,receipt_hash
                   ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    receipt["receipt_id"],
                    owner,
                    receipt["check_id"],
                    receipt["state"],
                    receipt["evidence_reference"],
                    receipt["failure_reason"],
                    receipt["recovery_requirement"],
                    receipt["previous_receipt_hash"],
                    receipt["receipt_hash"],
                ),
            )
            connection.commit()
        return receipt

    def read_receipts(self, *, owner_identity_id: object) -> list[dict[str, Any]]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        try:
            with postgres_db.connect(readonly=True) as connection:
                exists = connection.execute(
                    """SELECT 1 FROM information_schema.tables
                       WHERE table_schema='public'
                         AND table_name='oap_company_intelligence_evidence_receipts'
                       LIMIT 1"""
                ).fetchone()
                if exists is None:
                    return []
                rows = connection.execute(
                    """SELECT receipt_id,owner_identity_id,check_id,state,evidence_reference,
                              failure_reason,recovery_requirement,previous_receipt_hash,
                              receipt_hash,created_at
                       FROM oap_company_intelligence_evidence_receipts
                       WHERE owner_identity_id=%s
                       ORDER BY created_at,receipt_id""",
                    (owner,),
                ).fetchall()
        except Exception as exc:
            raise CompanyIntelligenceEvidenceUnavailable(
                "company_intelligence_evidence_read_failed"
            ) from exc
        return [
            {
                "receipt_id": str(row[0]),
                "owner_identity_id": str(row[1]),
                "check_id": str(row[2]),
                "state": str(row[3]),
                "evidence_reference": str(row[4]),
                "failure_reason": str(row[5]),
                "recovery_requirement": str(row[6]),
                "previous_receipt_hash": str(row[7]),
                "receipt_hash": str(row[8]),
                "observed_at": row[9].isoformat(),
            }
            for row in rows
        ]

    def projection(self, *, owner_identity_id: object) -> dict[str, Any]:
        rows = self.read_receipts(owner_identity_id=owner_identity_id)
        chain = verify_receipt_chain(rows)
        if not chain["chain_verified"]:
            return {
                **company_intelligence_evidence_registry.snapshot(),
                "receipt_chain_verified": False,
                "receipt_count": chain["receipt_count"],
                "head_hash": chain["head_hash"],
                "store_fail_closed": True,
            }
        registry_rows = [
            {
                "check_id": row["check_id"],
                "state": row["state"],
                "evidence_reference": row["evidence_reference"],
                "failure_reason": row["failure_reason"],
                "recovery_requirement": row["recovery_requirement"],
                "observed_at": row["observed_at"],
            }
            for row in rows
        ]
        return {
            **company_intelligence_evidence_registry.snapshot(registry_rows),
            "receipt_chain_verified": True,
            "receipt_count": chain["receipt_count"],
            "head_hash": chain["head_hash"],
            "store_fail_closed": True,
        }


def status() -> dict[str, object]:
    schema = schema_status()
    return {
        "name": "OAP Company Intelligence 700 Evidence Store",
        "migration": MIGRATION_VERSION,
        "checksum": MIGRATION_CHECKSUM,
        "append_only": True,
        "hash_chained": True,
        "owner_scoped": True,
        "schema": schema,
        "execution_authority_granted": False,
        "human_authority_final": True,
        "full_green": False,
    }
