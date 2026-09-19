"""Explicit Link message sync/idempotency schema.

Adds a client_message_id to messages so transient retries can safely return the
same persisted Link instead of creating duplicates. Activation is explicit and
multi-worker safe.
"""
from __future__ import annotations

from typing import Any

from . import postgres_db

SCHEMA_VERSION = "link_message_sync_v1"
SCHEMA_SQL = (
    "ALTER TABLE messages ADD COLUMN IF NOT EXISTS client_message_id UUID",
    """CREATE UNIQUE INDEX IF NOT EXISTS uq_messages_sender_client
       ON messages(sender_id, client_message_id)
       WHERE client_message_id IS NOT NULL""",
    """CREATE INDEX IF NOT EXISTS idx_messages_pair_created_id
       ON messages(
         LEAST(sender_id, recipient_id),
         GREATEST(sender_id, recipient_id),
         created_at,
         id
       )""",
)

class LinkMessageSyncUnavailable(RuntimeError):
    pass

def init_schema(*, assume_yes: bool = False, dry_run: bool = False) -> dict[str, Any]:
    if not assume_yes and not dry_run:
        raise PermissionError("explicit_confirmation_required")
    if dry_run:
        return {"version": SCHEMA_VERSION, "statements": list(SCHEMA_SQL), "applied": False}
    try:
        with postgres_db.connect() as connection:
            connection.execute(
                "SELECT pg_advisory_xact_lock(hashtext('oap_link_message_sync_v1'))"
            )
            for statement in SCHEMA_SQL:
                connection.execute(statement)
            connection.commit()
    except Exception as exc:
        raise LinkMessageSyncUnavailable("link_message_sync_schema_failed") from exc
    return {"version": SCHEMA_VERSION, "applied": True}

def status() -> dict[str, Any]:
    result = {
        "configured": postgres_db.configured(),
        "ready": False,
        "idempotent_send": False,
        "stable_cursor": False,
    }
    if not result["configured"]:
        return result
    try:
        with postgres_db.connect(readonly=True) as connection:
            column = connection.execute(
                """SELECT 1 FROM information_schema.columns
                   WHERE table_schema='public' AND table_name='messages'
                     AND column_name='client_message_id'"""
            ).fetchone()
            indexes = connection.execute(
                """SELECT indexname FROM pg_indexes
                   WHERE schemaname='public' AND tablename='messages'
                     AND indexname IN (
                       'uq_messages_sender_client',
                       'idx_messages_pair_created_id'
                     )"""
            ).fetchall()
        names = {str(row[0]) for row in indexes}
        result["idempotent_send"] = bool(
            column is not None and "uq_messages_sender_client" in names
        )
        result["stable_cursor"] = "idx_messages_pair_created_id" in names
        result["ready"] = bool(
            result["idempotent_send"] and result["stable_cursor"]
        )
    except Exception:  # noqa: BLE001 - readiness probe must fail closed.
        return result
    return result
