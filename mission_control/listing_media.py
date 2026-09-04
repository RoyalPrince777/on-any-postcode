"""First-party photo storage for OAP Direct listings.

Listing photos are stored in OAP's PostgreSQL data layer so public listing media
does not depend on a third-party image host. A photo may only be attached by the
listing owner after explicitly confirming they own or are authorised to use it.
No migration runs at import/startup time.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
from collections.abc import Iterable
from typing import Any
from uuid import UUID

from . import postgres_db

LISTING_MEDIA_MIGRATION_VERSION = "0009_oap_supply_listing_photos"
LISTING_MEDIA_REVISION = "2026-09-04-v1"
LISTING_MEDIA_TABLE = "oap_supply_listing_photos"
MAX_IMAGE_BYTES = 2 * 1024 * 1024
MAX_PHOTOS_PER_LISTING = 8
_ALLOWED_TYPES = frozenset({"image/jpeg", "image/png", "image/webp"})

LISTING_MEDIA_SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_supply_listing_photos (
        photo_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        listing_id UUID NOT NULL REFERENCES oap_supply_listings(listing_id)
            ON DELETE CASCADE,
        content_type TEXT NOT NULL
            CHECK (content_type IN ('image/jpeg','image/png','image/webp')),
        image_bytes BYTEA NOT NULL,
        byte_size INTEGER NOT NULL CHECK (byte_size BETWEEN 1 AND 2097152),
        sha256 TEXT NOT NULL CHECK (length(sha256)=64),
        alt_text TEXT NOT NULL DEFAULT '',
        display_order INTEGER NOT NULL DEFAULT 0
            CHECK (display_order BETWEEN 0 AND 99),
        rights_confirmed BOOLEAN NOT NULL DEFAULT TRUE
            CHECK (rights_confirmed),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CHECK (octet_length(image_bytes)=byte_size),
        UNIQUE(listing_id,sha256))""",
    """CREATE INDEX IF NOT EXISTS ix_supply_listing_photos_order
        ON oap_supply_listing_photos(listing_id,display_order,created_at)""",
)
LISTING_MEDIA_MIGRATION_CHECKSUM = hashlib.sha256(
    "\n".join(LISTING_MEDIA_SCHEMA_STATEMENTS).encode()
).hexdigest()


def _uuid(value: object, name: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"invalid_{name}") from exc


def _alt_text(value: object) -> str:
    text = " ".join(str(value or "").strip().split())
    if len(text) > 240:
        raise ValueError("alt_text_too_long")
    return text


def _display_order(value: object) -> int:
    try:
        order = int(value or 0)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid_display_order") from exc
    if not 0 <= order <= 99:
        raise ValueError("invalid_display_order")
    return order


def _decode_data_url(value: object) -> tuple[str, bytes]:
    raw = str(value or "").strip()
    if not raw.startswith("data:") or ";base64," not in raw:
        raise ValueError("image_data_url_required")
    header, encoded = raw.split(",", 1)
    content_type = header[5:].split(";", 1)[0].casefold()
    if content_type not in _ALLOWED_TYPES:
        raise ValueError("unsupported_listing_photo_type")
    try:
        data = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("invalid_listing_photo_base64") from exc
    if not data or len(data) > MAX_IMAGE_BYTES:
        raise ValueError("listing_photo_must_be_1_to_2mb")
    if content_type == "image/jpeg" and not data.startswith(b"\xff\xd8\xff"):
        raise ValueError("listing_photo_signature_mismatch")
    if content_type == "image/png" and not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("listing_photo_signature_mismatch")
    if content_type == "image/webp" and not (
        len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP"
    ):
        raise ValueError("listing_photo_signature_mismatch")
    return content_type, data


