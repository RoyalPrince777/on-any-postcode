"""First-party owner-scoped video assets for OAP Media.

Video bytes remain inside OAP Data. This module provides a bounded private-review
asset store only. It does not grant rights, publish media, create a public stream,
or bypass the canonical Rights Core / entitlement gates.
"""
from __future__ import annotations

import hashlib
import uuid

from . import postgres_db

MEDIA_ASSET_MIGRATION_VERSION = "0014_oap_media_assets"
SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_media_assets (
        asset_id UUID PRIMARY KEY,
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        title TEXT NOT NULL,
        media_kind TEXT NOT NULL CHECK (media_kind IN ('video')),
        original_name TEXT NOT NULL,
        mime_type TEXT NOT NULL,
        byte_size INTEGER NOT NULL CHECK (byte_size > 0 AND byte_size <= 67108864),
        sha256 CHAR(64) NOT NULL,
        media BYTEA NOT NULL,
        stopped BOOLEAN NOT NULL DEFAULT FALSE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        stopped_at TIMESTAMPTZ NULL
    )""",
    """CREATE INDEX IF NOT EXISTS ix_media_asset_owner_created
       ON oap_media_assets(owner_identity_id, created_at DESC)""",
)

MAX_VIDEO_BYTES = 64 * 1024 * 1024
MAX_OWNER_STORAGE_BYTES = 1024 * 1024 * 1024
ALLOWED_MIME_TYPES = ("video/mp4", "video/webm")


class MediaAssetUnavailable(RuntimeError):
    pass


def _uuid(value: object, code: str) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(code) from exc


def _text(value: object, code: str, limit: int) -> str:
    text = " ".join(str(value or "").strip().split())
    if not text or len(text) > limit:
        raise ValueError(code)
    return text


def _mime(value: object) -> str:
    mime = str(value or "").split(";", 1)[0].strip().casefold()
    if mime not in ALLOWED_MIME_TYPES:
        raise ValueError("unsupported_video_type")
    return mime


def _validate_magic(media: bytes, mime: str) -> None:
    if not isinstance(media, bytes):
        raise TypeError("invalid_video_data")
    if not media:
        raise ValueError("empty_video")
    if len(media) > MAX_VIDEO_BYTES:
        raise ValueError("video_too_large")
    if mime == "video/mp4":
        valid = len(media) >= 12 and media[4:8] == b"ftyp"
    else:
        valid = media.startswith(b"\x1aE\xdf\xa3")
    if not valid:
        raise ValueError("video_content_mismatch")


class MediaAssetStore:
    def create_video_asset(
        self,
        *,
        owner_identity_id: object,
        title: object,
        original_name: object,
        mime_type: object,
        media: bytes,
    ) -> dict[str, object]:
        owner = _uuid(owner_identity_id, "invalid_owner_identity")
        clean_title = _text(title, "invalid_media_title", 180)
        name = _text(original_name, "invalid_video_filename", 220)
        mime = _mime(mime_type)
        _validate_magic(media, mime)
        digest = hashlib.sha256(media).hexdigest()
        size = len(media)
        asset_id = str(uuid.uuid4())
        try:
            with postgres_db.connect() as connection:
                used_row = connection.execute(
                    """SELECT COALESCE(SUM(byte_size),0) FROM oap_media_assets
                       WHERE owner_identity_id=%s""",
                    (owner,),
                ).fetchone()
                used = int(used_row[0] or 0) if used_row else 0
                if used + size > MAX_OWNER_STORAGE_BYTES:
                    raise ValueError("media_storage_quota_reached")
                row = connection.execute(
                    """INSERT INTO oap_media_assets(
                           asset_id,owner_identity_id,title,media_kind,original_name,
                           mime_type,byte_size,sha256,media)
                       VALUES (%s,%s,%s,'video',%s,%s,%s,%s,%s)
                       RETURNING asset_id,created_at""",
                    (asset_id, owner, clean_title, name, mime, size, digest, media),
                ).fetchone()
                connection.commit()
        except ValueError:
            raise
        except Exception as exc:
            raise MediaAssetUnavailable("media_asset_store_failed") from exc
        return {
            "asset_id": str(row[0]),
            "content_id": f"oap:media:{row[0]}",
            "title": clean_title,
            "media_kind": "video",
            "original_name": name,
            "mime_type": mime,
            "byte_size": size,
            "sha256": digest,
            "created_at": row[1].isoformat(),
            "playback_scope": "OWNER_PRIVATE_REVIEW",
            "public_playback_enabled": False,
            "rights_allow_required": True,
            "entitlement_required": True,
            "stopped": False,
        }

    def read(
        self, *, owner_identity_id: object, asset_id: object
    ) -> tuple[bytes, str, str, str, bool] | None:
        owner = _uuid(owner_identity_id, "invalid_owner_identity")
        asset = _uuid(asset_id, "invalid_asset_id")
        try:
            with postgres_db.connect(readonly=True) as connection:
                row = connection.execute(
                    """SELECT media,mime_type,sha256,original_name,stopped
                       FROM oap_media_assets
                       WHERE asset_id=%s AND owner_identity_id=%s
                       LIMIT 1""",
                    (asset, owner),
                ).fetchone()
        except Exception as exc:
            raise MediaAssetUnavailable("media_asset_read_failed") from exc
        if row is None:
            return None
        data = bytes(row[0])
        digest = hashlib.sha256(data).hexdigest()
        if digest != str(row[2]):
            raise MediaAssetUnavailable("media_asset_integrity_failed")
        return data, str(row[1]), digest, str(row[3]), bool(row[4])

    def list_assets(self, *, owner_identity_id: object) -> list[dict[str, object]]:
        owner = _uuid(owner_identity_id, "invalid_owner_identity")
        try:
            with postgres_db.connect(readonly=True) as connection:
                rows = connection.execute(
                    """SELECT asset_id,title,original_name,mime_type,byte_size,sha256,
                              stopped,created_at,stopped_at
                       FROM oap_media_assets
                       WHERE owner_identity_id=%s
                       ORDER BY created_at DESC LIMIT 200""",
                    (owner,),
                ).fetchall()
        except Exception as exc:
            raise MediaAssetUnavailable("media_asset_list_failed") from exc
        return [
            {
                "asset_id": str(row[0]),
                "content_id": f"oap:media:{row[0]}",
                "title": str(row[1]),
                "original_name": str(row[2]),
                "mime_type": str(row[3]),
                "byte_size": int(row[4]),
                "sha256": str(row[5]),
                "stopped": bool(row[6]),
                "created_at": row[7].isoformat(),
                "stopped_at": row[8].isoformat() if row[8] else None,
                "playback_scope": "OWNER_PRIVATE_REVIEW",
                "public_playback_enabled": False,
            }
            for row in rows
        ]

    def stop(self, *, owner_identity_id: object, asset_id: object) -> dict[str, object]:
        owner = _uuid(owner_identity_id, "invalid_owner_identity")
        asset = _uuid(asset_id, "invalid_asset_id")
        try:
            with postgres_db.connect() as connection:
                row = connection.execute(
                    """UPDATE oap_media_assets
                       SET stopped=TRUE, stopped_at=COALESCE(stopped_at,CURRENT_TIMESTAMP)
                       WHERE asset_id=%s AND owner_identity_id=%s
                       RETURNING asset_id,stopped,stopped_at""",
                    (asset, owner),
                ).fetchone()
                connection.commit()
        except Exception as exc:
            raise MediaAssetUnavailable("media_asset_stop_failed") from exc
        if row is None:
            raise PermissionError("media_asset_not_owned")
        return {
            "asset_id": str(row[0]),
            "content_id": f"oap:media:{row[0]}",
            "stopped": bool(row[1]),
            "stopped_at": row[2].isoformat() if row[2] else None,
            "media_delivery_enabled": False,
            "human_authority_final": True,
        }
