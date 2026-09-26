"""Durable owner-scoped SIKA Security Ledger.

Reuses the canonical SIKA workspace and audit_events chain. Stores security
policy/events only; it cannot move money or alter Founder authentication.
"""
from __future__ import annotations

import json
from hashlib import sha256
from typing import Any
from uuid import UUID, uuid4

from . import postgres_db


class SikaSecurityLedgerUnavailable(RuntimeError):
    pass


def _owner(value: object) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("canonical_owner_uuid_required") from exc


def _digest(payload: dict[str, object]) -> str:
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def _read_rows(connection: Any, owner: str) -> list[tuple[Any, ...]]:
    return connection.execute(
        """SELECT record_id,title,body,created_at
           FROM oap_workspace_records
           WHERE identity_id=%s AND workspace_id='sika'
             AND status='active' AND title LIKE 'SIKA-SECURITY:%%'
           ORDER BY created_at DESC, record_id DESC""",
        (owner,),
    ).fetchall()


def history(owner_id: object, *, limit: int = 50) -> list[dict[str, object]]:
    owner = _owner(owner_id)
    safe_limit = max(1, min(int(limit), 100))
    try:
        with postgres_db.connect(readonly=True) as connection:
            rows = _read_rows(connection, owner)[:safe_limit]
    except Exception as exc:
        raise SikaSecurityLedgerUnavailable("security_ledger_read_failed") from exc
    out: list[dict[str, object]] = []
    for record_id, _title, body, created_at in rows:
        try:
            item = json.loads(str(body))
        except ValueError as exc:
            raise SikaSecurityLedgerUnavailable("security_ledger_unreadable") from exc
        if (
            not isinstance(item, dict)
            or item.get("owner_id") != owner
            or item.get("digest") != _digest({k: v for k, v in item.items() if k != "digest"})
        ):
            raise SikaSecurityLedgerUnavailable("security_ledger_tampered")
        out.append({**item, "record_id": str(record_id), "created_at": str(created_at)})
    return out


def record_authenticated_owner(
    owner_id: object,
    *,
    event_type: str,
    severity: str,
    details: dict[str, object] | None = None,
) -> dict[str, object]:
    owner = _owner(owner_id)
    kind = str(event_type or "").strip().upper()[:80]
    level = str(severity or "").strip().upper()[:24]
    if not kind:
        raise ValueError("security_event_type_required")
    if level not in {"INFO", "NOTICE", "WARNING", "HIGH", "CRITICAL"}:
        raise ValueError("valid_security_severity_required")
    event_id = str(uuid4())
    payload = {
        "event_id": event_id,
        "owner_id": owner,
        "event_type": kind,
        "severity": level,
        "details": dict(details or {}),
        "money_moved": False,
        "execution_authorised": False,
        "founder_auth_touched": False,
    }
    item = {**payload, "digest": _digest(payload)}
    body = json.dumps(item, sort_keys=True, separators=(",", ":"), allow_nan=False)
    try:
        with postgres_db.connect() as connection:
            connection.execute("SELECT pg_advisory_xact_lock(%s)", (25082513,))
            row = connection.execute(
                """INSERT INTO oap_workspace_records(
                       identity_id,workspace_id,title,body,status
                   ) VALUES (%s,'sika',%s,%s,'active')
                   RETURNING record_id""",
                (owner, f"SIKA-SECURITY:{event_id}", body),
            ).fetchone()
            record_id = str(row[0])

            connection.execute("SELECT pg_advisory_xact_lock(%s)", (25082509,))
            prior = connection.execute(
                "SELECT curr_hash FROM audit_events ORDER BY event_seq DESC LIMIT 1"
            ).fetchone()
            prev_hash = str(prior[0]) if prior else "GENESIS"
            metadata = {
                "workspace_id": "sika",
                "security_event_id": event_id,
                "record_id": record_id,
                "owner_id": owner,
                "event_type": kind,
                "severity": level,
                "digest": item["digest"],
                "execution_authorised": False,
                "founder_auth_touched": False,
            }
            canonical = json.dumps(metadata, sort_keys=True, separators=(",", ":"))
            curr_hash = sha256((prev_hash + canonical).encode()).hexdigest()
            connection.execute(
                """INSERT INTO audit_events(
                       prev_hash,curr_hash,actor_id,actor_type,authority_level,
                       action,target,reason,correlation_id,metadata
                   ) VALUES (
                       %s,%s,%s,'AUTHENTICATED_USER',NULL,
                       'SIKA_SECURITY_EVENT',%s,
                       'owner_scoped_security_event',%s,%s::jsonb
                   )""",
                (
                    prev_hash,
                    curr_hash,
                    owner,
                    f"sika_security:{event_id}",
                    event_id,
                    canonical,
                ),
            )
            connection.commit()
    except ValueError:
        raise
    except Exception as exc:
        raise SikaSecurityLedgerUnavailable("security_ledger_write_failed") from exc

    reread = history(owner, limit=1)
    if not reread or reread[0].get("event_id") != event_id:
        raise SikaSecurityLedgerUnavailable("security_ledger_readback_mismatch")
    return {**reread[0], "audit_recorded": True}


def readiness() -> dict[str, object]:
    return {
        "canonical_store_reused": True,
        "workspace_id": "sika",
        "audit_chain_reused": True,
        "owner_uuid_required": True,
        "durable_security_event_store": True,
        "standalone_public_write_enabled": False,
        "authenticated_host_required": True,
        "money_execution_enabled": False,
        "founder_auth_touched": False,
    }
