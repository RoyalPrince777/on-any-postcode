"""Temporary no-sign-in OAP PTT pairing.

Guest PTT identities are short-lived internal UUID users. Pairing codes resolve only
recent OAP PTT guest rows, then create an accepted purpose Link with an expiry so
existing Voice block, youth and integrity guards can be reused without creating a
parallel media authority.
"""
from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from . import link_relationships, postgres_db

PAIR_CODE_DIGITS = 8
INVITE_TTL_MINUTES = 10
PAIR_TTL_MINUTES = 60
GUEST_DISPLAY_NAME = "OAP PTT Guest"
GUEST_USERNAME_PREFIX = "oap-ptt-guest-"
PAIR_PURPOSE = "OAP PTT temporary pairing"
MAX_CODE_ATTEMPTS = 12


class PttGuestUnavailable(RuntimeError):
    pass


def _uuid(value: object, code: str) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(code) from exc


def _code(value: object) -> str:
    code = "".join(ch for ch in str(value or "") if ch.isdigit())
    if len(code) != PAIR_CODE_DIGITS:
        raise ValueError("invalid_pair_code")
    return code


def _guest_username(code: str) -> str:
    return f"{GUEST_USERNAME_PREFIX}{code}"


def _session_username(identity_id: str) -> str:
    return f"{GUEST_USERNAME_PREFIX}s-{identity_id.replace('-', '')}"


def _active_pair_from_relations(identity_id: str) -> dict[str, Any] | None:
    now = datetime.now(UTC)
    for relation in link_relationships.list_for_identity(identity_id):
        if relation.get("status") != "accepted":
            continue
        if relation.get("link_kind") != "purpose":
            continue
        if relation.get("purpose_text") != PAIR_PURPOSE:
            continue
        expires_raw = relation.get("expires_at")
        if not expires_raw:
            continue
        try:
            expires = datetime.fromisoformat(str(expires_raw))
        except ValueError:
            continue
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=UTC)
        if expires <= now:
            continue
        peer_id = (
            str(relation["recipient_id"])
            if str(relation["requester_id"]) == identity_id
            else str(relation["requester_id"])
        )
        return {
            "active": True,
            "relationship_id": str(relation["relationship_id"]),
            "peer_id": peer_id,
            "expires_at": expires.isoformat(),
        }
    return None


def active_pair(identity_id: object) -> dict[str, Any] | None:
    identity = _uuid(identity_id, "invalid_guest_identity")
    try:
        return _active_pair_from_relations(identity)
    except link_relationships.LinkRelationshipsUnavailable as exc:
        raise PttGuestUnavailable("ptt_pairing_unavailable") from exc


def _insert_guest(connection: Any, identity_id: str, username: str) -> None:
    connection.execute(
        """INSERT INTO users(id,username,display_name,status)
           VALUES (%s,%s,%s,'active')
           ON CONFLICT (id) DO UPDATE SET
             username=EXCLUDED.username,
             display_name=EXCLUDED.display_name,
             status='active',
             updated_at=CURRENT_TIMESTAMP""",
        (identity_id, username, GUEST_DISPLAY_NAME),
    )


def create_invite() -> dict[str, str]:
    identity_id = str(uuid.uuid4())
    try:
        with postgres_db.connect() as connection:
            for _attempt in range(MAX_CODE_ATTEMPTS):
                code = f"{secrets.randbelow(10 ** PAIR_CODE_DIGITS):0{PAIR_CODE_DIGITS}d}"
                username = _guest_username(code)
                exists = connection.execute(
                    "SELECT 1 FROM users WHERE username=%s LIMIT 1",
                    (username,),
                ).fetchone()
                if exists is not None:
                    continue
                _insert_guest(connection, identity_id, username)
                connection.commit()
                return {
                    "identity_id": identity_id,
                    "code": code,
                    "expires_at": (
                        datetime.now(UTC) + timedelta(minutes=INVITE_TTL_MINUTES)
                    ).isoformat(),
                }
        raise PttGuestUnavailable("pair_code_generation_failed")
    except PttGuestUnavailable:
        raise
    except Exception as exc:
        raise PttGuestUnavailable("ptt_invite_store_failed") from exc


