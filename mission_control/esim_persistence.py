"""Persistence boundary for governed eSIM lifecycle records.

No migration or write occurs at import time. Callers must explicitly initialize schema
through an approved database workflow before attaching this repository to the runtime.
"""
from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

SCHEMA_VERSION = "0001_esim_provisioning"
SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_esim_requests (
        request_id TEXT PRIMARY KEY,
        subject_id TEXT NOT NULL,
        purpose TEXT NOT NULL,
        state TEXT NOT NULL CHECK (
            state IN ('requested','approved','provisioning','active','suspended','revoked','failed')
        ),
        approved_by TEXT,
        provider_name TEXT,
        provider_profile_id TEXT,
        last_error TEXT,
        created_at TIMESTAMPTZ NOT NULL,
        updated_at TIMESTAMPTZ NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS oap_esim_events (
        event_seq BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        request_id TEXT NOT NULL REFERENCES oap_esim_requests(request_id) ON DELETE CASCADE,
        event TEXT NOT NULL,
        state TEXT NOT NULL,
        actor TEXT,
        provider TEXT,
        recorded_at TIMESTAMPTZ NOT NULL,
        metadata JSONB NOT NULL DEFAULT '{}'::jsonb
    )""",
    """CREATE INDEX IF NOT EXISTS ix_oap_esim_events_request
        ON oap_esim_events(request_id, event_seq)""",
)


class EsimRepository:
    """Small repository using an injected database connection factory."""

    def __init__(self, connect: Callable[[], Any]) -> None:
        self._connect = connect

    def save_request(self, item: dict[str, Any]) -> None:
        required = {"request_id", "subject_id", "purpose", "state", "created_at", "updated_at"}
        if not required.issubset(item):
            raise ValueError("invalid_esim_record")
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO oap_esim_requests (
                    request_id, subject_id, purpose, state, approved_by, provider_name,
                    provider_profile_id, last_error, created_at, updated_at
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (request_id) DO UPDATE SET
                    subject_id=EXCLUDED.subject_id,
                    purpose=EXCLUDED.purpose,
                    state=EXCLUDED.state,
                    approved_by=EXCLUDED.approved_by,
                    provider_name=EXCLUDED.provider_name,
                    provider_profile_id=EXCLUDED.provider_profile_id,
                    last_error=EXCLUDED.last_error,
                    updated_at=EXCLUDED.updated_at""",
                (
                    item["request_id"],
                    item["subject_id"],
                    item["purpose"],
                    item["state"],
                    item.get("approved_by"),
                    item.get("provider_name"),
                    item.get("provider_profile_id"),
                    item.get("last_error"),
                    item["created_at"],
                    item["updated_at"],
                ),
            )
            connection.commit()

    def append_event(self, event: dict[str, Any]) -> None:
        if not event.get("request_id") or not event.get("event") or not event.get("state"):
            raise ValueError("invalid_esim_event")
        metadata = {
            key: value
            for key, value in event.items()
            if key not in {"request_id", "event", "state", "actor", "provider", "recorded_at"}
        }
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO oap_esim_events
                    (request_id,event,state,actor,provider,recorded_at,metadata)
                    VALUES (%s,%s,%s,%s,%s,%s,%s::jsonb)""",
                (
                    event["request_id"],
                    event["event"],
                    event["state"],
                    event.get("actor"),
                    event.get("provider"),
                    event["recorded_at"],
                    json.dumps(metadata, separators=(",", ":"), sort_keys=True),
                ),
            )
            connection.commit()

    def get_request(self, request_id: str) -> dict[str, Any] | None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """SELECT request_id,subject_id,purpose,state,approved_by,provider_name,
                          provider_profile_id,last_error,created_at,updated_at
                   FROM oap_esim_requests WHERE request_id=%s""",
                (request_id,),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        keys = (
            "request_id",
            "subject_id",
            "purpose",
            "state",
            "approved_by",
            "provider_name",
            "provider_profile_id",
            "last_error",
            "created_at",
            "updated_at",
        )
        return dict(zip(keys, row, strict=True))

    def list_events(self, request_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """SELECT event,state,actor,provider,recorded_at,metadata
                   FROM oap_esim_events WHERE request_id=%s ORDER BY event_seq""",
                (request_id,),
            )
            rows = cursor.fetchall()
        return [
            {
                "request_id": request_id,
                "event": row[0],
                "state": row[1],
                "actor": row[2],
                "provider": row[3],
                "recorded_at": row[4],
                **(row[5] or {}),
            }
            for row in rows
        ]


def schema_status(connect: Callable[[], Any]) -> dict[str, Any]:
    """Return redacted eSIM schema readiness without mutating the database."""
    required = {"oap_esim_requests", "oap_esim_events"}
    try:
        with connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT table_name FROM information_schema.tables
                   WHERE table_schema = 'public'
                     AND table_name IN ('oap_esim_requests','oap_esim_events')"""
            ).fetchall()
        tables = {str(row[0]) for row in rows}
        return {
            "schema_version": SCHEMA_VERSION,
            "schema_ready": required <= tables,
            "missing_tables": sorted(required - tables),
            "error": None,
        }
    except Exception:  # noqa: BLE001 - redact database details.
        return {
            "schema_version": SCHEMA_VERSION,
            "schema_ready": False,
            "missing_tables": sorted(required),
            "error": "database_unavailable",
        }


def init_schema(
    connect: Callable[..., Any],
    *,
    dry_run: bool = False,
    assume_yes: bool = False,
) -> dict[str, Any]:
    """Apply only the eSIM schema after explicit human-authorized invocation."""
    if not assume_yes:
        raise RuntimeError("Explicit human approval required: pass --yes")
    if dry_run:
        return {
            **schema_status(connect),
            "dry_run": True,
            "would_apply": list(SCHEMA_STATEMENTS),
        }

    with connect() as connection:
        try:
            connection.execute("SELECT pg_advisory_xact_lock(%s)", (24680259,))
            for statement in SCHEMA_STATEMENTS:
                connection.execute(statement)
            connection.commit()
        except Exception:
            connection.rollback()
            raise

    status = schema_status(connect)
    if not status["schema_ready"]:
        raise RuntimeError("eSIM migration completed without a ready schema")
    return status