def schema_status() -> dict[str, Any]:
    result: dict[str, Any] = {
        "migration": LISTING_MEDIA_MIGRATION_VERSION,
        "checksum": LISTING_MEDIA_MIGRATION_CHECKSUM,
        "schema_ready": False,
        "table_ready": False,
        "error": None,
    }
    if not postgres_db.postgres_status().get("initialized"):
        result["error"] = "base_postgres_not_ready"
        return result
    try:
        with postgres_db.connect(readonly=True) as connection:
            table = connection.execute(
                """SELECT 1 FROM information_schema.tables
                   WHERE table_schema='public' AND table_name=%s""",
                (LISTING_MEDIA_TABLE,),
            ).fetchone()
            result["table_ready"] = table is not None
            if table is None:
                result["error"] = "listing_media_schema_pending"
                return result
            migration = connection.execute(
                "SELECT checksum FROM oap_schema_migrations WHERE version=%s",
                (LISTING_MEDIA_MIGRATION_VERSION,),
            ).fetchone()
            if migration is None or str(migration[0]) != LISTING_MEDIA_MIGRATION_CHECKSUM:
                result["error"] = "listing_media_migration_not_verified"
                return result
            result["schema_ready"] = True
            return result
    except Exception:  # noqa: BLE001
        result["error"] = "listing_media_store_unavailable"
        return result


def init_schema(*, assume_yes: bool = False, dry_run: bool = False) -> dict[str, Any]:
    if not assume_yes:
        raise RuntimeError("Explicit human approval required: pass --yes")
    if dry_run:
        return {
            "dry_run": True,
            "migration": LISTING_MEDIA_MIGRATION_VERSION,
            "checksum": LISTING_MEDIA_MIGRATION_CHECKSUM,
            "tables": 1,
        }
    with postgres_db.connect() as connection:
        connection.execute("SELECT pg_advisory_xact_lock(%s)", (25800009,))
        row = connection.execute(
            "SELECT checksum FROM oap_schema_migrations WHERE version=%s",
            (LISTING_MEDIA_MIGRATION_VERSION,),
        ).fetchone()
        if row is not None and str(row[0]) != LISTING_MEDIA_MIGRATION_CHECKSUM:
            raise RuntimeError("Applied listing-media migration checksum mismatch")
        if row is None:
            for statement in LISTING_MEDIA_SCHEMA_STATEMENTS:
                connection.execute(statement)
            connection.execute(
                "INSERT INTO oap_schema_migrations(version,checksum) VALUES (%s,%s)",
                (LISTING_MEDIA_MIGRATION_VERSION, LISTING_MEDIA_MIGRATION_CHECKSUM),
            )
        connection.commit()
    return schema_status()


