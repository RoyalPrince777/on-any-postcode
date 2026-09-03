"""First-party OAP Link Voice storage and deterministic Guardian validation.

Schema activation is explicit. Voice bytes are stored inside OAP Data; no
external object store, media processor, analytics SDK or scanning provider is
required by this module.
"""
from __future__ import annotations

import hashlib
import uuid
from typing import Any

from . import link_relationships, linkup_safety, postgres_db

SCHEMA_VERSION = "link_voice_v1"
MAX_VOICE_BYTES = 5 * 1024 * 1024
MAX_VOICE_DURATION_MS = 120_000
MAX_SENDER_STORAGE_BYTES = 100 * 1024 * 1024
ALLOWED_MIME_TYPES = (
    "audio/webm",
    "audio/ogg",
    "audio/mp4",
    "audio/mpeg",
)

SCHEMA_SQL = (
    """CREATE TABLE IF NOT EXISTS link_voice_notes (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        sender_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        recipient_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        mime_type TEXT NOT NULL CHECK (mime_type IN ('audio/webm','audio/ogg','audio/mp4','audio/mpeg')),
        byte_size INTEGER NOT NULL CHECK (byte_size > 0 AND byte_size <= 5242880),
        duration_ms INTEGER CHECK (duration_ms IS NULL OR (duration_ms >= 0 AND duration_ms <= 120000)),
        sha256 CHAR(64) NOT NULL,
        media BYTEA NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CHECK (sender_id <> recipient_id))""",
    "CREATE INDEX IF NOT EXISTS idx_link_voice_recipient_created ON link_voice_notes(recipient_id,created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_link_voice_sender_created ON link_voice_notes(sender_id,created_at DESC)",
)


class LinkVoiceUnavailable(RuntimeError):
    pass


def _uuid(value: object, code: str) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(code) from exc


def _mime(value: object) -> str:
    mime = str(value or "").split(";", 1)[0].strip().casefold()
    if mime not in ALLOWED_MIME_TYPES:
        raise ValueError("unsupported_voice_type")
    return mime


def _guardian_validate(media: bytes, mime_type: object) -> str:
    if not isinstance(media, bytes):
        raise TypeError("invalid_voice_data")
    if not media:
        raise ValueError("empty_voice")
    if len(media) > MAX_VOICE_BYTES:
        raise ValueError("voice_too_large")
    mime = _mime(mime_type)
    valid_magic = False
    if mime == "audio/webm":
        valid_magic = media.startswith(b"\x1aE\xdf\xa3")
    elif mime == "audio/ogg":
        valid_magic = media.startswith(b"OggS")
    elif mime == "audio/mp4":
        valid_magic = len(media) >= 12 and media[4:8] == b"ftyp"
    elif mime == "audio/mpeg":
        valid_magic = media.startswith(b"ID3") or (
            len(media) >= 2 and media[0] == 0xFF and media[1] & 0xE0 == 0xE0
        )
    if not valid_magic:
        raise ValueError("voice_content_mismatch")
    return mime


def _duration(value: object) -> int | None:
    if value in {None, ""}:
        return None
    try:
        duration = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid_voice_duration") from exc
    if not 0 <= duration <= MAX_VOICE_DURATION_MS:
        raise ValueError("invalid_voice_duration")
    return duration


def _peer_guard(first_id: object, second_id: object) -> tuple[str, str]:
    first = _uuid(first_id, "invalid_identity")
    second = _uuid(second_id, "invalid_peer")
    if first == second:
        raise ValueError("cannot_voice_self")
    try:
        if linkup_safety.blocked_between(first, second):
            raise ValueError("link_blocked")
        if not link_relationships.accepted_between(first, second):
            raise ValueError("accepted_link_required")
    except ValueError:
        raise
    except (linkup_safety.LinkUpSafetyUnavailable, link_relationships.LinkRelationshipsUnavailable) as exc:
        raise LinkVoiceUnavailable("voice_link_guard_unavailable") from exc
    return first, second


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
        raise LinkVoiceUnavailable("voice_schema_failed") from exc
    return {"version": SCHEMA_VERSION, "applied": True}


