"""SIKA bank-app security for the isolated acceptance shell.

This is deliberately separate from Founder authentication. Passwords are hashed
with Werkzeug's scrypt implementation and are never returned. State is
process-local in the isolated acceptance service, so this is real software
behaviour but not a production credential store.
"""
from __future__ import annotations

from dataclasses import dataclass
from time import monotonic
from typing import Any

from werkzeug.security import check_password_hash, generate_password_hash

MIN_PASSWORD_LENGTH = 12
MAX_PASSWORD_LENGTH = 128
MAX_FAILURES = 5
LOCK_SECONDS = 300


@dataclass
class _Credential:
    password_hash: str
    failures: int = 0
    locked_until: float = 0.0
    unlocked: bool = False


_CREDENTIALS: dict[str, _Credential] = {}


def _key(device_id: object) -> str:
    value = str(device_id or "").strip()
    if not value or len(value) > 120:
        raise ValueError("valid_device_id_required")
    return value


def _password(value: object) -> str:
    password = str(value or "")
    if len(password) < MIN_PASSWORD_LENGTH or len(password) > MAX_PASSWORD_LENGTH:
        raise ValueError("bank_app_password_must_be_12_to_128_characters")
    if not password.strip():
        raise ValueError("bank_app_password_required")
    return password


def create_password(device_id: object, password: object) -> dict[str, Any]:
    key = _key(device_id)
    secret = _password(password)
    if key in _CREDENTIALS:
        return {
            "created": False,
            "reason": "bank_app_password_already_exists",
            "founder_auth_touched": False,
            "production_ready": False,
        }
    _CREDENTIALS[key] = _Credential(
        password_hash=generate_password_hash(secret, method="scrypt")
    )
    return {
        "created": True,
        "device_id": key,
        "password_hash_returned": False,
        "storage": "process_local_acceptance_only",
        "founder_auth_touched": False,
        "production_ready": False,
    }


def unlock(device_id: object, password: object) -> dict[str, Any]:
    key = _key(device_id)
    secret = str(password or "")
    record = _CREDENTIALS.get(key)
    if record is None:
        return {
            "unlocked": False,
            "reason": "bank_app_password_not_created",
            "founder_auth_touched": False,
        }

    now = monotonic()
    if record.locked_until > now:
        return {
            "unlocked": False,
            "reason": "temporarily_locked_after_failed_attempts",
            "retry_after_seconds": max(1, int(record.locked_until - now)),
            "founder_auth_touched": False,
        }

    if not check_password_hash(record.password_hash, secret):
        record.failures += 1
        record.unlocked = False
        if record.failures >= MAX_FAILURES:
            record.locked_until = now + LOCK_SECONDS
            record.failures = 0
        return {
            "unlocked": False,
            "reason": "bank_app_password_not_recognised",
            "founder_auth_touched": False,
        }

    record.failures = 0
    record.locked_until = 0.0
    record.unlocked = True
    return {
        "unlocked": True,
        "device_id": key,
        "founder_auth_touched": False,
        "production_ready": False,
    }


def lock(device_id: object) -> dict[str, Any]:
    key = _key(device_id)
    record = _CREDENTIALS.get(key)
    if record is not None:
        record.unlocked = False
    return {
        "locked": True,
        "device_id": key,
        "founder_auth_touched": False,
    }


def status(device_id: object) -> dict[str, Any]:
    key = _key(device_id)
    record = _CREDENTIALS.get(key)
    return {
        "device_id": key,
        "password_created": record is not None,
        "unlocked": bool(record and record.unlocked),
        "password_hash_returned": False,
        "storage": "process_local_acceptance_only",
        "rate_limit_failures": MAX_FAILURES,
        "lock_seconds": LOCK_SECONDS,
        "founder_auth_touched": False,
        "owner_identity_bound": False,
        "durable_credential_store": False,
        "production_ready": False,
    }
