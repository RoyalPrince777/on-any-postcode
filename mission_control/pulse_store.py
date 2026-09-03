"""First-party Pulse feed persistence using the governed public posts table."""

from __future__ import annotations

import json
import uuid
from typing import Any

from . import postgres_db

PULSE_SCOPE = "oap_pulse"
PULSE_REACTION_SCOPE = "oap_pulse_reaction"
PULSE_REPLY_SCOPE = "oap_pulse_reply"
MAX_PULSE_RECORDS = 100
MAX_INTERACTION_RECORDS = 500
MAX_WRITES_PER_MINUTE = 30
MAX_REPLY_LENGTH = 500
PUBLIC_USERNAME_PREFIX = "oap-session-"
ALLOWED_REACTIONS = ("like", "love", "fire", "support")
REACTION_LABELS = {
    "like": "👍 Like",
    "love": "❤️ Love",
    "fire": "🔥 Fire",
    "support": "💚 Support",
}


class PulseStoreUnavailable(RuntimeError):
    """Raised when Pulse persistence cannot be read or written safely."""


def _uuid(value: object, code: str) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(code) from exc


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


def _target_exists(connection: Any, post_id: str, *, lock: bool = False) -> bool:
    suffix = " FOR UPDATE" if lock else ""
    row = connection.execute(
        """SELECT 1 FROM posts
           WHERE id=%s AND scope=%s AND status='published'""" + suffix,
        (post_id, PULSE_SCOPE),
    ).fetchone()
    return row is not None


def _trim_scope(connection: Any, scope: str, limit: int) -> None:
    connection.execute(
        """DELETE FROM posts WHERE id IN (
               SELECT id FROM posts WHERE scope=%s
               ORDER BY created_at DESC OFFSET %s
           )""",
        (scope, limit),
    )


def add_post(identity_id: str, *, name: str, body: str) -> None:
    identity = _uuid(identity_id, "invalid_pulse_identity")
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
            _ensure_user(connection, identity)
            _check_write_rate(connection, identity)
            connection.execute(
                """INSERT INTO posts(user_id,body,scope,status)
                   VALUES (%s,%s,%s,'published')""",
                (identity, payload, PULSE_SCOPE),
            )
            _trim_scope(connection, PULSE_SCOPE, MAX_PULSE_RECORDS)
            connection.commit()
    except ValueError:
        raise
    except Exception as exc:
        raise PulseStoreUnavailable("pulse_write_failed") from exc


def add_reaction(identity_id: object, post_id: object, reaction: object) -> str:
    identity = _uuid(identity_id, "invalid_pulse_identity")
    target = _uuid(post_id, "invalid_pulse_post")
    choice = str(reaction or "").strip().casefold()
    if choice not in ALLOWED_REACTIONS:
        raise ValueError("invalid_pulse_reaction")
    try:
        with postgres_db.connect() as connection:
            _ensure_user(connection, identity)
            _check_write_rate(connection, identity)
            if not _target_exists(connection, target, lock=True):
                raise ValueError("pulse_post_not_found")
            rows = connection.execute(
                """SELECT id,body FROM posts
                   WHERE user_id=%s AND scope=%s AND status='published'
                   ORDER BY created_at DESC LIMIT 100""",
                (identity, PULSE_REACTION_SCOPE),
            ).fetchall()
            existing_id = None
            existing_reaction = None
            for row_id, raw_body in rows:
                try:
                    payload = json.loads(str(raw_body))
                except (TypeError, ValueError, json.JSONDecodeError):
                    continue
                if isinstance(payload, dict) and str(payload.get("target_id")) == target:
                    existing_id = str(row_id)
                    existing_reaction = str(payload.get("reaction", ""))
                    break
            if existing_id and existing_reaction == choice:
                connection.execute(
                    "DELETE FROM posts WHERE id=%s AND user_id=%s AND scope=%s",
                    (existing_id, identity, PULSE_REACTION_SCOPE),
                )
                state = "removed"
            else:
                body = json.dumps(
                    {"target_id": target, "reaction": choice},
                    separators=(",", ":"),
                )
                if existing_id:
                    connection.execute(
                        """UPDATE posts SET body=%s,created_at=CURRENT_TIMESTAMP
                           WHERE id=%s AND user_id=%s""",
                        (body, existing_id, identity),
                    )
                else:
                    connection.execute(
                        """INSERT INTO posts(user_id,body,scope,status)
                           VALUES (%s,%s,%s,'published')""",
                        (identity, body, PULSE_REACTION_SCOPE),
                    )
                state = "set"
            _trim_scope(connection, PULSE_REACTION_SCOPE, MAX_INTERACTION_RECORDS)
            connection.commit()
    except ValueError:
        raise
    except Exception as exc:
        raise PulseStoreUnavailable("pulse_reaction_failed") from exc
    return state