def add_photo(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("rights_confirmed") is not True:
        raise PermissionError("listing_photo_rights_confirmation_required")
    if not schema_status().get("schema_ready"):
        raise RuntimeError("listing_media_schema_not_ready")
    owner = _uuid(payload.get("owner_identity_id"), "owner_identity_id")
    listing = _uuid(payload.get("listing_id"), "listing_id")
    content_type, image = _decode_data_url(payload.get("image_data"))
    alt = _alt_text(payload.get("alt_text"))
    order = _display_order(payload.get("display_order"))
    digest = hashlib.sha256(image).hexdigest()
    with postgres_db.connect() as connection:
        owned = connection.execute(
            """SELECT 1 FROM oap_supply_listings l
               JOIN oap_supply_suppliers s ON s.supplier_id=l.supplier_id
               WHERE l.listing_id=%s AND s.owner_identity_id=%s""",
            (listing, owner),
        ).fetchone()
        if owned is None:
            raise PermissionError("listing_not_owned")
        count = connection.execute(
            "SELECT COUNT(*) FROM oap_supply_listing_photos WHERE listing_id=%s",
            (listing,),
        ).fetchone()
        existing = connection.execute(
            """SELECT photo_id FROM oap_supply_listing_photos
               WHERE listing_id=%s AND sha256=%s""",
            (listing, digest),
        ).fetchone()
        if existing is None and int(count[0] if count else 0) >= MAX_PHOTOS_PER_LISTING:
            raise ValueError("listing_photo_limit_reached")
        row = connection.execute(
            """INSERT INTO oap_supply_listing_photos
               (listing_id,content_type,image_bytes,byte_size,sha256,alt_text,
                display_order,rights_confirmed)
               VALUES (%s,%s,%s,%s,%s,%s,%s,TRUE)
               ON CONFLICT (listing_id,sha256) DO UPDATE SET
                 alt_text=EXCLUDED.alt_text,display_order=EXCLUDED.display_order,
                 updated_at=CURRENT_TIMESTAMP
               RETURNING photo_id,content_type,byte_size,sha256,alt_text,display_order""",
            (listing, content_type, image, len(image), digest, alt, order),
        ).fetchone()
        connection.commit()
    return {
        "photo_id": str(row[0]),
        "listing_id": listing,
        "content_type": str(row[1]),
        "byte_size": int(row[2]),
        "sha256": str(row[3]),
        "alt_text": str(row[4]),
        "display_order": int(row[5]),
        "rights_confirmed": True,
        "public_path": f"/travel/direct/photos/{row[0]}",
    }


def photo_map(listing_ids: Iterable[str]) -> dict[str, list[dict[str, Any]]]:
    ids = tuple(dict.fromkeys(str(item) for item in listing_ids if item))
    if not ids or not schema_status().get("schema_ready"):
        return {}
    placeholders = ",".join(["%s"] * len(ids))
    with postgres_db.connect(readonly=True) as connection:
        rows = connection.execute(
            f"""SELECT photo_id,listing_id,alt_text,display_order,content_type,byte_size
                FROM oap_supply_listing_photos
                WHERE listing_id IN ({placeholders})
                ORDER BY listing_id,display_order,created_at""",
            ids,
        ).fetchall()
    result: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        listing_id = str(row[1])
        result.setdefault(listing_id, []).append(
            {
                "photo_id": str(row[0]),
                "alt_text": str(row[2]),
                "display_order": int(row[3]),
                "content_type": str(row[4]),
                "byte_size": int(row[5]),
                "public_path": f"/travel/direct/photos/{row[0]}",
            }
        )
    return result


def public_photo(photo_id: object) -> tuple[bytes, str, str] | None:
    if not schema_status().get("schema_ready"):
        return None
    photo = _uuid(photo_id, "photo_id")
    with postgres_db.connect(readonly=True) as connection:
        row = connection.execute(
            """SELECT p.image_bytes,p.content_type,p.sha256
               FROM oap_supply_listing_photos p
               JOIN oap_supply_listings l ON l.listing_id=p.listing_id
               JOIN oap_supply_suppliers s ON s.supplier_id=l.supplier_id
               WHERE p.photo_id=%s AND l.state='ACTIVE'
                 AND s.state='CERTIFIED' AND s.commercial_terms_state='CERTIFIED'
               LIMIT 1""",
            (photo,),
        ).fetchone()
    if row is None:
        return None
    return bytes(row[0]), str(row[1]), str(row[2])


def status() -> dict[str, Any]:
    schema = schema_status()
    count = 0
    if schema.get("schema_ready"):
        try:
            with postgres_db.connect(readonly=True) as connection:
                row = connection.execute(
                    "SELECT COUNT(*) FROM oap_supply_listing_photos"
                ).fetchone()
            count = int(row[0] if row else 0)
        except Exception:  # noqa: BLE001
            schema["error"] = "listing_media_count_failed"
    return {
        "component": "OAP Direct Listing Photos",
        "revision": LISTING_MEDIA_REVISION,
        "schema": schema,
        "schema_ready": bool(schema.get("schema_ready")),
        "photo_count": count,
        "max_image_bytes": MAX_IMAGE_BYTES,
        "max_photos_per_listing": MAX_PHOTOS_PER_LISTING,
        "allowed_content_types": tuple(sorted(_ALLOWED_TYPES)),
        "first_party_storage": True,
        "rights_confirmation_required": True,
        "external_image_host_required": False,
        "human_authority_final": True,
    }
