"""Governed PRA/FCA permission-scope evidence for real-bank readiness.

A regulator authorisation decision does not automatically grant every regulated
capability. This store records the accepted permission scope, effective date,
mobilisation state and restrictions. It never grants permission by itself.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

from . import bank_authorisation, postgres_db

MIGRATION_VERSION = "bank_permission_scope_v1"
SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_bank_permission_scope (
        scope_id UUID PRIMARY KEY,
        status TEXT NOT NULL CHECK (status IN ('DRAFT','REVIEWED','ACCEPTED','REJECTED')),
        authorisation_letter_reference TEXT NOT NULL,
        part4a_permission_reference TEXT NOT NULL,
        financial_services_register_reference TEXT NOT NULL DEFAULT '',
        effective_from DATE NOT NULL,
        mobilisation BOOLEAN NOT NULL DEFAULT FALSE,
        deposit_cap_gbp NUMERIC(18,2),
        permitted_capabilities JSONB NOT NULL,
        restrictions JSONB NOT NULL,
        reviewed_by TEXT NOT NULL DEFAULT '',
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE INDEX IF NOT EXISTS ix_bank_permission_scope_created
       ON oap_bank_permission_scope(created_at DESC)""",
)


class PermissionScopeUnavailable(RuntimeError):
    """Raised when the governed permission-scope store is unavailable."""


@dataclass(frozen=True)
class PermissionScope:
    scope_id: str
    status: str
    authorisation_letter_reference: str
    part4a_permission_reference: str
    financial_services_register_reference: str
    effective_from: date
    mobilisation: bool
    deposit_cap_gbp: Decimal | None
    permitted_capabilities: frozenset[str]
    restrictions: tuple[str, ...]

    def effective(self, *, today: date | None = None) -> bool:
        return self.status == "ACCEPTED" and self.effective_from <= (today or date.today())

    def allows(self, capability: str, *, today: date | None = None) -> bool:
        if capability not in bank_authorisation.REGULATED_CAPABILITIES:
            return False
        return self.effective(today=today) and capability in self.permitted_capabilities


def _clean(value: object, *, limit: int) -> str:
    return str(value or "").strip()[:limit]


def _deposit_cap(value: object) -> Decimal | None:
    if value in (None, ""):
        return None
    try:
        parsed = Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("deposit_cap_gbp_invalid") from exc
    if not parsed.is_finite() or parsed < 0:
        raise ValueError("deposit_cap_gbp_invalid")
    return parsed


def init_schema(
    *,
    assume_yes: bool = False,
    dry_run: bool = False,
) -> dict[str, object]:
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
        raise PermissionScopeUnavailable(
            "bank_permission_scope_schema_init_failed"
        ) from exc
    return {
        **schema_status(),
        "migration": MIGRATION_VERSION,
        "dry_run": False,
        "human_authority_final": True,
    }


def schema_status() -> dict[str, object]:
    result: dict[str, object] = {
        "database_reachable": False,
        "scope_table_ready": False,
        "schema_ready": False,
        "error": None,
    }
    try:
        with postgres_db.connect(readonly=True) as connection:
            result["database_reachable"] = True
            row = connection.execute(
                """SELECT 1 FROM information_schema.tables
                   WHERE table_schema='public'
                     AND table_name='oap_bank_permission_scope'
                   LIMIT 1"""
            ).fetchone()
            ready = row is not None
            result["scope_table_ready"] = ready
            result["schema_ready"] = ready
    except Exception:  # noqa: BLE001
        result["error"] = "bank_permission_scope_store_unavailable"
    return result


