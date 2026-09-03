"""First-party OAP Link Share storage and deterministic Guardian validation.

Schema activation is explicit. Certified Share bytes are stored inside OAP Data;
no external object store, CDN, media processor, analytics SDK or scanning provider
is required by this module.
"""
from __future__ import annotations

import hashlib
import re
import uuid
from pathlib import PurePath
from typing import Any

from . import link_relationships, linkup_safety, postgres_db

SCHEMA_VERSION = "link_share_v1"
MAX_SHARE_BYTES = 25 * 1024 * 1024
MAX_SENDER_STORAGE_BYTES = 500 * 1024 * 1024
MAX_NAME_LENGTH = 180
ALLOWED_MIME_TYPES = {
    "image/jpeg": "photo",
    "image/png": "photo",
    "image/webp": "photo",
    "video/mp4": "video",
    "video/webm": "video",
    "application/pdf": "file",
    "text/plain": "file",
}

SCHEMA_SQL = (
    """CREATE TABLE IF NOT EXISTS link_shares (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        sender_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        recipient_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        kind TEXT NOT NULL CHECK (kind IN ('photo','video','file')),
        original_name TEXT NOT NULL CHECK (char_length(original_name) BETWEEN 1 AND 180),
        mime_type TEXT NOT NULL CHECK (mime_type IN ('image/jpeg','image/png','image/webp','video/mp4','video/webm','application/pdf','text/plain')),
        byte_size INTEGER NOT NULL CHECK (byte_size > 0 AND byte_size <= 26214400),
        sha256 CHAR(64) NOT NULL,
        media BYTEA NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CHECK (sender_id <> recipient_id),
        CHECK (
          (kind='photo' AND mime_type IN ('image/jpeg','image/png','image/webp')) OR
          (kind='video' AND mime_type IN ('video/mp4','video/webm')) OR
          (kind='file' AND mime_type IN ('application/pdf','text/plain'))
        ))""",
    "CREATE INDEX IF NOT EXISTS idx_link_shares_recipient_created ON link_shares(recipient_id,created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_link_shares_sender_created ON link_shares(sender_id,created_at DESC)",
)


class LinkShareUnavailable(RuntimeError):
    pass


def _uuid(value: object, code: str) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(code) from exc


def _safe_name(value: object) -> str:
    raw = PurePath(str(value or "share").replace("\\", "/")).name.strip()
    raw = re.sub(r"[^A-Za-z0-9._() -]+", "_", raw)
    raw = re.sub(r"\s+", " ", raw).strip(" .")
    if not raw:
        raw = "share"
    return raw[:MAX_NAME_LENGTH]


def _mime(value: object) -> tuple[str, str]:
    mime = str(value or "").split(";", 1)[0].strip().casefold()
    kind = ALLOWED_MIME_TYPES.get(mime)
    if kind is None:
        raise ValueError("unsupported_share_type")
    return mime, kind


def _guardian_validate(media: bytes, mime_type: object) -> tuple[str, str]:
    if not isinstance(media, bytes):
        raise TypeError("invalid_share_data")
    if not media:
        raise ValueError("empty_share")
    if len(media) > MAX_SHARE_BYTES:
        raise ValueError("share_too_large")
    mime, kind = _mime(mime_type)
    valid = False
    if mime == "image/jpeg":
        valid = len(media) >= 3 and media[:3] == b"\xff\xd8\xff"
    elif mime == "image/png":
        valid = media.startswith(b"\x89PNG\r\n\x1a\n")
    elif mime == "image/webp":
        valid = len(media) >= 12 and media[:4] == b"RIFF" and media[8:12] == b"WEBP"
    elif mime == "video/mp4":
        valid = len(media) >= 12 and media[4:8] == b"ftyp"
    elif mime == "video/webm":
        valid = media.startswith(b"\x1aE\xdf\xa3")
    elif mime == "application/pdf":
        valid = media.startswith(b"%PDF-")
    elif mime == "text/plain":
        try:
            decoded = media.decode("utf-8")
        except UnicodeDecodeError:
            decoded = ""
        valid = bool(decoded or media == b"") and "\x00" not in decoded
    if not valid:
        raise ValueError("share_content_mismatch")
    return mime, kind


def _peer_guard(first_id: object, second_id: object) -> tuple[str, str]:
    first = _uuid(first_id, "invalid_identity")
    second = _uuid(second_id, "invalid_peer")
    if first == second:
        raise ValueError("cannot_share_self")
    try:
        if linkup_safety.blocked_between(first, second):
            raise ValueError("link_blocked")
        if not link_relationships.accepted_between(first, second):
            raise ValueError("accepted_link_required")
    except ValueError:
        raise
    except (linkup_safety.LinkUpSafetyUnavailable, link_relationships.LinkRelationshipsUnavailable) as exc:
        raise LinkShareUnavailable("share_link_guard_unavailable") from exc
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
        raise LinkShareUnavailable("share_schema_failed") from exc
    return {"version": SCHEMA_VERSION, "applied": True}