def status() -> dict[str, Any]:
    result: dict[str, Any] = {
        "configured": postgres_db.configured(),
        "schema_ready": False,
        "ready": False,
        "first_party": True,
        "guardian_validation": "deterministic_audio",
        "external_media_provider_required": False,
        "max_voice_bytes": MAX_VOICE_BYTES,
        "max_voice_duration_ms": MAX_VOICE_DURATION_MS,
    }
    if not result["configured"]:
        return result
    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT 1 FROM information_schema.tables
                   WHERE table_schema='public' AND table_name='link_voice_notes'"""
            ).fetchone()
        result["schema_ready"] = row is not None
    except Exception:  # noqa: BLE001 - status is intentionally coarse and fail-closed.
        return result
    result["ready"] = bool(result["schema_ready"])
    return result


def create_voice(
    sender_id: object,
    recipient_id: object,
    *,
    media: bytes,
    mime_type: object,
    duration_ms: object = None,
) -> dict[str, object]:
    sender, recipient = _peer_guard(sender_id, recipient_id)
    mime = _guardian_validate(media, mime_type)
    duration = _duration(duration_ms)
    digest = hashlib.sha256(media).hexdigest()
    size = len(media)
    try:
        with postgres_db.connect() as connection:
            used_row = connection.execute(
                "SELECT COALESCE(SUM(byte_size),0) FROM link_voice_notes WHERE sender_id=%s",
                (sender,),
            ).fetchone()
            used = int(used_row[0] or 0) if used_row else 0
            if used + size > MAX_SENDER_STORAGE_BYTES:
                raise ValueError("voice_storage_quota_reached")
            row = connection.execute(
                """INSERT INTO link_voice_notes(
                       sender_id,recipient_id,mime_type,byte_size,duration_ms,sha256,media)
                   VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id,created_at""",
                (sender, recipient, mime, size, duration, digest, media),
            ).fetchone()
            connection.commit()
    except ValueError:
        raise
    except Exception as exc:
        raise LinkVoiceUnavailable("voice_store_failed") from exc
    return {
        "voice_id": str(row[0]),
        "mime_type": mime,
        "byte_size": size,
        "duration_ms": duration,
        "sha256": digest,
        "created_at": row[1].isoformat(),
    }


def list_voice(identity_id: object, peer_id: object, *, limit: int = 100) -> list[dict[str, object]]:
    identity, peer = _peer_guard(identity_id, peer_id)
    bounded_limit = max(1, min(int(limit), 100))
    try:
        with postgres_db.connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT id,sender_id,recipient_id,mime_type,byte_size,duration_ms,created_at
                   FROM link_voice_notes
                   WHERE (sender_id=%s AND recipient_id=%s)
                      OR (sender_id=%s AND recipient_id=%s)
                   ORDER BY created_at DESC LIMIT %s""",
                (identity, peer, peer, identity, bounded_limit),
            ).fetchall()
    except Exception as exc:
        raise LinkVoiceUnavailable("voice_list_failed") from exc
    return [
        {
            "voice_id": str(row[0]),
            "direction": "sent" if str(row[1]) == identity else "received",
            "mime_type": str(row[3]),
            "byte_size": int(row[4]),
            "duration_ms": None if row[5] is None else int(row[5]),
            "created_at": row[6].isoformat(),
        }
        for row in rows
    ]


def read_voice(identity_id: object, peer_id: object, voice_id: object) -> tuple[bytes, str, str] | None:
    identity, peer = _peer_guard(identity_id, peer_id)
    note = _uuid(voice_id, "invalid_voice")
    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT media,mime_type,sha256 FROM link_voice_notes
                   WHERE id=%s AND (
                     (sender_id=%s AND recipient_id=%s)
                     OR (sender_id=%s AND recipient_id=%s)
                   ) LIMIT 1""",
                (note, identity, peer, peer, identity),
            ).fetchone()
    except Exception as exc:
        raise LinkVoiceUnavailable("voice_read_failed") from exc
    if row is None:
        return None
    data = bytes(row[0])
    if hashlib.sha256(data).hexdigest() != str(row[2]):
        raise LinkVoiceUnavailable("voice_integrity_failed")
    return data, str(row[1]), str(row[2])


def delete_voice(sender_id: object, voice_id: object) -> bool:
    sender = _uuid(sender_id, "invalid_identity")
    note = _uuid(voice_id, "invalid_voice")
    try:
        with postgres_db.connect() as connection:
            row = connection.execute(
                "DELETE FROM link_voice_notes WHERE id=%s AND sender_id=%s RETURNING id",
                (note, sender),
            ).fetchone()
            connection.commit()
    except Exception as exc:
        raise LinkVoiceUnavailable("voice_delete_failed") from exc
    return row is not None
