"""First-party Pulse feed persistence using the governed public posts table."""

from __future__ import annotations

import json
from typing import Any

from . import postgres_db

PULSE_SCOPE = "oap_pulse"
MAX_PULSE_RECORDS = 100
MAX_WRITES_PER_MINUTE = 30
PUBLIC_USERNAME_PREFIX = "oap-session-"


class PulseStoreUnavailable(RuntimeError):
    """Raised when Pulse persistence cannot be read or written safely."""


def _username(identity_id: str) -> str:
    return f"{PUBLIC_USERNAME_PREFIX}{identity_id.replace('-', '')}"


def _ensure_user(connection: Any, identity_id: str) -> None:
    connection.execute(
        """INSERT INTO users(id,username,status)
           VALUES (%s,%s,'active') ON CONFLICT (id) DO NOTHING""",
        (identity_id, _username(identity_id)),
    )


def _check_write_rate(connection: Any, identity_id: str) -> None:
    row = connection.execute(
        """SELECT COUNT(*) FROM posts
           WHERE user_id=%s AND created_at >= CURRENT_TIMESTAMP - INTERVAL '1 minute'""",
        (identity_id,),
    ).fetchone()
    if row and int(row[0]) >= MAX_WRITES_PER_MINUTE:
        raise ValueError("pulse_rate_limit")


def add_post(identity_id: str, *, name: str, body: str) -> None:
    clean_name = str(name).strip()[:80]
    clean_body = str(body).strip()[:2000]
    if not clean_name or not clean_body:
        raise ValueError("pulse_content_required")
    payload = json.dumps(
        {"name": clean_name, "body": clean_body},
        ensure_ascii=False,
        separators=(",", ":"),
    )
    try:
        with postgres_db.connect() as connection:
            _ensure_user(connection, identity_id)
            _check_write_rate(connection, identity_id)
            connection.execute(
                """INSERT INTO posts(user_id,body,scope,status)
                   VALUES (%s,%s,%s,'published')""",
                (identity_id, payload, PULSE_SCOPE),
            )
            connection.execute(
                """DELETE FROM posts WHERE id IN (
                       SELECT id FROM posts WHERE scope=%s
                       ORDER BY created_at DESC OFFSET %s
                   )""",
                (PULSE_SCOPE, MAX_PULSE_RECORDS),
            )
            connection.commit()
    except ValueError:
        raise
    except Exception as exc:
        raise PulseStoreUnavailable("pulse_write_failed") from exc


def list_posts() -> list[dict[str, str]]:
    try:
        with postgres_db.connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT body,created_at FROM posts
                   WHERE scope=%s AND status='published'
                   ORDER BY created_at DESC LIMIT %s""",
                (PULSE_SCOPE, MAX_PULSE_RECORDS),
            ).fetchall()
    except Exception as exc:
        raise PulseStoreUnavailable("pulse_read_failed") from exc

    result: list[dict[str, str]] = []
    for raw_body, created_at in rows:
        try:
            item = json.loads(str(raw_body))
        except (TypeError, ValueError, json.JSONDecodeError):
            continue
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        body = str(item.get("body", "")).strip()
        if not name or not body:
            continue
        result.append(
            {
                "name": name[:80],
                "body": body[:2000],
                "created_at": str(created_at),
            }
        )
    return result
