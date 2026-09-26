"""Durable SIKA owner-device binding on canonical OAP stores.

Reuses the existing owner-scoped SIKA workspace plus global audit_events chain.
This module contains no web authentication and must only be called by an
authenticated host that has already resolved the canonical owner UUID.
"""
from __future__ import annotations

import json
from hashlib import sha256
from typing import Any
from uuid import UUID, uuid4

from . import postgres_db


class SikaDeviceBindingUnavailable(RuntimeError):
    pass


def _owner(value: object) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("canonical_owner_uuid_required") from exc


def _device(value: object) -> str:
    device = str(value or "").strip()
    if not device or len(device) > 120:
        raise ValueError("valid_device_id_required")
    return device


def _digest(payload: dict[str, object]) -> str:
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def _active_rows(connection: Any, owner_id: str) -> list[tuple[Any, ...]]:
    return connection.execute(
        """SELECT record_id,body,created_at
           FROM oap_workspace_records
           WHERE identity_id=%s AND workspace_id='sika'
             AND status='active' AND title LIKE 'SIKA-DEVICE:%%'
           ORDER BY created_at DESC, record_id DESC""",
        (owner_id,),
    ).fetchall()


def read(owner_id: object) -> dict[str, object]:
    owner = _owner(owner_id)
    try:
        with postgres_db.connect(readonly=True) as connection:
            rows = _active_rows(connection, owner)
    except Exception as exc:
        raise SikaDeviceBindingUnavailable("device_binding_read_failed") from exc
    if not rows:
        return {
            "owner_id": owner,
            "bound": False,
            "durable": True,
            "founder_auth_touched": False,
        }
    try:
        item = json.loads(str(rows[0][1]))
    except ValueError as exc:
        raise SikaDeviceBindingUnavailable("device_binding_unreadable") from exc
    if (
        not isinstance(item, dict)
        or item.get("owner_id") != owner
        or item.get("digest") != _digest({k: v for k, v in item.items() if k != "digest"})
    ):
        raise SikaDeviceBindingUnavailable("device_binding_tampered")
    return {
        **item,
        "record_id": str(rows[0][0]),
        "bound": True,
        "durable": True,
        "founder_auth_touched": False,
    }


