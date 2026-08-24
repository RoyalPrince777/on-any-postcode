"""Explicit PostgreSQL foundation for OAP production.

No connection or migration runs at import time. Readiness probes are read-only.
Schema changes require the explicit Flask oap-init-postgres --yes command.
"""

from __future__ import annotations

import base64
import os
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

REQUIRED_TABLES = frozenset({
    "oap_schema_migrations", "oap_identities", "oap_roles",
    "oap_identity_roles", "oap_permissions", "oap_role_permissions",
    "oap_guardian_reviews", "audit_events", "smi_memory_records",
    "smi_approval_receipts", "smi_conversations", "smi_messages",
    "smi_provider_assignments", "smi_judgement_reviews",
    "oap_workspace_records", "users", "posts", "messages", "products",
    "wallets", "transactions",
})
MIGRATION_VERSION = "0003_product_governance"
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
        review_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        request_id UUID NOT NULL,
        identity_id UUID NOT NULL
            CONSTRAINT oap_guardian_reviews_identity_id_fkey
            REFERENCES oap_identities(identity_id),
        outcome TEXT NOT NULL CHECK (outcome IN ('PASSED','REVIEW_REQUIRED','BLOCKED')),
        reason TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE TABLE IF NOT EXISTS audit_events (
        event_seq BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        event_id UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
        prev_hash TEXT NOT NULL,
        curr_hash TEXT NOT NULL UNIQUE, actor_id TEXT NOT NULL,
        actor_type TEXT NOT NULL, authority_level INTEGER,
        action TEXT NOT NULL, target TEXT NOT NULL, reason TEXT NOT NULL,
        correlation_id UUID NOT NULL, metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
        timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    "CREATE INDEX IF NOT EXISTS ix_audit_timestamp ON audit_events(timestamp)",
    "CREATE INDEX IF NOT EXISTS ix_audit_correlation ON audit_events(correlation_id)",
    """CREATE TABLE IF NOT EXISTS smi_memory_records (
        memory_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        request_id UUID NOT NULL UNIQUE,
        identity_id UUID NOT NULL, task_type TEXT NOT NULL,
        content_hash TEXT NOT NULL, summary TEXT NOT NULL,
        output_state TEXT NOT NULL CHECK (output_state IN
            ('RECOMMENDATION_READY','REVIEW_REQUIRED','BLOCK_REQUEST','SYSTEM_LOG_ONLY')),
        signal_level TEXT NOT NULL, rationale_json JSONB NOT NULL,
        processing_states_json JSONB NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE TABLE IF NOT EXISTS smi_approval_receipts (
        receipt_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        request_id UUID NOT NULL UNIQUE REFERENCES smi_memory_records(request_id),
        identity_id UUID NOT NULL,
        decision TEXT NOT NULL CHECK (decision IN ('APPROVED','REJECTED')),
        issued_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMPTZ NOT NULL, action_digest TEXT NOT NULL,
        consumed_at TIMESTAMPTZ,
        authority_level SMALLINT NOT NULL,
        nonce TEXT NOT NULL, signature TEXT NOT NULL)""",
    "ALTER TABLE smi_approval_receipts ADD COLUMN IF NOT EXISTS authority_level SMALLINT",
    "ALTER TABLE smi_approval_receipts ADD COLUMN IF NOT EXISTS nonce TEXT",
    "ALTER TABLE smi_approval_receipts ADD COLUMN IF NOT EXISTS signature TEXT",
    "ALTER TABLE smi_approval_receipts ALTER COLUMN identity_id SET NOT NULL",
    "ALTER TABLE smi_approval_receipts ALTER COLUMN authority_level SET NOT NULL",
    "ALTER TABLE smi_approval_receipts ALTER COLUMN nonce SET NOT NULL",
    "ALTER TABLE smi_approval_receipts ALTER COLUMN signature SET NOT NULL",
    """ALTER TABLE smi_approval_receipts
        ADD CONSTRAINT smi_approval_receipts_identity_id_fkey
        FOREIGN KEY (identity_id) REFERENCES oap_identities(identity_id)""",
    """ALTER TABLE smi_approval_receipts
        ADD CONSTRAINT smi_approval_receipts_authority_level_check
        CHECK (authority_level = 0)""",
    """CREATE UNIQUE INDEX IF NOT EXISTS ix_smi_approval_nonce
        ON smi_approval_receipts(nonce) WHERE nonce IS NOT NULL""",
    """CREATE TABLE IF NOT EXISTS smi_judgement_reviews (
        request_id UUID PRIMARY KEY REFERENCES smi_memory_records(request_id)
            ON DELETE CASCADE,
        identity_id UUID NOT NULL REFERENCES oap_identities(identity_id),
        evidence_json JSONB NOT NULL DEFAULT '[]'::jsonb,
        provenance_quality TEXT NOT NULL
            CHECK (provenance_quality IN ('STRONG','ADEQUATE','LIMITED')),
        confidence DOUBLE PRECISION NOT NULL
            CHECK (confidence >= 0 AND confidence <= 1),
        uncertainty_json JSONB NOT NULL DEFAULT '[]'::jsonb,
        counter_case TEXT NOT NULL,
        consequences_json JSONB NOT NULL DEFAULT '[]'::jsonb,
        reversibility TEXT NOT NULL
            CHECK (reversibility IN ('REVERSIBLE','REVIEW_REQUIRED')),
        proportionality TEXT NOT NULL
            CHECK (proportionality IN ('PROPORTIONATE','REVIEW_REQUIRED')),
        constitution_consistent BOOLEAN NOT NULL,
        sections_completed SMALLINT NOT NULL DEFAULT 5
            CHECK (sections_completed BETWEEN 1 AND 5),
        human_decision TEXT CHECK (human_decision IN ('APPROVED','REJECTED')),
        human_identity_id UUID REFERENCES oap_identities(identity_id),
        human_decided_at TIMESTAMPTZ,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CHECK ((human_decision IS NULL AND human_identity_id IS NULL
                AND human_decided_at IS NULL) OR
               (human_decision IS NOT NULL AND human_identity_id IS NOT NULL
                AND human_decided_at IS NOT NULL)))""",
    """CREATE INDEX IF NOT EXISTS ix_smi_judgement_identity_created
        ON smi_judgement_reviews(identity_id, created_at DESC)""",
    """CREATE TABLE IF NOT EXISTS smi_conversations (
        conversation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        identity_id UUID, title TEXT NOT NULL DEFAULT 'SMI Chat',
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE TABLE IF NOT EXISTS smi_messages (
        message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        conversation_id UUID NOT NULL REFERENCES smi_conversations(conversation_id)
            ON DELETE CASCADE,
        request_id UUID NOT NULL,
        role TEXT NOT NULL CHECK (role IN ('user','assistant','system')),
        content TEXT NOT NULL, provider TEXT, model TEXT, guardian_outcome TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE INDEX IF NOT EXISTS ix_smi_messages_conversation
        ON smi_messages(conversation_id, created_at)""",
    """CREATE TABLE IF NOT EXISTS smi_provider_assignments (
        assignment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        agent_id TEXT NOT NULL, provider_id TEXT NOT NULL, model TEXT NOT NULL,
        status TEXT NOT NULL CHECK (status IN ('APPROVED','SUSPENDED','REVOKED')),
        approved_by TEXT NOT NULL,
        approved_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(agent_id,provider_id,model))""",
    """INSERT INTO oap_permissions(permission_id,description)
        VALUES ('REQUEST_RECOMMENDATION','Request a governed SMI recommendation')
        ON CONFLICT (permission_id) DO NOTHING""",
    """INSERT INTO oap_permissions(permission_id,description)
        VALUES ('APPROVE_RECOMMENDATION','Record a level-zero Human Authority decision')
        ON CONFLICT (permission_id) DO NOTHING""",
    """INSERT INTO smi_provider_assignments
        (agent_id,provider_id,model,status,approved_by)
        VALUES ('NEO-001','openai','gpt-5-mini','APPROVED','HUMAN_AUTHORITY')
        ON CONFLICT (agent_id,provider_id,model) DO NOTHING""",
    """CREATE TABLE IF NOT EXISTS users (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(), email TEXT UNIQUE,
        username TEXT NOT NULL UNIQUE, display_name TEXT, postcode TEXT,
        borough TEXT, county TEXT, country TEXT, continent TEXT,
        status TEXT NOT NULL DEFAULT 'active'
            CHECK (status IN ('active','suspended','deleted')),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE TABLE IF NOT EXISTS posts (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        body TEXT NOT NULL, scope TEXT NOT NULL DEFAULT 'postcode', postcode TEXT,
        status TEXT NOT NULL DEFAULT 'published',
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE INDEX IF NOT EXISTS idx_posts_scope_created
        ON posts(scope, created_at DESC)""",
    """CREATE TABLE IF NOT EXISTS messages (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        sender_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        recipient_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        body TEXT NOT NULL, read_at TIMESTAMPTZ,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CHECK (sender_id <> recipient_id))""",
    """CREATE INDEX IF NOT EXISTS idx_messages_recipient_created
        ON messages(recipient_id, created_at DESC)""",
    """CREATE INDEX IF NOT EXISTS idx_messages_sender_created
        ON messages(sender_id, created_at DESC)""",
    """CREATE TABLE IF NOT EXISTS products (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        seller_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        name TEXT NOT NULL, description TEXT,
        price_minor BIGINT NOT NULL CHECK (price_minor >= 0),
        currency TEXT NOT NULL DEFAULT 'GBP', active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE INDEX IF NOT EXISTS idx_products_active_created
        ON products(active, created_at DESC)""",
    """CREATE TABLE IF NOT EXISTS wallets (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
        balance BIGINT NOT NULL DEFAULT 0 CHECK (balance >= 0),
        currency_code TEXT NOT NULL DEFAULT 'SIKA',
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE TABLE IF NOT EXISTS transactions (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        wallet_id UUID NOT NULL REFERENCES wallets(id) ON DELETE RESTRICT,
        amount BIGINT NOT NULL CHECK (amount <> 0),
        transaction_type TEXT NOT NULL, reference TEXT NOT NULL UNIQUE,
        metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE INDEX IF NOT EXISTS idx_transactions_wallet_created
        ON transactions(wallet_id, created_at DESC)""",
    """CREATE TABLE IF NOT EXISTS oap_workspace_records (
        record_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        identity_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        workspace_id TEXT NOT NULL CHECK (workspace_id IN
            ('ecosystem','signals','hrm-memory','governance','performance','news',
             'transport','market','maps','identity','tv','sika')),
        title TEXT NOT NULL, body TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'active'
            CHECK (status IN ('draft','active','archived')),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE INDEX IF NOT EXISTS ix_workspace_identity_dashboard_updated
        ON oap_workspace_records(identity_id, workspace_id, updated_at DESC)""",
)
MIGRATION_CHECKSUM = "4fddba35b7e57fc5c4c36700cb10e000a1b56e4cec794b9e26424d34d73f1749"


def render_migration_sql() -> str:
    """Render the exact idempotent SQL used by branch-first migration tooling."""

    statements = [*MIGRATION_STATEMENTS]
    statements.append(
        "INSERT INTO oap_schema_migrations(version,checksum) "
        f"VALUES ('{MIGRATION_VERSION}','{MIGRATION_CHECKSUM}') "
        "ON CONFLICT (version) DO NOTHING"
    )
    return ";\n\n".join(statements) + ";\n"


def _database_url() -> str:
    encoded = (os.environ.get("OAP_DB_SECRET_B64") or os.environ.get("OAP_NEON_DATABASE_URL_B64", "")).strip()
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