def add_reply(
    identity_id: object,
    post_id: object,
    *,
    name: object,
    body: object,
) -> None:
    identity = _uuid(identity_id, "invalid_pulse_identity")
    target = _uuid(post_id, "invalid_pulse_post")
    clean_name = str(name or "").strip()[:80]
    clean_body = str(body or "").strip()[:MAX_REPLY_LENGTH]
    if not clean_name or not clean_body:
        raise ValueError("pulse_reply_required")
    payload = json.dumps(
        {"target_id": target, "name": clean_name, "body": clean_body},
        ensure_ascii=False,
        separators=(",", ":"),
    )
    try:
        with postgres_db.connect() as connection:
            _ensure_user(connection, identity)
            _check_write_rate(connection, identity)
            if not _target_exists(connection, target):
                raise ValueError("pulse_post_not_found")
            connection.execute(
                """INSERT INTO posts(user_id,body,scope,status)
                   VALUES (%s,%s,%s,'published')""",
                (identity, payload, PULSE_REPLY_SCOPE),
            )
            _trim_scope(connection, PULSE_REPLY_SCOPE, MAX_INTERACTION_RECORDS)
            connection.commit()
    except ValueError:
        raise
    except Exception as exc:
        raise PulseStoreUnavailable("pulse_reply_failed") from exc


def list_posts() -> list[dict[str, Any]]:
    try:
        with postgres_db.connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT id,body,created_at FROM posts
                   WHERE scope=%s AND status='published'
                   ORDER BY created_at DESC LIMIT %s""",
                (PULSE_SCOPE, MAX_PULSE_RECORDS),
            ).fetchall()
            interactions = connection.execute(
                """SELECT scope,body,created_at FROM posts
                   WHERE scope IN (%s,%s) AND status='published'
                   ORDER BY created_at DESC LIMIT %s""",
                (
                    PULSE_REACTION_SCOPE,
                    PULSE_REPLY_SCOPE,
                    MAX_INTERACTION_RECORDS,
                ),
            ).fetchall()
    except Exception as exc:
        raise PulseStoreUnavailable("pulse_read_failed") from exc

    result: list[dict[str, Any]] = []
    by_id: dict[str, dict[str, Any]] = {}
    for post_id, raw_body, created_at in rows:
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
        post = {
            "id": str(post_id),
            "name": name[:80],
            "body": body[:2000],
            "created_at": str(created_at),
            "reactions": {reaction: 0 for reaction in ALLOWED_REACTIONS},
            "reaction_total": 0,
            "replies": [],
        }
        result.append(post)
        by_id[str(post_id)] = post

    for scope, raw_body, created_at in reversed(interactions):
        try:
            item = json.loads(str(raw_body))
        except (TypeError, ValueError, json.JSONDecodeError):
            continue
        if not isinstance(item, dict):
            continue
        target = by_id.get(str(item.get("target_id", "")))
        if target is None:
            continue
        if scope == PULSE_REACTION_SCOPE:
            reaction = str(item.get("reaction", ""))
            if reaction not in ALLOWED_REACTIONS:
                continue
            target["reactions"][reaction] += 1
            target["reaction_total"] += 1
            continue
        if scope == PULSE_REPLY_SCOPE and len(target["replies"]) < 20:
            name = str(item.get("name", "")).strip()
            body = str(item.get("body", "")).strip()
            if not name or not body:
                continue
            target["replies"].append(
                {
                    "name": name[:80],
                    "body": body[:MAX_REPLY_LENGTH],
                    "created_at": str(created_at),
                }
            )
    return result
