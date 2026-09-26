"""Durable SIKA bank-app credential store.

Reuses canonical owner-scoped SIKA workspace records. Stores only password
verifiers, never plaintext passwords. This module does not authenticate users
itself and must only be called after the authenticated OAP owner has been
resolved server-side.

No Founder authentication code is touched.
"""
from __future__ import annotations

import json
from hashlib import sha256
from typing import Any
from uuid import UUID, uuid4

from werkzeug.security import check_password_hash, generate_password_hash

from . import postgres_db


class SikaCredentialStoreUnavailable(RuntimeError):
    pass


MIN_PASSWORD_LENGTH = 12
MAX_PASSWORD_LENGTH = 128


def _owner(value: object) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("canonical_owner_uuid_required") from exc


def _password(value: object) -> str:
    password = str(value or "")
    if len(password) < MIN_PASSWORD_LENGTH or len(password) > MAX_PASSWORD_LENGTH:
        raise ValueError("bank_app_password_must_be_12_to_128_characters")
    if not password.strip():
        raise ValueError("bank_app_password_required")
    return password


def _digest(payload: dict[str, object]) -> str:
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def _active_rows(connection: Any, owner_id: str) -> list[tuple[Any, ...]]:
    return connection.execute(
        """SELECT record_id,body,created_at
           FROM oap_workspace_records
           WHERE identity_id=%s AND workspace_id='sika'
             AND status='active' AND title LIKE 'SIKA-CREDENTIAL:%%'
           ORDER BY created_at DESC, record_id DESC""",
        (owner_id,),
    ).fetchall()


def status(owner_id: object) -> dict[str, object]:
    owner = _owner(owner_id)
    try:
        with postgres_db.connect(readonly=True) as connection:
            rows = _active_rows(connection, owner)
    except Exception as exc:
        raise SikaCredentialStoreUnavailable("credential_read_failed") from exc
    if not rows:
        return {
            "owner_id": owner,
            "credential_present": False,
            "durable": True,
            "founder_auth_touched": False,
        }
    try:
        item = json.loads(str(rows[0][1]))
    except ValueError as exc:
        raise SikaCredentialStoreUnavailable("credential_unreadable") from exc
    safe = {k: v for k, v in item.items() if k != "password_hash"}
    if (
        not isinstance(item, dict)
        or item.get("owner_id") != owner
        or item.get("digest") != _digest({k: v for k, v in item.items() if k != "digest"})
    ):
        raise SikaCredentialStoreUnavailable("credential_tampered")
    return {
        **safe,
        "record_id": str(rows[0][0]),
        "credential_present": True,
        "durable": True,
        "password_hash_returned": False,
        "founder_auth_touched": False,
    }


