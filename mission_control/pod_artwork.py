"""Owner-scoped POD artwork bytes; no supplier execution or public publishing."""
from __future__ import annotations

import hashlib
import uuid

from . import postgres_db

MAX_ARTWORK_BYTES = 5 * 1024 * 1024
ALLOWED_TYPES = {"image/png": "png", "image/jpeg": "jpeg", "image/webp": "webp"}
SCHEMA = """
CREATE TABLE IF NOT EXISTS oap_pod_artwork (
 asset_id UUID PRIMARY KEY,
 owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 filename TEXT NOT NULL,
 mime_type TEXT NOT NULL,
 byte_size INTEGER NOT NULL CHECK(byte_size BETWEEN 1 AND 5242880),
 sha256 CHAR(64) NOT NULL,
 media BYTEA NOT NULL,
 created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_pod_artwork_owner ON oap_pod_artwork(owner_identity_id,created_at DESC);
"""


def validate_image(media: bytes, mime_type: str) -> None:
    if mime_type not in ALLOWED_TYPES:
        raise ValueError("pod_artwork_type_invalid")
    if not isinstance(media, bytes) or not 1 <= len(media) <= MAX_ARTWORK_BYTES:
        raise ValueError("pod_artwork_size_invalid")
    valid = (
        (mime_type == "image/png" and media.startswith(b"\\x89PNG\\r\\n\\x1a\\n"))
        or (mime_type == "image/jpeg" and media.startswith(b"\\xff\\xd8\\xff"))
        or (mime_type == "image/webp" and len(media) >= 12
            and media[:4] == b"RIFF" and media[8:12] == b"WEBP")
    )
    if not valid:
        raise ValueError("pod_artwork_content_mismatch")


def save(*, owner_identity_id: str, filename: str, mime_type: str, media: bytes) -> str:
    owner = str(uuid.UUID(str(owner_identity_id)))
    validate_image(media, mime_type)
    if not filename or len(filename) > 220:
        raise ValueError("pod_artwork_filename_invalid")
    asset_id = str(uuid.uuid4())
    with postgres_db.connect() as conn:
        conn.execute(
            """INSERT INTO oap_pod_artwork
              (asset_id,owner_identity_id,filename,mime_type,byte_size,sha256,media)
              VALUES (%s,%s,%s,%s,%s,%s,%s)""",
            (asset_id, owner, filename, mime_type, len(media),
             hashlib.sha256(media).hexdigest(), media),
        )
        conn.commit()
    return "oap-pod-artwork:" + asset_id


def load(*, owner_identity_id: str, asset_id: str) -> tuple[str, bytes] | None:
    owner = str(uuid.UUID(str(owner_identity_id)))
    asset = str(uuid.UUID(str(asset_id)))
    with postgres_db.connect(readonly=True) as conn:
        row = conn.execute(
            "SELECT mime_type,media FROM oap_pod_artwork WHERE owner_identity_id=%s AND asset_id=%s",
            (owner, asset),
        ).fetchone()
    return (str(row[0]), bytes(row[1])) if row else None