def record_scope(
    *,
    status: object,
    authorisation_letter_reference: object,
    part4a_permission_reference: object,
    financial_services_register_reference: object = "",
    effective_from: date,
    mobilisation: bool = False,
    deposit_cap_gbp: object = None,
    permitted_capabilities: object,
    restrictions: object = (),
    reviewed_by: object = "",
) -> dict[str, object]:
    status_value = _clean(status, limit=20).upper()
    letter = _clean(authorisation_letter_reference, limit=1000)
    part4a = _clean(part4a_permission_reference, limit=1000)
    fsr = _clean(financial_services_register_reference, limit=1000)
    reviewer = _clean(reviewed_by, limit=240)

    if status_value not in {"DRAFT", "REVIEWED", "ACCEPTED", "REJECTED"}:
        raise ValueError("invalid_bank_permission_scope_status")
    if not letter or not part4a:
        raise ValueError("bank_permission_scope_references_required")
    if status_value in {"REVIEWED", "ACCEPTED", "REJECTED"} and not reviewer:
        raise ValueError("bank_permission_scope_reviewer_required")
    if not isinstance(effective_from, date):
        raise ValueError("bank_permission_scope_effective_date_required")

    capabilities = frozenset(str(item) for item in (permitted_capabilities or ()))
    unknown = capabilities - bank_authorisation.REGULATED_CAPABILITIES
    if unknown:
        raise ValueError("unknown_bank_permission_capability")
    restriction_values = tuple(
        cleaned
        for item in (restrictions or ())
        if (cleaned := _clean(item, limit=500))
    )
    cap = _deposit_cap(deposit_cap_gbp)
    if mobilisation and "accept_deposits" in capabilities and cap is None:
        raise ValueError("mobilisation_deposit_cap_required")

    scope_id = str(uuid.uuid4())
    try:
        with postgres_db.connect() as connection:
            row = connection.execute(
                """INSERT INTO oap_bank_permission_scope(
                       scope_id,status,authorisation_letter_reference,
                       part4a_permission_reference,financial_services_register_reference,
                       effective_from,mobilisation,deposit_cap_gbp,
                       permitted_capabilities,restrictions,reviewed_by
                   ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s)
                   RETURNING created_at""",
                (
                    scope_id,
                    status_value,
                    letter,
                    part4a,
                    fsr,
                    effective_from,
                    bool(mobilisation),
                    cap,
                    json.dumps(sorted(capabilities)),
                    json.dumps(list(restriction_values)),
                    reviewer,
                ),
            ).fetchone()
            connection.commit()
    except Exception as exc:
        raise PermissionScopeUnavailable(
            "bank_permission_scope_write_failed"
        ) from exc

    return {
        "scope_id": scope_id,
        "status": status_value,
        "effective_from": effective_from.isoformat(),
        "mobilisation": bool(mobilisation),
        "deposit_cap_gbp": str(cap) if cap is not None else None,
        "permitted_capabilities": sorted(capabilities),
        "created_at": row[0].isoformat(),
        "regulated_execution_enabled": False,
        "human_authority_final": True,
    }


def current_scope() -> PermissionScope | None:
    try:
        with postgres_db.connect(readonly=True) as connection:
            exists = connection.execute(
                """SELECT 1 FROM information_schema.tables
                   WHERE table_schema='public'
                     AND table_name='oap_bank_permission_scope'
                   LIMIT 1"""
            ).fetchone()
            if exists is None:
                return None
            row = connection.execute(
                """SELECT scope_id,status,authorisation_letter_reference,
                          part4a_permission_reference,financial_services_register_reference,
                          effective_from,mobilisation,deposit_cap_gbp,
                          permitted_capabilities,restrictions
                   FROM oap_bank_permission_scope
                   WHERE status='ACCEPTED'
                   ORDER BY created_at DESC,scope_id DESC
                   LIMIT 1"""
            ).fetchone()
    except Exception as exc:
        raise PermissionScopeUnavailable(
            "bank_permission_scope_read_failed"
        ) from exc
    if row is None:
        return None
    return PermissionScope(
        scope_id=str(row[0]),
        status=str(row[1]),
        authorisation_letter_reference=str(row[2]),
        part4a_permission_reference=str(row[3]),
        financial_services_register_reference=str(row[4]),
        effective_from=row[5],
        mobilisation=bool(row[6]),
        deposit_cap_gbp=Decimal(str(row[7])) if row[7] is not None else None,
        permitted_capabilities=frozenset(str(item) for item in (row[8] or [])),
        restrictions=tuple(str(item) for item in (row[9] or [])),
    )


def capability_allowed(capability: str) -> bool:
    scope = current_scope()
    return bool(scope and scope.allows(capability))