def create_authenticated_owner(owner_id: object, password: object) -> dict[str, object]:
    owner = _owner(owner_id)
    secret = _password(password)
    credential_id = str(uuid4())
    password_hash = generate_password_hash(secret, method="scrypt")
    payload = {
        "credential_id": credential_id,
        "owner_id": owner,
        "scope": "SIKA_BANK_APP",
        "password_hash": password_hash,
        "founder_auth_touched": False,
    }
    item = {**payload, "digest": _digest(payload)}
    body = json.dumps(item, sort_keys=True, separators=(",", ":"), allow_nan=False)

    try:
        with postgres_db.connect() as connection:
            connection.execute("SELECT pg_advisory_xact_lock(%s)", (25082512,))
            rows = _active_rows(connection, owner)
            if rows:
                return {
                    "created": False,
                    "reason": "bank_app_credential_already_exists",
                    "owner_id": owner,
                    "password_hash_returned": False,
                    "founder_auth_touched": False,
                }

            row = connection.execute(
                """INSERT INTO oap_workspace_records(
                       identity_id,workspace_id,title,body,status
                   ) VALUES (%s,'sika',%s,%s,'active')
                   RETURNING record_id""",
                (owner, f"SIKA-CREDENTIAL:{credential_id}", body),
            ).fetchone()
            record_id = str(row[0])

            connection.execute("SELECT pg_advisory_xact_lock(%s)", (25082509,))
            prior = connection.execute(
                "SELECT curr_hash FROM audit_events ORDER BY event_seq DESC LIMIT 1"
            ).fetchone()
            prev_hash = str(prior[0]) if prior else "GENESIS"
            metadata = {
                "workspace_id": "sika",
                "credential_id": credential_id,
                "record_id": record_id,
                "owner_id": owner,
                "password_hash_returned": False,
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
                       'SIKA_BANK_CREDENTIAL_CREATE',%s,
                       'authenticated_owner_scoped_bank_app_credential',%s,%s::jsonb
                   )""",
                (
                    prev_hash,
                    curr_hash,
                    owner,
                    f"sika_credential:{credential_id}",
                    credential_id,
                    canonical,
                ),
            )
            connection.commit()
    except ValueError:
        raise
    except Exception as exc:
        raise SikaCredentialStoreUnavailable("credential_write_failed") from exc

    reread = status(owner)
    if not reread.get("credential_present"):
        raise SikaCredentialStoreUnavailable("credential_write_readback_mismatch")
    return {
        "created": True,
        "owner_id": owner,
        "record_id": record_id,
        "audit_recorded": True,
        "password_hash_returned": False,
        "founder_auth_touched": False,
    }


def verify_authenticated_owner(owner_id: object, password: object) -> dict[str, object]:
    owner = _owner(owner_id)
    secret = str(password or "")
    try:
        with postgres_db.connect(readonly=True) as connection:
            rows = _active_rows(connection, owner)
    except Exception as exc:
        raise SikaCredentialStoreUnavailable("credential_read_failed") from exc
    if not rows:
        return {
            "verified": False,
            "reason": "bank_app_credential_not_created",
            "owner_id": owner,
            "founder_auth_touched": False,
        }
    try:
        item = json.loads(str(rows[0][1]))
    except ValueError as exc:
        raise SikaCredentialStoreUnavailable("credential_unreadable") from exc
    password_hash = str(item.get("password_hash") or "")
    verified = bool(password_hash and check_password_hash(password_hash, secret))
    return {
        "verified": verified,
        "owner_id": owner,
        "password_hash_returned": False,
        "founder_auth_touched": False,
    }


def recover_authenticated_owner(owner_id: object) -> dict[str, object]:
    owner = _owner(owner_id)
    try:
        with postgres_db.connect() as connection:
            connection.execute("SELECT pg_advisory_xact_lock(%s)", (25082512,))
            rows = _active_rows(connection, owner)
            if not rows:
                return {
                    "recovered": False,
                    "reason": "bank_app_credential_not_found",
                    "owner_id": owner,
                    "founder_auth_touched": False,
                }
            record_id = str(rows[0][0])
            connection.execute(
                """UPDATE oap_workspace_records
                   SET status='archived', updated_at=CURRENT_TIMESTAMP
                   WHERE record_id=%s AND identity_id=%s
                     AND workspace_id='sika' AND status='active'""",
                (record_id, owner),
            )
            connection.execute("SELECT pg_advisory_xact_lock(%s)", (25082509,))
            prior = connection.execute(
                "SELECT curr_hash FROM audit_events ORDER BY event_seq DESC LIMIT 1"
            ).fetchone()
            prev_hash = str(prior[0]) if prior else "GENESIS"
            correlation_id = str(uuid4())
            metadata = {
                "workspace_id": "sika",
                "record_id": record_id,
                "owner_id": owner,
                "recovery": "archive_bank_app_credential",
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
                       'SIKA_BANK_CREDENTIAL_RECOVERY',%s,
                       'authenticated_owner_scoped_credential_recovery',%s,%s::jsonb
                   )""",
                (
                    prev_hash,
                    curr_hash,
                    owner,
                    f"sika_credential:{record_id}",
                    correlation_id,
                    canonical,
                ),
            )
            connection.commit()
    except Exception as exc:
        raise SikaCredentialStoreUnavailable("credential_recovery_failed") from exc
    return {
        "recovered": True,
        "owner_id": owner,
        "record_id": record_id,
        "archived": True,
        "audit_recorded": True,
        "founder_auth_touched": False,
    }


def readiness() -> dict[str, object]:
    return {
        "canonical_store_reused": True,
        "workspace_id": "sika",
        "hash_algorithm": "scrypt",
        "plaintext_password_stored": False,
        "password_hash_returned": False,
        "durable_create_function_present": True,
        "durable_verify_function_present": True,
        "durable_recovery_function_present": True,
        "standalone_public_write_enabled": False,
        "authenticated_host_required": True,
        "founder_auth_touched": False,
        "production_ready": False,
        "reason": "authenticated_owner_host_route_required",
    }
