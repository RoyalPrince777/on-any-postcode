"""First-party owner-scoped audio assets for OAP Music.

Audio bytes remain inside OAP Data. This module does not grant copyright,
publish a track, start a broadcast, distribute to an external DSP, or represent
SIKA as money.
"""
from __future__ import annotations

import hashlib
import uuid
from typing import Any

from . import postgres_db

MAX_AUDIO_BYTES = 6 * 1024 * 1024
MAX_OWNER_STORAGE_BYTES = 250 * 1024 * 1024
ALLOWED_MIME_TYPES = (
    "audio/mpeg",
    "audio/mp4",
    "audio/ogg",
    "audio/webm",
    "audio/wav",
    "audio/x-wav",
)

SCHEMA_SQL = (
    """CREATE TABLE IF NOT EXISTS oap_music_assets (
        asset_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        release_id UUID NOT NULL REFERENCES oap_music_releases(release_id)
            ON DELETE CASCADE,
        track_id UUID UNIQUE REFERENCES oap_music_tracks(track_id)
            ON DELETE CASCADE,
        original_name TEXT NOT NULL,
        mime_type TEXT NOT NULL,
        byte_size INTEGER NOT NULL CHECK (byte_size > 0 AND byte_size <= 6291456),
        sha256 CHAR(64) NOT NULL,
        media BYTEA NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE INDEX IF NOT EXISTS ix_music_asset_owner_created
       ON oap_music_assets(owner_identity_id,created_at DESC)""",
    """CREATE INDEX IF NOT EXISTS ix_music_asset_release
       ON oap_music_assets(release_id,created_at)""",
)


class MusicAssetUnavailable(RuntimeError):
    pass


def _uuid(value: object, code: str) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(code) from exc


def _name(value: object) -> str:
    text = " ".join(str(value or "").strip().split())
    if not text or len(text) > 220:
        raise ValueError("invalid_audio_filename")
    return text


def _mime(value: object) -> str:
    mime = str(value or "").split(";", 1)[0].strip().casefold()
    if mime not in ALLOWED_MIME_TYPES:
        raise ValueError("unsupported_audio_type")
    return mime


def _validate_magic(media: bytes, mime: str) -> None:
    if not isinstance(media, bytes):
        raise TypeError("invalid_audio_data")
    if not media:
        raise ValueError("empty_audio")
    if len(media) > MAX_AUDIO_BYTES:
        raise ValueError("audio_too_large")

    valid = False
    if mime == "audio/mpeg":
        valid = media.startswith(b"ID3") or (
            len(media) >= 2 and media[0] == 0xFF and media[1] & 0xE0 == 0xE0
        )
    elif mime == "audio/ogg":
        valid = media.startswith(b"OggS")
    elif mime == "audio/webm":
        valid = media.startswith(b"\x1aE\xdf\xa3")
    elif mime == "audio/mp4":
        valid = len(media) >= 12 and media[4:8] == b"ftyp"
    elif mime in {"audio/wav", "audio/x-wav"}:
        valid = (
            len(media) >= 12
            and media.startswith(b"RIFF")
            and media[8:12] == b"WAVE"
        )
    if not valid:
        raise ValueError("audio_content_mismatch")


