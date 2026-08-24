"""Explicit PostgreSQL foundation for OAP production.

No connection or migration runs at import time. Readiness probes are read-only.
Schema changes require the explicit Flask oap-init-postgres --yes command.
"""

from __future__ import annotations

import base64
import hashlib
import os
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

REQUIRED_TABLES = frozenset({
    "oap_schema_migrations", "oap_identities", "oap_roles",
    "oap_identity_roles", "oap_permissions", "oap_role_permissions",
    "oap_guardian_reviews", "audit_events", "smi_memory_records",
    "smi_approval_receipts", "smi_conversations", "smi_messages",
    "smi_provider_assignments",
})
MIGRATION_VERSION = "0002_smi_chat_production"
MIGRATION_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_schema_migrations (
        version TEXT PRIMARY KEY, checksum TEXT NOT NULL,
        applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE TABLE IF NOT EXISTS oap_identities (
        identity_id UUID PRIMARY KEY, display_name TEXT NOT NULL,
        identity_type TEXT NOT NULL,
        status TEXT NOT NULL CHECK (status IN ('ACTIVE','SUSPENDED','REVOKED')),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE TABLE IF NOT EXISTS oap_roles (
        role_id TEXT PRIMARY KEY, name TEXT NOT NULL UNIQUE,
        authority_level INTEGER NOT NULL CHECK (authority_level BETWEEN 0 AND 5))""",
    """CREATE TABLE IF NOT EXISTS oap_identity_roles (
        identity_id UUID NOT NULL REFERENCES oap_identities(identity_id),
        role_id TEXT NOT NULL REFERENCES oap_roles(role_id),
        granted_by UUID REFERENCES oap_identities(identity_id),
        granted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (identity_id, role_id))""",
    """CREATE TABLE IF NOT EXISTS oap_permissions (
        permission_id TEXT PRIMARY KEY, description TEXT NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS oap_role_permissions (
        role_id TEXT NOT NULL REFERENCES oap_roles(role_id),
        permission_id TEXT NOT NULL REFERENCES oap_permissions(permission_id),
        PRIMARY KEY (role_id, permission_id))""",
    """CREATE TABLE IF NOT EXISTS oap_guardian_reviews (
        review_id UUID PRIMARY KEY, request_id UUID NOT NULL,
        identity_id UUID NOT NULL,
        outcome TEXT NOT NULL CHECK (outcome IN ('PASSED','REVIEW_REQUIRED','BLOCKED')),
        reason TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE TABLE IF NOT EXISTS audit_events (
        event_seq BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        event_id UUID NOT NULL UNIQUE, prev_hash TEXT NOT NULL,
        curr_hash TEXT NOT NULL UNIQUE, actor_id TEXT NOT NULL,
        actor_type TEXT NOT NULL, authority_level INTEGER,
        action TEXT NOT NULL, target TEXT NOT NULL, reason TEXT NOT NULL,
        correlation_id UUID NOT NULL, metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
        timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    "CREATE INDEX IF NOT EXISTS ix_audit_timestamp ON audit_events(timestamp)",
    "CREATE INDEX IF NOT EXISTS ix_audit_correlation ON audit_events(correlation_id)",
    """CREATE TABLE IF NOT EXISTS smi_memory_records (
        memory_id UUID PRIMARY KEY, request_id UUID NOT NULL UNIQUE,
        identity_id UUID NOT NULL, task_type TEXT NOT NULL,
        content_hash TEXT NOT NULL, summary TEXT NOT NULL,
        output_state TEXT NOT NULL CHECK (output_state IN
            ('RECOMMENDATION_READY','REVIEW_REQUIRED','BLOCK_REQUEST','SYSTEM_LOG_ONLY')),
        signal_level TEXT NOT NULL, rationale_json JSONB NOT NULL,
        processing_states_json JSONB NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE TABLE IF NOT EXISTS smi_approval_receipts (
        receipt_id UUID PRIMARY KEY,
        request_id UUID NOT NULL UNIQUE REFERENCES smi_memory_records(request_id),
        identity_id UUID NOT NULL,
        decision TEXT NOT NULL CHECK (decision IN ('APPROVED','REJECTED')),
        issued_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMPTZ NOT NULL, action_digest TEXT NOT NULL,
        consumed_at TIMESTAMPTZ)""",
)
MIGRATION_CHECKSUM = "9a5b1d7c4e2f8a60b3c91d5e7f20486aa6c8e1b35d79f024ce6a8b4d1f73e590"


def _database_url() -> str:
    encoded = os.environ.get("OAP_NEON_DATABASE_URL_B64", "").strip()
    if encoded:
        try:
            return base64.b64decode(encoded).decode("utf-8").strip()
        except (ValueError, UnicodeDecodeError):
            return ""
    return (os.environ.get("OAP_NEON_DATABASE_URL") or os.environ.get("DATABASE_URL", "")).strip()


def configured() -> bool:
    return bool(_database_url())


def _driver():
    try:
        import psycopg
    except ImportError as exc:
        raise RuntimeError("psycopg is required when DATABASE_URL is configured") from exc
    return psycopg


@contextmanager
def connect(*, readonly: bool = False) -> Iterator[Any]:
    """Open a bounded production connection without exposing its URL."""
    database_url = _database_url()
    if not database_url:
        raise RuntimeError("Neon database URL is not configured")
    psycopg = _driver()
    with psycopg.connect(
        database_url, connect_timeout=5,
        application_name="oap-mission-control", autocommit=False,
    ) as connection:
        if readonly:
            connection.execute("SET TRANSACTION READ ONLY")
        yield connection


def postgres_status() -> dict[str, Any]:
    """Return a redacted, read-only readiness result."""
    result: dict[str, Any] = {
        "backend": "postgresql", "configured": configured(),
        "reachable": False, "initialized": False,
        "pending": [MIGRATION_VERSION], "checksum_mismatches": [], "error": None,
    }
    if not result["configured"]:
        result["error"] = "database_url_not_configured"
        return result
    try:
        with connect(readonly=True) as connection:
            connection.execute("SELECT 1").fetchone()
            result["reachable"] = True
            rows = connection.execute(
                """SELECT table_name FROM information_schema.tables
                   WHERE table_schema = 'public'"""
            ).fetchall()
            tables = {str(row[0]) for row in rows}
            if "oap_schema_migrations" not in tables:
                return result
            applied = connection.execute(
                "SELECT version, checksum FROM oap_schema_migrations"
            ).fetchall()
            versions = {str(row[0]): str(row[1]) for row in applied}
            if versions.get(MIGRATION_VERSION) not in {None, MIGRATION_CHECKSUM}:
                result["checksum_mismatches"] = [MIGRATION_VERSION]
                result["error"] = "migration_checksum_mismatch"
                return result
            if MIGRATION_VERSION in versions:
                result["pending"] = []
            result["initialized"] = (
                not result["pending"] and not result["checksum_mismatches"]
                and REQUIRED_TABLES <= tables
            )
            return result
    except (_driver().Error, RuntimeError, OSError):
        result["error"] = "database_unavailable"
        return result


def init_postgres(*, dry_run: bool = False, assume_yes: bool = False) -> dict[str, Any]:
    """Apply the schema only after explicit human-authorized invocation."""
    if not configured():
        raise RuntimeError("DATABASE_URL is not configured")
    if not assume_yes:
        raise RuntimeError("Explicit human approval required: pass --yes")
    if dry_run:
        status = postgres_status()
        return {**status, "dry_run": True, "would_apply": status["pending"]}

    with connect() as connection:
        try:
            connection.execute("SELECT pg_advisory_xact_lock(%s)", (24680258,))
            connection.execute(MIGRATION_STATEMENTS[0])
            row = connection.execute(
                "SELECT checksum FROM oap_schema_migrations WHERE version = %s",
                (MIGRATION_VERSION,),
            ).fetchone()
            if row is not None:
                if str(row[0]) != MIGRATION_CHECKSUM:
                    raise RuntimeError("Applied PostgreSQL migration checksum mismatch")
            else:
                for statement in MIGRATION_STATEMENTS[1:]:
                    connection.execute(statement)
                connection.execute(
                    """INSERT INTO oap_schema_migrations(version, checksum)
                       VALUES (%s, %s)""",
                    (MIGRATION_VERSION, MIGRATION_CHECKSUM),
                )
            connection.commit()
        except Exception:
            connection.rollback()
            raise

    status = postgres_status()
    if not status["initialized"]:
        raise RuntimeError("PostgreSQL migration completed without a ready schema")
    return status