def bind_authenticated_owner(owner_id: object, device_id: object) -> dict[str, object]:
    owner = _owner(owner_id)
    device = _device(device_id)
    binding_id = str(uuid4())
    payload = {
        "binding_id": binding_id,
        "owner_id": owner,
        "device_id": device,
        "scope": "SIKA_BANK_APP",
        "esim_provisioned": False,
        "identity_authority_changed": False,
    }
    item = {**payload, "digest": _digest(payload)}
    body = json.dumps(item, sort_keys=True, separators=(",", ":"), allow_nan=False)

    try:
        with postgres_db.connect() as connection:
            connection.execute("SELECT pg_advisory_xact_lock(%s)", (25082511,))
            rows = _active_rows(connection, owner)
            if rows:
                current = json.loads(str(rows[0][1]))
                if current.get("device_id") != device:
                    raise ValueError("owner_already_bound_to_different_device")
                return {
                    **current,
                    "record_id": str(rows[0][0]),
                    "bound": True,
                    "durable": True,
                    "audit_recorded": True,
                    "idempotent": True,
                    "founder_auth_touched": False,
                }

            reverse = connection.execute(
                """SELECT identity_id FROM oap_workspace_records
                   WHERE workspace_id='sika' AND status='active'
                     AND title LIKE 'SIKA-DEVICE:%%'
                     AND body::jsonb->>'device_id'=%s
                   LIMIT 1""",
                (device,),
            ).fetchone()
            if reverse and str(reverse[0]) != owner:
                raise ValueError("device_already_bound_to_different_owner")

            row = connection.execute(
                """INSERT INTO oap_workspace_records(
                       identity_id,workspace_id,title,body,status
                   ) VALUES (%s,'sika',%s,%s,'active')
                   RETURNING record_id""",
                (owner, f"SIKA-DEVICE:{binding_id}", body),
            ).fetchone()
            record_id = str(row[0])

            connection.execute("SELECT pg_advisory_xact_lock(%s)", (25082509,))
            prior = connection.execute(
                "SELECT curr_hash FROM audit_events ORDER BY event_seq DESC LIMIT 1"
            ).fetchone()
            prev_hash = str(prior[0]) if prior else "GENESIS"
            metadata = {
                "workspace_id": "sika",
                "binding_id": binding_id,
                "record_id": record_id,
                "owner_id": owner,
                "device_digest": sha256(device.encode()).hexdigest(),
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
                       'SIKA_DEVICE_BIND',%s,
                       'authenticated_owner_scoped_device_binding',%s,%s::jsonb
                   )""",
                (
                    prev_hash,
                    curr_hash,
                    owner,
                    f"sika_device:{binding_id}",
                    binding_id,
                    canonical,
                ),
            )
            connection.commit()
    except ValueError:
        raise
    except Exception as exc:
        raise SikaDeviceBindingUnavailable("device_binding_write_failed") from exc

    reread = read(owner)
    if not reread.get("bound") or reread.get("device_id") != device:
        raise SikaDeviceBindingUnavailable("device_binding_readback_mismatch")
    return {
        **reread,
        "audit_recorded": True,
        "idempotent": False,
    }


def recover_authenticated_owner(owner_id: object, device_id: object) -> dict[str, object]:
    owner = _owner(owner_id)
    device = _device(device_id)
    current = read(owner)
    if not current.get("bound") or current.get("device_id") != device:
        return {
            "recovered": False,
            "reason": "binding_not_found",
            "owner_id": owner,
            "founder_auth_touched": False,
        }
    try:
        with postgres_db.connect() as connection:
            connection.execute("SELECT pg_advisory_xact_lock(%s)", (25082511,))
            connection.execute(
                """UPDATE oap_workspace_records
                   SET status='archived', updated_at=CURRENT_TIMESTAMP
                   WHERE record_id=%s AND identity_id=%s
                     AND workspace_id='sika' AND status='active'""",
                (current["record_id"], owner),
            )
            connection.execute("SELECT pg_advisory_xact_lock(%s)", (25082509,))
            prior = connection.execute(
                "SELECT curr_hash FROM audit_events ORDER BY event_seq DESC LIMIT 1"
            ).fetchone()
            prev_hash = str(prior[0]) if prior else "GENESIS"
            correlation_id = str(uuid4())
            metadata = {
                "workspace_id": "sika",
                "record_id": current["record_id"],
                "owner_id": owner,
                "device_digest": sha256(device.encode()).hexdigest(),
                "recovery": "archive_binding",
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
                       'SIKA_DEVICE_RECOVERY',%s,
                       'authenticated_owner_scoped_binding_recovery',%s,%s::jsonb
                   )""",
                (
                    prev_hash,
                    curr_hash,
                    owner,
                    f"sika_device:{current['record_id']}",
                    correlation_id,
                    canonical,
                ),
            )
            connection.commit()
    except Exception as exc:
        raise SikaDeviceBindingUnavailable("device_binding_recovery_failed") from exc
    return {
        "recovered": True,
        "owner_id": owner,
        "device_id": device,
        "archived": True,
        "audit_recorded": True,
        "founder_auth_touched": False,
    }


def readiness() -> dict[str, object]:
    return {
        "canonical_store_reused": True,
        "workspace_id": "sika",
        "audit_chain_reused": True,
        "owner_uuid_required": True,
        "durable_bind_function_present": True,
        "durable_recovery_function_present": True,
        "standalone_public_write_enabled": False,
        "authenticated_host_required": True,
        "founder_auth_touched": False,
        "production_ready": False,
        "reason": "authenticated_owner_session_adapter_required",
    }
