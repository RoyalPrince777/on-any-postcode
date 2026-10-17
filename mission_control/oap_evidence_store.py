"""Durable owner-scoped receipt store for the OAP-wide 700 evidence fabric."""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any
from uuid import UUID, uuid4

from . import oap_evidence_fabric, postgres_db

GENESIS_HASH = "0" * 64
MIGRATION_VERSION = "oap_whole_company_evidence_fabric_v1"

SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_whole_company_evidence_receipts (
        receipt_id UUID PRIMARY KEY,
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        check_id TEXT NOT NULL,
        state TEXT NOT NULL CHECK (state IN ('PASS','FAIL','CONFLICTING','UNKNOWN','N/A')),
        source_system TEXT NOT NULL,
        evidence_reference TEXT NOT NULL,
        failure_reason TEXT NOT NULL DEFAULT '',
        recovery_requirement TEXT NOT NULL DEFAULT '',
        previous_receipt_hash TEXT NOT NULL CHECK (length(previous_receipt_hash)=64),
        receipt_hash TEXT NOT NULL UNIQUE CHECK (length(receipt_hash)=64),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE INDEX IF NOT EXISTS ix_oap_whole_company_evidence_owner_created
       ON oap_whole_company_evidence_receipts(owner_identity_id,created_at,receipt_id)""",
)
MIGRATION_CHECKSUM = hashlib.sha256("\n".join(SCHEMA_STATEMENTS).encode()).hexdigest()


class OAPEvidenceStoreUnavailable(RuntimeError):
    pass


def _uuid(value: object, name: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"invalid_{name}") from exc


def _clean(value: object, *, limit: int, required: bool = True) -> str:
    text = " ".join(str(value or "").split())[:limit]
    if required and not text:
        raise ValueError("required_value_missing")
    return text


def _hash(value: object) -> str:
    text = str(value or "")
    if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
        raise ValueError("invalid_hash")
    return text


def _known_ids() -> set[str]:
    return {cell["check_id"] for cell in oap_evidence_fabric.catalogue()}


def canonical_payload(
    *,
    receipt_id: str,
    owner_identity_id: str,
    check_id: str,
    state: str,
    source_system: str,
    evidence_reference: str,
    failure_reason: str,
    recovery_requirement: str,
    previous_receipt_hash: str,
) -> bytes:
    return json.dumps(
        {
            "check_id": check_id,
            "evidence_reference": evidence_reference,
            "failure_reason": failure_reason,
            "owner_identity_id": owner_identity_id,
            "previous_receipt_hash": previous_receipt_hash,
            "receipt_id": receipt_id,
            "recovery_requirement": recovery_requirement,
            "source_system": source_system,
            "state": state,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode()


def build_receipt(
    *,
    owner_identity_id: object,
    check_id: object,
    state: object,
    source_system: object,
    evidence_reference: object,
    failure_reason: object = "",
    recovery_requirement: object = "",
    previous_receipt_hash: object = GENESIS_HASH,
    receipt_id: object = None,
) -> dict[str, str]:
    owner = _uuid(owner_identity_id, "owner_identity_id")
    rid = _uuid(receipt_id or str(uuid4()), "receipt_id")
    check = str(check_id or "").strip().upper()
    if check not in _known_ids():
        raise ValueError("invalid_check_id")
    state_value = str(state or "").strip().upper()
    if state_value not in oap_evidence_fabric.CELL_STATES:
        raise ValueError("invalid_state")
    source = _clean(source_system, limit=120)
    reference = _clean(evidence_reference, limit=500)
    failure = _clean(failure_reason, limit=500, required=False)
    recovery = _clean(recovery_requirement, limit=500, required=False)
    previous = _hash(previous_receipt_hash)
    payload = canonical_payload(
        receipt_id=rid,
        owner_identity_id=owner,
        check_id=check,
        state=state_value,
        source_system=source,
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
        "source_system": source,
        "evidence_reference": reference,
        "failure_reason": failure,
        "recovery_requirement": recovery,
        "previous_receipt_hash": previous,
        "receipt_hash": hashlib.sha256(payload).hexdigest(),
    }


def verify_chain(receipts: object) -> dict[str, object]:
    rows = receipts if isinstance(receipts, list) else []
    previous = GENESIS_HASH
    checked = 0
    verified = True
    for row in rows:
        if not isinstance(row, Mapping):
            verified = False
            break
        try:
            built = build_receipt(
                owner_identity_id=row.get("owner_identity_id"),
                check_id=row.get("check_id"),
                state=row.get("state"),
                source_system=row.get("source_system"),
                evidence_reference=row.get("evidence_reference"),
                failure_reason=row.get("failure_reason"),
                recovery_requirement=row.get("recovery_requirement"),
                previous_receipt_hash=row.get("previous_receipt_hash"),
                receipt_id=row.get("receipt_id"),
            )
            claimed = _hash(row.get("receipt_hash"))
        except (TypeError, ValueError):
            verified = False
            break
        if built["previous_receipt_hash"] != previous or built["receipt_hash"] != claimed:
            verified = False
            break
        previous = claimed
        checked += 1
    return {
        "chain_verified": verified and checked == len(rows),
        "receipt_count": checked,
        "head_hash": previous if checked else GENESIS_HASH,
    }


class OAPEvidenceStore:
    def append_receipt(self, **values: object) -> dict[str, str]:
        owner = _uuid(values.get("owner_identity_id"), "owner_identity_id")
        with postgres_db.connect() as connection:
            previous_row = connection.execute(
                """SELECT receipt_hash FROM oap_whole_company_evidence_receipts
                   WHERE owner_identity_id=%s
                   ORDER BY created_at DESC,receipt_id DESC LIMIT 1 FOR UPDATE""",
                (owner,),
            ).fetchone()
            receipt = build_receipt(
                **values,
                previous_receipt_hash=(
                    str(previous_row[0]) if previous_row else GENESIS_HASH
                ),
            )
            connection.execute(
                """INSERT INTO oap_whole_company_evidence_receipts(
                   receipt_id,owner_identity_id,check_id,state,source_system,
                   evidence_reference,failure_reason,recovery_requirement,
                   previous_receipt_hash,receipt_hash)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    receipt["receipt_id"], receipt["owner_identity_id"],
                    receipt["check_id"], receipt["state"], receipt["source_system"],
                    receipt["evidence_reference"], receipt["failure_reason"],
                    receipt["recovery_requirement"], receipt["previous_receipt_hash"],
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
                         AND table_name='oap_whole_company_evidence_receipts'
                       LIMIT 1"""
                ).fetchone()
                if exists is None:
                    return []
                rows = connection.execute(
                    """SELECT receipt_id,owner_identity_id,check_id,state,source_system,
                              evidence_reference,failure_reason,recovery_requirement,
                              previous_receipt_hash,receipt_hash,created_at
                       FROM oap_whole_company_evidence_receipts
                       WHERE owner_identity_id=%s
                       ORDER BY created_at,receipt_id""",
                    (owner,),
                ).fetchall()
        except Exception as exc:
            raise OAPEvidenceStoreUnavailable("oap_evidence_store_read_failed") from exc
        return [
            {
                "receipt_id": str(row[0]),
                "owner_identity_id": str(row[1]),
                "check_id": str(row[2]),
                "state": str(row[3]),
                "source_system": str(row[4]),
                "evidence_reference": str(row[5]),
                "failure_reason": str(row[6]),
                "recovery_requirement": str(row[7]),
                "previous_receipt_hash": str(row[8]),
                "receipt_hash": str(row[9]),
                "observed_at": row[10].isoformat(),
            }
            for row in rows
        ]

    def projection(self, *, owner_identity_id: object) -> dict[str, Any]:
        rows = self.read_receipts(owner_identity_id=owner_identity_id)
        chain = verify_chain(rows)
        if not chain["chain_verified"]:
            return {
                **oap_evidence_fabric.snapshot(),
                **chain,
                "store_fail_closed": True,
            }
        projected = [
            {
                "check_id": row["check_id"],
                "state": row["state"],
                "source_system": row["source_system"],
                "evidence_reference": row["evidence_reference"],
                "failure_reason": row["failure_reason"],
                "recovery_requirement": row["recovery_requirement"],
                "observed_at": row["observed_at"],
            }
            for row in rows
        ]
        return {
            **oap_evidence_fabric.snapshot(projected),
            **chain,
            "store_fail_closed": True,
        }


def status() -> dict[str, object]:
    return {
        "name": "OAP Whole-Company Evidence Store",
        "migration": MIGRATION_VERSION,
        "checksum": MIGRATION_CHECKSUM,
        "append_only": True,
        "hash_chained": True,
        "owner_scoped": True,
        "whole_company_scope": True,
        "execution_authority_granted": False,
        "human_authority_final": True,
        "full_green": False,
    }
