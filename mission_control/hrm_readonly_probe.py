"""Read-only, secret-safe probe for the independent HRM PostgreSQL candidate.

This module never creates tables, writes receipts, migrates schema or exposes a
connection string. It exists only to prove whether an already-configured HRM
PostgreSQL alias is present and reachable before any Human-Authority-approved
promotion or migration is considered.
"""
from __future__ import annotations

import base64
import binascii
import os
from typing import Any

_DIRECT_ALIASES = (
    ("OAP_HRM_DATABASE_URL", "oap_hrm_database_url"),
    ("OAP_SMI_HRM_DATABASE_URL", "oap_smi_hrm_database_url"),
)
_ENCODED_ALIASES = (
    ("OAP_HRM_DATABASE_URL_B64", "oap_hrm_database_url_b64"),
    ("OAP_SMI_HRM_DATABASE_URL_B64", "oap_smi_hrm_database_url_b64"),
)


def _decode(value: str) -> str:
    try:
        return base64.b64decode(value, validate=True).decode("utf-8").strip()
    except (binascii.Error, ValueError, UnicodeDecodeError):
        return ""


def _database_config() -> tuple[str, str]:
    for env_name, source in _DIRECT_ALIASES:
        value = os.environ.get(env_name, "").strip()
        if value:
            return value, source
    for env_name, source in _ENCODED_ALIASES:
        encoded = os.environ.get(env_name, "").strip()
        if encoded:
            return _decode(encoded), source
    return "", "unconfigured"


def _ssl_url(value: str) -> str:
    clean = str(value or "").strip()
    if not clean or "sslmode=" in clean:
        return clean
    if clean.startswith(("postgres://", "postgresql://")):
        return clean + ("&sslmode=require" if "?" in clean else "?sslmode=require")
    return clean


def status() -> dict[str, Any]:
    """Run one bounded SELECT 1 and return only coarse readiness evidence."""

    database_url, source = _database_config()
    result: dict[str, Any] = {
        "backend": "independent_hrm_postgres_candidate",
        "source": source,
        "configured": bool(database_url),
        "reachable": False,
        "read_only": True,
        "write_performed": False,
        "schema_changed": False,
        "secret_exposed": False,
        "error": None,
    }
    if not database_url:
        result["error"] = "hrm_database_url_not_configured"
        return result

    try:
        import psycopg

        with psycopg.connect(
            _ssl_url(database_url),
            connect_timeout=5,
            application_name="oap-hrm-readonly-proof",
            autocommit=False,
        ) as connection:
            connection.execute("SET TRANSACTION READ ONLY")
            connection.execute("SELECT 1").fetchone()
            connection.rollback()
        result["reachable"] = True
        return result
    except Exception:  # noqa: BLE001 - proof must degrade without secret/error leakage.
        result["error"] = "hrm_database_unavailable"
        return result