class MusicAssetStore:
    def ensure_schema(self) -> None:
        try:
            with postgres_db.connect() as connection:
                for statement in SCHEMA_SQL:
                    connection.execute(statement)
                connection.commit()
        except Exception as exc:
            raise MusicAssetUnavailable("music_asset_schema_failed") from exc

    def create(
        self,
        *,
        owner_identity_id: object,
        release_id: object,
        original_name: object,
        mime_type: object,
        media: bytes,
    ) -> dict[str, object]:
        owner = _uuid(owner_identity_id, "invalid_owner_identity")
        release = _uuid(release_id, "invalid_release_id")
        name = _name(original_name)
        mime = _mime(mime_type)
        _validate_magic(media, mime)
        digest = hashlib.sha256(media).hexdigest()
        size = len(media)
        self.ensure_schema()
        try:
            with postgres_db.connect() as connection:
                owned = connection.execute(
                    """SELECT 1 FROM oap_music_releases
                       WHERE release_id=%s AND owner_identity_id=%s
                         AND state IN ('DRAFT','REVIEW_REQUIRED')
                       FOR UPDATE""",
                    (release, owner),
                ).fetchone()
                if owned is None:
                    raise PermissionError("music_release_not_owned_or_editable")
                used_row = connection.execute(
                    """SELECT COALESCE(SUM(byte_size),0) FROM oap_music_assets
                       WHERE owner_identity_id=%s""",
                    (owner,),
                ).fetchone()
                used = int(used_row[0] or 0) if used_row else 0
                if used + size > MAX_OWNER_STORAGE_BYTES:
                    raise ValueError("music_storage_quota_reached")
                row = connection.execute(
                    """INSERT INTO oap_music_assets(
                           owner_identity_id,release_id,original_name,mime_type,
                           byte_size,sha256,media)
                       VALUES (%s,%s,%s,%s,%s,%s,%s)
                       RETURNING asset_id,created_at""",
                    (owner, release, name, mime, size, digest, media),
                ).fetchone()
                connection.commit()
        except (PermissionError, ValueError):
            raise
        except Exception as exc:
            raise MusicAssetUnavailable("music_asset_store_failed") from exc
        return {
            "asset_id": str(row[0]),
            "release_id": release,
            "original_name": name,
            "mime_type": mime,
            "byte_size": size,
            "sha256": digest,
            "created_at": row[1].isoformat(),
            "playback_scope": "OWNER_PRIVATE",
        }

    def bind_track(
        self, *, owner_identity_id: object, asset_id: object, track_id: object
    ) -> dict[str, object]:
        owner = _uuid(owner_identity_id, "invalid_owner_identity")
        asset = _uuid(asset_id, "invalid_asset_id")
        track = _uuid(track_id, "invalid_track_id")
        try:
            with postgres_db.connect() as connection:
                row = connection.execute(
                    """UPDATE oap_music_assets a
                       SET track_id=%s
                       FROM oap_music_tracks t
                       JOIN oap_music_releases r ON r.release_id=t.release_id
                       WHERE a.asset_id=%s
                         AND a.owner_identity_id=%s
                         AND t.track_id=%s
                         AND r.owner_identity_id=%s
                         AND a.release_id=r.release_id
                       RETURNING a.asset_id,a.track_id""",
                    (track, asset, owner, track, owner),
                ).fetchone()
                if row is None:
                    raise PermissionError("music_asset_or_track_not_owned")
                connection.commit()
        except PermissionError:
            raise
        except Exception as exc:
            raise MusicAssetUnavailable("music_asset_bind_failed") from exc
        return {"asset_id": str(row[0]), "track_id": str(row[1])}

    def delete(self, *, owner_identity_id: object, asset_id: object) -> bool:
        owner = _uuid(owner_identity_id, "invalid_owner_identity")
        asset = _uuid(asset_id, "invalid_asset_id")
        try:
            with postgres_db.connect() as connection:
                row = connection.execute(
                    """DELETE FROM oap_music_assets
                       WHERE asset_id=%s AND owner_identity_id=%s
                       RETURNING asset_id""",
                    (asset, owner),
                ).fetchone()
                connection.commit()
        except Exception as exc:
            raise MusicAssetUnavailable("music_asset_delete_failed") from exc
        return row is not None

    def read(
        self, *, owner_identity_id: object, asset_id: object
    ) -> tuple[bytes, str, str, str] | None:
        owner = _uuid(owner_identity_id, "invalid_owner_identity")
        asset = _uuid(asset_id, "invalid_asset_id")
        try:
            with postgres_db.connect(readonly=True) as connection:
                row = connection.execute(
                    """SELECT media,mime_type,sha256,original_name
                       FROM oap_music_assets
                       WHERE asset_id=%s AND owner_identity_id=%s
                       LIMIT 1""",
                    (asset, owner),
                ).fetchone()
        except Exception as exc:
            raise MusicAssetUnavailable("music_asset_read_failed") from exc
        if row is None:
            return None
        data = bytes(row[0])
        digest = hashlib.sha256(data).hexdigest()
        if digest != str(row[2]):
            raise MusicAssetUnavailable("music_asset_integrity_failed")
        return data, str(row[1]), digest, str(row[3])

    def list_assets(self, *, owner_identity_id: object) -> list[dict[str, object]]:
        owner = _uuid(owner_identity_id, "invalid_owner_identity")
        self.ensure_schema()
        try:
            with postgres_db.connect(readonly=True) as connection:
                rows = connection.execute(
                    """SELECT asset_id,release_id,track_id,original_name,mime_type,
                              byte_size,sha256,created_at
                       FROM oap_music_assets
                       WHERE owner_identity_id=%s
                       ORDER BY created_at DESC LIMIT 200""",
                    (owner,),
                ).fetchall()
        except Exception as exc:
            raise MusicAssetUnavailable("music_asset_list_failed") from exc
        return [
            {
                "asset_id": str(row[0]),
                "release_id": str(row[1]),
                "track_id": str(row[2]) if row[2] is not None else None,
                "original_name": str(row[3]),
                "mime_type": str(row[4]),
                "byte_size": int(row[5]),
                "sha256": str(row[6]),
                "created_at": row[7].isoformat(),
                "playback_scope": "OWNER_PRIVATE",
            }
            for row in rows
        ]
