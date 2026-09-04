"""First-party OAP Direct listing media.

Listing pictures are stored inside OAP's PostgreSQL supply core. This module does
not import provider photography, does not use an external CDN, and does not add
provider authority. Media writes are Founder-triggered and listings remain owned
by their Certified OAP supplier.
"""
from __future__ import annotations

import hashlib
from typing import Any

from . import postgres_db

LISTING_MEDIA_MIGRATION_VERSION = "0009_oap_supply_listing_media"
LISTING_MEDIA_REVISION = "2026-09-04-v1"
LISTING_MEDIA_TABLE = "oap_supply_listing_media"
MAX_IMAGES_PER_LISTING = 8
MAX_IMAGE_BYTES = 5 * 1024 * 1024
ALLOWED_IMAGE_MIME_TYPES = frozenset({"image/jpeg", "image/png", "image/webp"})

LISTING_MEDIA_SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_supply_listing_media (
        media_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        listing_id UUID NOT NULL REFERENCES oap_supply_listings(listing_id)
            ON DELETE CASCADE,
        mime_type TEXT NOT NULL CHECK (mime_type IN ('image/jpeg','image/png','image/webp')),
        original_name TEXT NOT NULL,
        alt_text TEXT NOT NULL DEFAULT '',
        content_bytes BYTEA NOT NULL,
        content_sha256 TEXT NOT NULL,
        position INTEGER NOT NULL CHECK (position >= 0 AND position < 8),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CHECK (octet_length(content_bytes) > 0 AND octet_length(content_bytes) <= 5242880),
        UNIQUE(listing_id, position),
        UNIQUE(listing_id, content_sha256))""",
    """CREATE INDEX IF NOT EXISTS ix_supply_listing_media_listing
        ON oap_supply_listing_media(listing_id, position, created_at)""",
)
LISTING_MEDIA_MIGRATION_CHECKSUM = hashlib.sha256(
    "\n".join(LISTING_MEDIA_SCHEMA_STATEMENTS).encode()
).hexdigest()


def schema_status() -> dict[str, Any]:
    result: dict[str, Any] = {
        "migration": LISTING_MEDIA_MIGRATION_VERSION,
        "checksum": LISTING_MEDIA_MIGRATION_CHECKSUM,
        "schema_ready": False,
        "table_ready": False,
        "max_images_per_listing": MAX_IMAGES_PER_LISTING,
        "max_image_bytes": MAX_IMAGE_BYTES,
        "allowed_mime_types": tuple(sorted(ALLOWED_IMAGE_MIME_TYPES)),
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
            row = connection.execute(
                "SELECT checksum FROM oap_schema_migrations WHERE version=%s",
                (LISTING_MEDIA_MIGRATION_VERSION,),
            ).fetchone()
            if row is None or str(row[0]) != LISTING_MEDIA_MIGRATION_CHECKSUM:
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
    if not postgres_db.postgres_status().get("initialized"):
        raise RuntimeError("Base PostgreSQL schema must be ready first")
    if dry_run:
        return {
            "dry_run": True,
            "migration": LISTING_MEDIA_MIGRATION_VERSION,
            "checksum": LISTING_MEDIA_MIGRATION_CHECKSUM,
            "statements": len(LISTING_MEDIA_SCHEMA_STATEMENTS),
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


def _clean_text(value: object, maximum: int) -> str:
    return " ".join(str(value or "").strip().split())[:maximum]


def _owned_listing(connection, *, listing_id: object, owner_identity_id: object):
    row = connection.execute(
        """SELECT l.listing_id,l.title,p.owner_identity_id
           FROM oap_supply_listings l
           JOIN oap_supply_suppliers p ON p.supplier_id=l.supplier_id
           WHERE l.listing_id=%s""",
        (str(listing_id or "").strip(),),
    ).fetchone()
    if row is None:
        raise ValueError("listing_not_found")
    if str(row[2]) != str(owner_identity_id or "").strip():
        raise PermissionError("listing_owner_required")
    return row


def add_image(
    *,
    owner_identity_id: object,
    listing_id: object,
    mime_type: object,
    original_name: object,
    content: bytes,
    alt_text: object = "",
) -> dict[str, Any]:
    """Add one real listing image after validating ownership and media bounds."""

    if not schema_status().get("schema_ready"):
        raise RuntimeError("listing_media_schema_not_ready")
    mime = str(mime_type or "").strip().casefold()
    if mime not in ALLOWED_IMAGE_MIME_TYPES:
        raise ValueError("unsupported_listing_image_type")
    if not isinstance(content, bytes) or not content:
        raise ValueError("listing_image_required")
    if len(content) > MAX_IMAGE_BYTES:
        raise ValueError("listing_image_too_large")
    name = _clean_text(original_name, 180) or "listing-image"
    alt = _clean_text(alt_text, 240)
    digest = hashlib.sha256(content).hexdigest()

    with postgres_db.connect() as connection:
        listing = _owned_listing(
            connection,
            listing_id=listing_id,
            owner_identity_id=owner_identity_id,
        )
        rows = connection.execute(
            """SELECT position FROM oap_supply_listing_media
               WHERE listing_id=%s ORDER BY position""",
            (str(listing[0]),),
        ).fetchall()
        used = {int(row[0]) for row in rows}
        if len(used) >= MAX_IMAGES_PER_LISTING:
            raise ValueError("listing_image_limit_reached")
        position = next(index for index in range(MAX_IMAGES_PER_LISTING) if index not in used)
        row = connection.execute(
            """INSERT INTO oap_supply_listing_media
               (listing_id,mime_type,original_name,alt_text,content_bytes,content_sha256,position)
               VALUES (%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT(listing_id,content_sha256) DO UPDATE
               SET alt_text=EXCLUDED.alt_text,updated_at=CURRENT_TIMESTAMP
               RETURNING media_id,position,content_sha256""",
            (
                str(listing[0]),
                mime,
                name,
                alt,
                content,
                digest,
                position,
            ),
        ).fetchone()
        if row is None:
            raise RuntimeError("listing_image_write_failed")
        connection.commit()
    return {
        "media_id": str(row[0]),
        "listing_id": str(listing[0]),
        "listing_title": str(listing[1]),
        "position": int(row[1]),
        "content_sha256": str(row[2]),
        "mime_type": mime,
        "original_name": name,
        "alt_text": alt,
        "public_url": f"/travel/direct/media/{row[0]}",
        "provider_authority": False,
        "human_authority_final": True,
    }


def listing_media(listing_ids: list[str] | tuple[str, ...]) -> dict[str, list[dict[str, Any]]]:
    ids = tuple(dict.fromkeys(str(value) for value in listing_ids if value))
    if not ids or not schema_status().get("schema_ready"):
        return {}
    placeholders = ",".join(["%s"] * len(ids))
    query = f"""SELECT media_id,listing_id,mime_type,original_name,alt_text,
                       content_sha256,position
                FROM oap_supply_listing_media
                WHERE listing_id IN ({placeholders})
                ORDER BY listing_id,position,created_at"""
    with postgres_db.connect(readonly=True) as connection:
        rows = connection.execute(query, ids).fetchall()
    result: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        listing_id = str(row[1])
        result.setdefault(listing_id, []).append(
            {
                "media_id": str(row[0]),
                "listing_id": listing_id,
                "mime_type": str(row[2]),
                "original_name": str(row[3]),
                "alt_text": str(row[4]),
                "content_sha256": str(row[5]),
                "position": int(row[6]),
                "public_url": f"/travel/direct/media/{row[0]}",
            }
        )
    return result


def read_public_image(media_id: object) -> dict[str, Any]:
    if not schema_status().get("schema_ready"):
        raise RuntimeError("listing_media_schema_not_ready")
    with postgres_db.connect(readonly=True) as connection:
        row = connection.execute(
            """SELECT m.mime_type,m.original_name,m.alt_text,m.content_bytes,
                      m.content_sha256,m.updated_at,l.state,p.state,p.commercial_terms_state
               FROM oap_supply_listing_media m
               JOIN oap_supply_listings l ON l.listing_id=m.listing_id
               JOIN oap_supply_suppliers p ON p.supplier_id=l.supplier_id
               WHERE m.media_id=%s""",
            (str(media_id or "").strip(),),
        ).fetchone()
    if row is None:
        raise ValueError("listing_image_not_found")
    if str(row[6]) != "ACTIVE" or str(row[7]) != "CERTIFIED" or str(row[8]) != "CERTIFIED":
        raise PermissionError("listing_image_not_public")
    return {
        "mime_type": str(row[0]),
        "original_name": str(row[1]),
        "alt_text": str(row[2]),
        "content": bytes(row[3]),
        "content_sha256": str(row[4]),
        "updated_at": row[5].isoformat(),
    }


def status() -> dict[str, Any]:
    schema = schema_status()
    return {
        "component": "OAP Direct Listing Media",
        "revision": LISTING_MEDIA_REVISION,
        "schema": schema,
        "ready": schema["schema_ready"],
        "max_images_per_listing": MAX_IMAGES_PER_LISTING,
        "max_image_bytes": MAX_IMAGE_BYTES,
        "allowed_mime_types": tuple(sorted(ALLOWED_IMAGE_MIME_TYPES)),
        "external_cdn_required": False,
        "external_provider_photography_imported": False,
        "provider_authority": False,
        "human_authority_final": True,
    }