def status() -> dict[str, Any]:
    result: dict[str, Any] = {
        "configured": postgres_db.configured(),
        "schema_ready": False,
        "ready": False,
        "first_party": True,
        "guardian_validation": "deterministic_certified_share",
        "external_media_provider_required": False,
        "max_share_bytes": MAX_SHARE_BYTES,
        "allowed_mime_types": sorted(ALLOWED_MIME_TYPES),
    }
    if not result["configured"]:
        return result
    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT 1 FROM information_schema.tables
                   WHERE table_schema='public' AND table_name='link_shares'"""
            ).fetchone()
        result["schema_ready"] = row is not None
    except Exception:  # noqa: BLE001 - status is intentionally coarse and fail-closed.
        return result
    result["ready"] = bool(result["schema_ready"])
    return result


def create_share(
    sender_id: object,
    recipient_id: object,
    *,
    media: bytes,
    mime_type: object,
    original_name: object,
) -> dict[str, object]:
    sender, recipient = _peer_guard(sender_id, recipient_id)
    mime, kind = _guardian_validate(media, mime_type)
    name = _safe_name(original_name)
    digest = hashlib.sha256(media).hexdigest()
    size = len(media)
    try:
        with postgres_db.connect() as connection:
            used_row = connection.execute(
                "SELECT COALESCE(SUM(byte_size),0) FROM link_shares WHERE sender_id=%s",
                (sender,),
            ).fetchone()
            used = int(used_row[0] or 0) if used_row else 0
            if used + size > MAX_SENDER_STORAGE_BYTES:
                raise ValueError("share_storage_quota_reached")
            row = connection.execute(
                """INSERT INTO link_shares(
                       sender_id,recipient_id,kind,original_name,mime_type,byte_size,sha256,media)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id,created_at""",
                (sender, recipient, kind, name, mime, size, digest, media),
            ).fetchone()
            connection.commit()
    except ValueError:
        raise
    except Exception as exc:
        raise LinkShareUnavailable("share_store_failed") from exc
    return {
        "share_id": str(row[0]),
        "kind": kind,
        "original_name": name,
        "mime_type": mime,
        "byte_size": size,
        "sha256": digest,
        "created_at": row[1].isoformat(),
    }


def list_shares(identity_id: object, peer_id: object, *, limit: int = 100) -> list[dict[str, object]]:
    identity, peer = _peer_guard(identity_id, peer_id)
    bounded_limit = max(1, min(int(limit), 100))
    try:
        with postgres_db.connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT id,sender_id,recipient_id,kind,original_name,mime_type,byte_size,created_at
                   FROM link_shares
                   WHERE (sender_id=%s AND recipient_id=%s)
                      OR (sender_id=%s AND recipient_id=%s)
                   ORDER BY created_at DESC LIMIT %s""",
                (identity, peer, peer, identity, bounded_limit),
            ).fetchall()
    except Exception as exc:
        raise LinkShareUnavailable("share_list_failed") from exc
    return [
        {
            "share_id": str(row[0]),
            "direction": "sent" if str(row[1]) == identity else "received",
            "kind": str(row[3]),
            "original_name": str(row[4]),
            "mime_type": str(row[5]),
            "byte_size": int(row[6]),
            "created_at": row[7].isoformat(),
        }
        for row in rows
    ]


def read_share(
    identity_id: object,
    peer_id: object,
    share_id: object,
) -> tuple[bytes, str, str, str, str] | None:
    identity, peer = _peer_guard(identity_id, peer_id)
    item = _uuid(share_id, "invalid_share")
    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT media,mime_type,sha256,original_name,kind FROM link_shares
                   WHERE id=%s AND (
                     (sender_id=%s AND recipient_id=%s)
                     OR (sender_id=%s AND recipient_id=%s)
                   ) LIMIT 1""",
                (item, identity, peer, peer, identity),
            ).fetchone()
    except Exception as exc:
        raise LinkShareUnavailable("share_read_failed") from exc
    if row is None:
        return None
    data = bytes(row[0])
    if hashlib.sha256(data).hexdigest() != str(row[2]):
        raise LinkShareUnavailable("share_integrity_failed")
    return data, str(row[1]), str(row[2]), str(row[3]), str(row[4])


def delete_share(sender_id: object, share_id: object) -> bool:
    sender = _uuid(sender_id, "invalid_identity")
    item = _uuid(share_id, "invalid_share")
    try:
        with postgres_db.connect() as connection:
            row = connection.execute(
                "DELETE FROM link_shares WHERE id=%s AND sender_id=%s RETURNING id",
                (item, sender),
            ).fetchone()
            connection.commit()
    except Exception as exc:
        raise LinkShareUnavailable("share_delete_failed") from exc
    return row is not None
