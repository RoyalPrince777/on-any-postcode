"""First-party owner-scoped audio assets for OAP Music.

Audio bytes remain inside OAP Data. Schema creation is performed only by the
explicit governed product-core migration. This module never grants copyright,
publishes a track, starts a broadcast, distributes to an external DSP, or
represents SIKA as money.
"""
from __future__ import annotations

import hashlib
import uuid

from . import postgres_db

MUSIC_ASSET_MIGRATION_VERSION = "0013_oap_music_assets"
SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_music_assets (
        asset_id UUID PRIMARY KEY,
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        release_id UUID NOT NULL REFERENCES oap_music_releases(release_id)
            ON DELETE CASCADE,
        track_id UUID NOT NULL UNIQUE REFERENCES oap_music_tracks(track_id)
            ON DELETE CASCADE,
        original_name TEXT NOT NULL,
        mime_type TEXT NOT NULL,
        byte_size INTEGER NOT NULL CHECK (byte_size > 0 AND byte_size <= 6291456),
        sha256 CHAR(64) NOT NULL,
        media BYTEA NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE INDEX IF NOT EXISTS ix_music_asset_owner_created
       ON oap_music_assets(owner_identity_id, created_at DESC)""",
    """CREATE INDEX IF NOT EXISTS ix_music_asset_release
       ON oap_music_assets(release_id, created_at)""",
)

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


def _title(value: object) -> str:
    text = " ".join(str(value or "").strip().split())
    if not text or len(text) > 180:
        raise ValueError("invalid_track_title")
    return text


def _mime(value: object) -> str:
    mime = str(value or "").split(";", 1)[0].strip().casefold()
    if mime not in ALLOWED_MIME_TYPES:
        raise ValueError("unsupported_audio_type")
    return mime


def _position(value: object) -> int:
    try:
        position = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid_track_position") from exc
    if not 1 <= position <= 99:
        raise ValueError("invalid_track_position")
    return position


def _duration(value: object) -> int | None:
    if value in (None, ""):
        return None
    try:
        duration = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid_duration_ms") from exc
    if not 1000 <= duration <= 7_200_000:
        raise ValueError("invalid_duration_ms")
    return duration


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
    def create_track_asset(
        self,
        *,
        owner_identity_id: object,
        release_id: object,
        title: object,
        position: object,
        original_name: object,
        mime_type: object,
        media: bytes,
        duration_ms: object = None,
        explicit: bool = False,
    ) -> tuple[dict[str, object], dict[str, object]]:
        """Atomically persist one audio asset and its canonical music track."""

        owner = _uuid(owner_identity_id, "invalid_owner_identity")
        release = _uuid(release_id, "invalid_release_id")
        name = _name(original_name)
        track_title = _title(title)
        track_position = _position(position)
        duration = _duration(duration_ms)
        mime = _mime(mime_type)
        _validate_magic(media, mime)
        digest = hashlib.sha256(media).hexdigest()
        size = len(media)
        asset_id = str(uuid.uuid4())

        try:
            with postgres_db.connect() as connection:
                owned = connection.execute(
                    """SELECT state FROM oap_music_releases
                       WHERE release_id=%s AND owner_identity_id=%s
                       FOR UPDATE""",
                    (release, owner),
                ).fetchone()
                if owned is None:
                    raise PermissionError("music_release_not_owned")
                if str(owned[0]) not in {"DRAFT", "REVIEW_REQUIRED"}:
                    raise ValueError("release_not_editable")

                used_row = connection.execute(
                    """SELECT COALESCE(SUM(byte_size),0) FROM oap_music_assets
                       WHERE owner_identity_id=%s""",
                    (owner,),
                ).fetchone()
                used = int(used_row[0] or 0) if used_row else 0
                if used + size > MAX_OWNER_STORAGE_BYTES:
                    raise ValueError("music_storage_quota_reached")

                track = connection.execute(
                    """INSERT INTO oap_music_tracks
                       (release_id,title,position,media_ref,duration_ms,explicit)
                       VALUES (%s,%s,%s,%s,%s,%s)
                       RETURNING track_id,title,position,created_at""",
                    (
                        release,
                        track_title,
                        track_position,
                        f"oap-music-asset:{asset_id}",
                        duration,
                        bool(explicit),
                    ),
                ).fetchone()
                asset = connection.execute(
                    """INSERT INTO oap_music_assets(
                           asset_id,owner_identity_id,release_id,track_id,
                           original_name,mime_type,byte_size,sha256,media)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                       RETURNING asset_id,created_at""",
                    (
                        asset_id,
                        owner,
                        release,
                        track[0],
                        name,
                        mime,
                        size,
                        digest,
                        media,
                    ),
                ).fetchone()
                connection.commit()
        except (PermissionError, ValueError):
            raise
        except Exception as exc:
            raise MusicAssetUnavailable("music_asset_store_failed") from exc

        asset_result = {
            "asset_id": str(asset[0]),
            "release_id": release,
            "track_id": str(track[0]),
            "original_name": name,
            "mime_type": mime,
            "byte_size": size,
            "sha256": digest,
            "created_at": asset[1].isoformat(),
            "playback_scope": "OWNER_PRIVATE",
        }
        track_result = {
            "track_id": str(track[0]),
            "title": str(track[1]),
            "position": int(track[2]),
            "created_at": track[3].isoformat(),
            "audio_delivery_enabled": False,
        }
        return asset_result, track_result

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
                "track_id": str(row[2]),
                "original_name": str(row[3]),
                "mime_type": str(row[4]),
                "byte_size": int(row[5]),
                "sha256": str(row[6]),
                "created_at": row[7].isoformat(),
                "playback_scope": "OWNER_PRIVATE",
            }
            for row in rows
        ]
