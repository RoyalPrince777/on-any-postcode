"""Protected Link Up block/report safety store.

Schema changes are explicit only; importing this module never mutates production.
"""
from __future__ import annotations

import uuid
from typing import Any

from . import postgres_db

SCHEMA_VERSION = "linkup_safety_v1"
SCHEMA_SQL = (
    """CREATE TABLE IF NOT EXISTS linkup_blocks (
        blocker_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        blocked_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (blocker_id, blocked_id),
        CHECK (blocker_id <> blocked_id))""",
    """CREATE TABLE IF NOT EXISTS linkup_reports (
        report_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        reporter_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        reported_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        message_id UUID REFERENCES messages(id) ON DELETE SET NULL,
        reason TEXT NOT NULL,
        detail TEXT NOT NULL DEFAULT '',
        status TEXT NOT NULL DEFAULT 'open'
            CHECK (status IN ('open','reviewing','closed')),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CHECK (reporter_id <> reported_id))""",
    "CREATE INDEX IF NOT EXISTS idx_linkup_reports_status_created ON linkup_reports(status, created_at DESC)",
    """CREATE OR REPLACE FUNCTION oap_linkup_block_guard() RETURNS trigger AS $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM linkup_blocks
                WHERE (blocker_id=NEW.sender_id AND blocked_id=NEW.recipient_id)
                   OR (blocker_id=NEW.recipient_id AND blocked_id=NEW.sender_id)
            ) THEN
                RAISE EXCEPTION 'linkup_blocked_pair';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql""",
    "DROP TRIGGER IF EXISTS trg_linkup_block_guard ON messages",
    """CREATE TRIGGER trg_linkup_block_guard
        BEFORE INSERT ON messages
        FOR EACH ROW EXECUTE FUNCTION oap_linkup_block_guard()""",
)


class LinkUpSafetyUnavailable(RuntimeError):
    pass


def _uuid(value: object, code: str) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(code) from exc


def init_schema(*, assume_yes: bool = False, dry_run: bool = False) -> dict[str, Any]:
    if not assume_yes and not dry_run:
        raise PermissionError("explicit_confirmation_required")
    if dry_run:
        return {"version": SCHEMA_VERSION, "statements": list(SCHEMA_SQL), "applied": False}
    try:
        with postgres_db.connect() as connection:
            for statement in SCHEMA_SQL:
                connection.execute(statement)
            connection.commit()
    except Exception as exc:
        raise LinkUpSafetyUnavailable("linkup_safety_schema_failed") from exc
    return {"version": SCHEMA_VERSION, "applied": True}


def status() -> dict[str, Any]:
    result = {"configured": postgres_db.configured(), "ready": False, "tables": []}
    if not result["configured"]:
        return result
    try:
        with postgres_db.connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT table_name FROM information_schema.tables
                   WHERE table_schema='public' AND table_name IN ('linkup_blocks','linkup_reports')"""
            ).fetchall()
        result["tables"] = sorted(str(row[0]) for row in rows)
        result["ready"] = result["tables"] == ["linkup_blocks", "linkup_reports"]
    except Exception:
        return result
    return result


def block(blocker_id: object, blocked_id: object) -> None:
    blocker = _uuid(blocker_id, "invalid_blocker")
    blocked = _uuid(blocked_id, "invalid_blocked")
    if blocker == blocked:
        raise ValueError("cannot_block_self")
    try:
        with postgres_db.connect() as connection:
            active = connection.execute(
                "SELECT id FROM users WHERE id=%s AND status='active'", (blocked,)
            ).fetchone()
            if active is None:
                raise ValueError("member_unavailable")
            connection.execute(
                """INSERT INTO linkup_blocks(blocker_id,blocked_id) VALUES (%s,%s)
                   ON CONFLICT (blocker_id,blocked_id) DO NOTHING""",
                (blocker, blocked),
            )
            connection.commit()
    except ValueError:
        raise
    except Exception as exc:
        raise LinkUpSafetyUnavailable("linkup_block_failed") from exc


def unblock(blocker_id: object, blocked_id: object) -> bool:
    blocker = _uuid(blocker_id, "invalid_blocker")
    blocked = _uuid(blocked_id, "invalid_blocked")
    try:
        with postgres_db.connect() as connection:
            row = connection.execute(
                "DELETE FROM linkup_blocks WHERE blocker_id=%s AND blocked_id=%s RETURNING blocked_id",
                (blocker, blocked),
            ).fetchone()
            connection.commit()
    except Exception as exc:
        raise LinkUpSafetyUnavailable("linkup_unblock_failed") from exc
    return row is not None


def blocked_between(first_id: object, second_id: object) -> bool:
    first = _uuid(first_id, "invalid_identity")
    second = _uuid(second_id, "invalid_identity")
    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT 1 FROM linkup_blocks
                   WHERE (blocker_id=%s AND blocked_id=%s)
                      OR (blocker_id=%s AND blocked_id=%s) LIMIT 1""",
                (first, second, second, first),
            ).fetchone()
    except Exception as exc:
        raise LinkUpSafetyUnavailable("linkup_block_check_failed") from exc
    return row is not None


def report(reporter_id: object, reported_id: object, *, message_id: object = None, reason: object, detail: object = "") -> str:
    reporter = _uuid(reporter_id, "invalid_reporter")
    reported = _uuid(reported_id, "invalid_reported")
    if reporter == reported:
        raise ValueError("cannot_report_self")
    reason_value = " ".join(str(reason or "").split())[:120]
    detail_value = str(detail or "").strip()[:2000]
    if not reason_value:
        raise ValueError("report_reason_required")
    message = None if not message_id else _uuid(message_id, "invalid_message")
    try:
        with postgres_db.connect() as connection:
            if message:
                owned = connection.execute(
                    """SELECT 1 FROM messages WHERE id=%s AND
                       ((sender_id=%s AND recipient_id=%s) OR (sender_id=%s AND recipient_id=%s))""",
                    (message, reporter, reported, reported, reporter),
                ).fetchone()
                if owned is None:
                    raise ValueError("message_not_reportable")
            row = connection.execute(
                """INSERT INTO linkup_reports(reporter_id,reported_id,message_id,reason,detail)
                   VALUES (%s,%s,%s,%s,%s) RETURNING report_id""",
                (reporter, reported, message, reason_value, detail_value),
            ).fetchone()
            connection.commit()
    except ValueError:
        raise
    except Exception as exc:
        raise LinkUpSafetyUnavailable("linkup_report_failed") from exc
    return str(row[0])
