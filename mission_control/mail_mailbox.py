"""Owner-scoped read-only OAP Mail mailbox projection.

This module reuses the existing oap_mail_items store. It never accepts inbound
SMTP, claims delivery, mutates mailbox rows or creates a second mail store.
"""
from __future__ import annotations

import uuid
from typing import Any

from . import mail_migration, postgres_db

FOLDERS = frozenset({"inbox", "sent", "draft", "review"})
MAX_LIMIT = 100


class MailboxUnavailable(RuntimeError):
    pass


def _uuid(value: object) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("invalid_mailbox_owner") from exc


def _folder(value: object) -> str:
    folder = str(value or "").strip().casefold()
    if folder not in FOLDERS:
        raise ValueError("invalid_mail_folder")
    return folder


def status() -> dict[str, Any]:
    schema = mail_migration.schema_status()
    return {
        "component": "OAP Mail mailbox",
        "schema_ready": bool(schema.get("schema_ready")),
        "read_only": True,
        "owner_scoped": True,
        "folders": tuple(sorted(FOLDERS)),
        "inbound_transport_built": False,
        "delivery_claimed": False,
        "ready": bool(schema.get("schema_ready")),
        "error": schema.get("error"),
    }


def list_folder(owner_id: object, folder: object, *, limit: int = 50) -> list[dict[str, Any]]:
    owner = _uuid(owner_id)
    clean_folder = _folder(folder)
    bounded = max(1, min(int(limit), MAX_LIMIT))
    if not status()["ready"]:
        raise MailboxUnavailable("oap_mail_mailbox_unavailable")
    try:
        with postgres_db.connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT id,folder,subject,body,correspondent,created_at,updated_at
                   FROM oap_mail_items
                   WHERE owner_id=%s AND folder=%s
                   ORDER BY created_at DESC
                   LIMIT %s""",
                (owner, clean_folder, bounded),
            ).fetchall()
    except Exception as exc:
        raise MailboxUnavailable("oap_mail_mailbox_unavailable") from exc

    return [
        {
            "id": str(row[0]),
            "folder": str(row[1]),
            "subject": str(row[2]),
            "body": str(row[3]),
            "correspondent": str(row[4]),
            "created_at": row[5].isoformat(),
            "updated_at": row[6].isoformat(),
        }
        for row in rows
    ]


def search(owner_id: object, query: object, *, limit: int = 50) -> list[dict[str, Any]]:
    owner = _uuid(owner_id)
    clean = str(query or "").strip()
    if not clean or len(clean) > 200:
        raise ValueError("invalid_mail_search")
    bounded = max(1, min(int(limit), MAX_LIMIT))
    if not status()["ready"]:
        raise MailboxUnavailable("oap_mail_mailbox_unavailable")
    pattern = f"%{clean}%"
    try:
        with postgres_db.connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT id,folder,subject,body,correspondent,created_at,updated_at
                   FROM oap_mail_items
                   WHERE owner_id=%s
                     AND (subject ILIKE %s OR correspondent ILIKE %s OR body ILIKE %s)
                   ORDER BY created_at DESC
                   LIMIT %s""",
                (owner, pattern, pattern, pattern, bounded),
            ).fetchall()
    except Exception as exc:
        raise MailboxUnavailable("oap_mail_mailbox_unavailable") from exc

    return [
        {
            "id": str(row[0]),
            "folder": str(row[1]),
            "subject": str(row[2]),
            "body": str(row[3]),
            "correspondent": str(row[4]),
            "created_at": row[5].isoformat(),
            "updated_at": row[6].isoformat(),
        }
        for row in rows
    ]