def ensure_session_guest(identity_id: object | None = None) -> str:
    identity = (
        str(uuid.uuid4())
        if not identity_id
        else _uuid(identity_id, "invalid_guest_identity")
    )
    try:
        with postgres_db.connect() as connection:
            _insert_guest(connection, identity, _session_username(identity))
            connection.commit()
    except Exception as exc:
        raise PttGuestUnavailable("ptt_guest_identity_failed") from exc
    return identity


def join_invite(code_value: object, joiner_identity_id: object | None = None) -> dict[str, Any]:
    code = _code(code_value)
    username = _guest_username(code)
    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT id FROM users
                   WHERE username=%s
                     AND display_name=%s
                     AND status='active'
                     AND updated_at >= CURRENT_TIMESTAMP - INTERVAL '10 minutes'
                   LIMIT 1""",
                (username, GUEST_DISPLAY_NAME),
            ).fetchone()
        if row is None:
            raise ValueError("pair_code_expired_or_unknown")
        creator = str(row[0])
        if joiner_identity_id and creator == _uuid(joiner_identity_id, "invalid_guest_identity"):
            raise ValueError("cannot_pair_same_device")
        joiner = ensure_session_guest(joiner_identity_id)
        if creator == joiner:
            raise ValueError("cannot_pair_same_device")
        if _active_pair_from_relations(creator) is not None:
            raise ValueError("pair_code_already_used")
        if _active_pair_from_relations(joiner) is not None:
            raise ValueError("device_already_paired")
        expiry = datetime.now(UTC) + timedelta(minutes=PAIR_TTL_MINUTES)
        relationship_id = link_relationships.request_link(
            creator,
            joiner,
            link_kind="purpose",
            purpose_text=PAIR_PURPOSE,
            expires_at=expiry,
        )
        if not link_relationships.respond(joiner, relationship_id, "accepted"):
            raise PttGuestUnavailable("ptt_pair_accept_failed")
        return {
            "active": True,
            "identity_id": joiner,
            "peer_id": creator,
            "relationship_id": relationship_id,
            "expires_at": expiry.isoformat(),
        }
    except (ValueError, PttGuestUnavailable):
        raise
    except link_relationships.LinkRelationshipsUnavailable as exc:
        raise PttGuestUnavailable("ptt_pairing_unavailable") from exc
    except Exception as exc:
        raise PttGuestUnavailable("ptt_pairing_unavailable") from exc


def _deactivate_guest(identity_id: str) -> None:
    try:
        with postgres_db.connect() as connection:
            connection.execute(
                """UPDATE users SET status='inactive',updated_at=CURRENT_TIMESTAMP
                   WHERE id=%s AND display_name=%s""",
                (identity_id, GUEST_DISPLAY_NAME),
            )
            connection.commit()
    except Exception as exc:
        raise PttGuestUnavailable("ptt_guest_deactivate_failed") from exc


def stop(identity_id: object) -> bool:
    identity = _uuid(identity_id, "invalid_guest_identity")
    try:
        pair = _active_pair_from_relations(identity)
        if pair is None:
            _deactivate_guest(identity)
            return False
        revoked = link_relationships.revoke(identity, pair["relationship_id"])
        _deactivate_guest(identity)
        return revoked
    except link_relationships.LinkRelationshipsUnavailable as exc:
        raise PttGuestUnavailable("ptt_pairing_unavailable") from exc


def _invite_valid(identity_id: str, code: str) -> bool:
    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT 1 FROM users
                   WHERE id=%s
                     AND username=%s
                     AND display_name=%s
                     AND status='active'
                     AND updated_at >= CURRENT_TIMESTAMP - INTERVAL '10 minutes'
                   LIMIT 1""",
                (identity_id, _guest_username(code), GUEST_DISPLAY_NAME),
            ).fetchone()
        return row is not None
    except Exception as exc:
        raise PttGuestUnavailable("ptt_invite_status_failed") from exc


def invite_state(identity_id: object, code_value: object | None) -> dict[str, Any]:
    identity = _uuid(identity_id, "invalid_guest_identity")
    pair = active_pair(identity)
    if pair is not None:
        return pair
    code = None
    if code_value:
        try:
            candidate = _code(code_value)
            code = candidate if _invite_valid(identity, candidate) else None
        except ValueError:
            code = None
    return {
        "active": False,
        "identity_id": identity,
        "code": code,
        "peer_id": None,
        "expires_at": None,
    }
