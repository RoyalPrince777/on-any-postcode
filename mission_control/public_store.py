"""Durable Neon-backed storage for the small OAP public community surface."""

from __future__ import annotations

import json
from typing import Any

from . import postgres_db

PUBLIC_SIGNAL_SCOPE = "oap_signal"
PUBLIC_ROOM_SCOPE = "oap_team_room"
PUBLIC_FLAG_SCOPE = "oap_flag"
PUBLIC_USERNAME_PREFIX = "oap-session-"
MAX_PUBLIC_RECORDS = 100
MAX_WRITES_PER_MINUTE = 30


class PublicStoreUnavailable(RuntimeError):
    """Raised when a configured durable public store cannot complete a write."""


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
        raise ValueError("community_rate_limit")


def _insert_post(
    identity_id: str,
    *,
    scope: str,
    body: str,
    location: str | None = None,
) -> None:
    try:
        with postgres_db.connect() as connection:
            _ensure_user(connection, identity_id)
            _check_write_rate(connection, identity_id)
            connection.execute(
                """INSERT INTO posts(user_id,body,scope,postcode,status)
                   VALUES (%s,%s,%s,%s,'published')""",
                (identity_id, body, scope, location),
            )
            if scope != PUBLIC_FLAG_SCOPE:
                connection.execute(
                    """DELETE FROM posts WHERE id IN (
                           SELECT id FROM posts WHERE scope=%s
                           ORDER BY created_at DESC OFFSET %s
                       )""",
                    (scope, MAX_PUBLIC_RECORDS),
                )
            connection.commit()
    except ValueError:
        raise
    except Exception as exc:
        raise PublicStoreUnavailable("durable_public_write_failed") from exc


def add_signal(identity_id: str, *, name: str, body: str) -> None:
    payload = json.dumps(
        {"name": name, "body": body}, ensure_ascii=False, separators=(",", ":")
    )
    _insert_post(identity_id, scope=PUBLIC_SIGNAL_SCOPE, body=payload)


def add_room_message(
    identity_id: str, *, room: str, name: str, message: str
) -> None:
    payload = json.dumps(
        {"name": name, "message": message},
        ensure_ascii=False,
        separators=(",", ":"),
    )
    _insert_post(
        identity_id,
        scope=PUBLIC_ROOM_SCOPE,
        body=payload,
        location=room,
    )


def add_flag(identity_id: str, *, team: str) -> None:
    _insert_post(identity_id, scope=PUBLIC_FLAG_SCOPE, body=team)


def update_profile(identity_id: str, *, nickname: str, country: str) -> None:
    try:
        with postgres_db.connect() as connection:
            connection.execute(
                """INSERT INTO users(id,username,display_name,country,status)
                   VALUES (%s,%s,%s,%s,'active')
                   ON CONFLICT (id) DO UPDATE SET
                     display_name=EXCLUDED.display_name,
                     country=EXCLUDED.country,
                     updated_at=CURRENT_TIMESTAMP""",
                (identity_id, _username(identity_id), nickname, country),
            )
            connection.commit()
    except Exception as exc:
        raise PublicStoreUnavailable("durable_profile_write_failed") from exc


def ensure_authenticated_user(
    identity_id: str, *, email: str, display_name: str
) -> None:
    """Link a verified Neon Auth UUID to its established OAP user record."""

    try:
        with postgres_db.connect() as connection:
            connection.execute(
                """INSERT INTO users(
                       id,username,email,display_name,status
                   ) VALUES (%s,%s,%s,%s,'active')
                   ON CONFLICT (id) DO UPDATE SET
                     email=EXCLUDED.email,
                     display_name=COALESCE(users.display_name,EXCLUDED.display_name),
                     status='active',
                     updated_at=CURRENT_TIMESTAMP""",
                (
                    identity_id,
                    _username(identity_id),
                    email,
                    display_name,
                ),
            )
            connection.commit()
    except Exception as exc:
        raise PublicStoreUnavailable("authenticated_user_sync_failed") from exc


def get_profile(identity_id: str) -> dict[str, str] | None:
    """Load exactly one authenticated user's private My World projection."""

    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT display_name,country FROM users
                   WHERE id=%s AND status='active' LIMIT 1""",
                (identity_id,),
            ).fetchone()
    except Exception as exc:
        raise PublicStoreUnavailable("private_profile_read_failed") from exc
    if row is None:
        return None
    return {"nickname": str(row[0] or ""), "country": str(row[1] or "")}


def _decode_object(raw: object) -> dict[str, str] | None:
    try:
        value = json.loads(str(raw))
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    if not isinstance(value, dict):
        return None
    return {str(key): str(item) for key, item in value.items()}


def snapshot() -> dict[str, Any]:
    """Load bounded community posts; profiles stay inside private My World."""

    try:
        with postgres_db.connect(readonly=True) as connection:
            signal_rows = connection.execute(
                """SELECT body FROM posts
                   WHERE scope=%s AND status='published'
                   ORDER BY created_at DESC LIMIT %s""",
                (PUBLIC_SIGNAL_SCOPE, MAX_PUBLIC_RECORDS),
            ).fetchall()
            room_rows = connection.execute(
                """SELECT postcode,body FROM posts
                   WHERE scope=%s AND status='published'
                   ORDER BY created_at DESC LIMIT %s""",
                (PUBLIC_ROOM_SCOPE, MAX_PUBLIC_RECORDS),
            ).fetchall()
            flag_rows = connection.execute(
                """SELECT body,COUNT(*) FROM posts
                   WHERE scope=%s AND status='published'
                   GROUP BY body""",
                (PUBLIC_FLAG_SCOPE,),
            ).fetchall()
    except Exception as exc:
        raise PublicStoreUnavailable("durable_public_read_failed") from exc

    signals = [item for row in signal_rows if (item := _decode_object(row[0]))]
    messages: list[dict[str, str]] = []
    for row in room_rows:
        item = _decode_object(row[1])
        if item:
            messages.append(
                {
                    "room": str(row[0] or "Team Room"),
                    "name": item.get("name", "Visitor"),
                    "message": item.get("message", ""),
                }
            )
    return {
        "signal_posts": signals,
        "team_messages": messages,
        "flag_counts": {str(row[0]): int(row[1]) for row in flag_rows},
        "durable": True,
    }


def status() -> dict[str, Any]:
    """Return a redacted schema-and-connectivity readiness check."""

    result = {
        "configured": postgres_db.configured(),
        "reachable": False,
        "schema_ready": False,
        "durable": False,
        "error": None,
    }
    if not result["configured"]:
        result["error"] = "database_url_not_configured"
        return result
    try:
        with postgres_db.connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT table_name,column_name FROM information_schema.columns
                   WHERE table_schema='public' AND table_name IN ('users','posts')"""
            ).fetchall()
            columns: dict[str, set[str]] = {"users": set(), "posts": set()}
            for table_name, column_name in rows:
                columns.setdefault(str(table_name), set()).add(str(column_name))
            result["reachable"] = True
            result["schema_ready"] = {
                "id",
                "username",
                "display_name",
                "country",
                "status",
                "updated_at",
            } <= columns["users"] and {
                "id",
                "user_id",
                "body",
                "scope",
                "postcode",
                "status",
                "created_at",
            } <= columns["posts"]
            result["durable"] = result["schema_ready"]
    # A readiness endpoint must degrade safely for every driver/network failure.
    except Exception:  # noqa: BLE001
        result["error"] = "database_unavailable"
    return result
