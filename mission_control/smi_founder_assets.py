"""Founder-only durable asset index for Personal SMI.

This index records secret-safe metadata about chat attachments and generated media so
Saved Work can reference what was used without retaining raw attachment bytes. Raw
media storage remains a separate, explicitly governed capability.

No migration runs at import time.
"""
from __future__ import annotations

import base64
import hashlib
import re
from typing import Any
from uuid import UUID

from . import postgres_db

ASSET_MIGRATION_VERSION = "0010_smi_founder_asset_index"
ASSET_REVISION = "2026-09-18-v1"
ASSET_TABLE = "smi_founder_assets"

ASSET_SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS smi_founder_assets (
        asset_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        identity_id UUID NOT NULL REFERENCES oap_identities(identity_id)
            ON DELETE CASCADE,
        conversation_id UUID NOT NULL REFERENCES smi_conversations(conversation_id)
            ON DELETE CASCADE,
        request_id UUID NOT NULL,
        source TEXT NOT NULL DEFAULT 'chat_attachment'
            CHECK (source IN ('chat_attachment','chat_image','studio_generation')),
        asset_kind TEXT NOT NULL
            CHECK (asset_kind IN ('image','audio','video','document','studio_image','studio_video')),
        filename TEXT NOT NULL,
        mime_type TEXT NOT NULL DEFAULT '',
        content_sha256 TEXT NOT NULL CHECK (length(content_sha256)=64),
        frame_count INTEGER NOT NULL DEFAULT 0 CHECK (frame_count BETWEEN 0 AND 16),
        raw_content_retained BOOLEAN NOT NULL DEFAULT FALSE
            CHECK (raw_content_retained=FALSE),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(identity_id,request_id,source,content_sha256))""",
    """CREATE INDEX IF NOT EXISTS ix_smi_founder_assets_identity_created
        ON smi_founder_assets(identity_id,created_at DESC)""",
    """CREATE INDEX IF NOT EXISTS ix_smi_founder_assets_conversation
        ON smi_founder_assets(identity_id,conversation_id,created_at DESC)""",
)
ASSET_MIGRATION_CHECKSUM = hashlib.sha256(
    "\n".join(ASSET_SCHEMA_STATEMENTS).encode()
).hexdigest()

_IMAGE_DATA = re.compile(
    r"^data:(image/(?:png|jpeg|webp|gif));base64,([A-Za-z0-9+/=]+)$",
    re.IGNORECASE,
)


def _uuid(value: object, name: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"invalid_{name}") from exc


def schema_status() -> dict[str, Any]:
    result: dict[str, Any] = {
        "component": "SMI Founder Asset Index",
        "revision": ASSET_REVISION,
        "migration": ASSET_MIGRATION_VERSION,
        "checksum": ASSET_MIGRATION_CHECKSUM,
        "schema_ready": False,
        "table_ready": False,
        "asset_count": 0,
        "studio_generated_asset_count": 0,
        "raw_content_retained": False,
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
                (ASSET_TABLE,),
            ).fetchone()
            result["table_ready"] = table is not None
            if table is None:
                result["error"] = "founder_asset_schema_pending"
                return result
            migration = connection.execute(
                "SELECT checksum FROM oap_schema_migrations WHERE version=%s",
                (ASSET_MIGRATION_VERSION,),
            ).fetchone()
            if migration is None or str(migration[0]) != ASSET_MIGRATION_CHECKSUM:
                result["error"] = "founder_asset_migration_not_verified"
                return result
            count = connection.execute(
                "SELECT COUNT(*) FROM smi_founder_assets"
            ).fetchone()
            generated = connection.execute(
                "SELECT COUNT(*) FROM smi_founder_assets WHERE source='studio_generation'"
            ).fetchone()
            result["asset_count"] = int(count[0] if count else 0)
            result["studio_generated_asset_count"] = int(generated[0] if generated else 0)
            result["schema_ready"] = True
            return result
    except Exception:  # noqa: BLE001 - readiness must fail closed.
        result["error"] = "founder_asset_store_unavailable"
        return result


def init_schema(*, assume_yes: bool = False, dry_run: bool = False) -> dict[str, Any]:
    if not assume_yes:
        raise RuntimeError("Explicit human approval required: pass --yes")
    if dry_run:
        return {
            "dry_run": True,
            "migration": ASSET_MIGRATION_VERSION,
            "checksum": ASSET_MIGRATION_CHECKSUM,
            "tables": 1,
            "raw_content_retained": False,
        }
    with postgres_db.connect() as connection:
        connection.execute("SELECT pg_advisory_xact_lock(%s)", (25800010,))
        row = connection.execute(
            "SELECT checksum FROM oap_schema_migrations WHERE version=%s",
            (ASSET_MIGRATION_VERSION,),
        ).fetchone()
        if row is not None and str(row[0]) != ASSET_MIGRATION_CHECKSUM:
            raise RuntimeError("Applied Founder asset migration checksum mismatch")
        if row is None:
            for statement in ASSET_SCHEMA_STATEMENTS:
                connection.execute(statement)
            connection.execute(
                "INSERT INTO oap_schema_migrations(version,checksum) VALUES (%s,%s)",
                (ASSET_MIGRATION_VERSION, ASSET_MIGRATION_CHECKSUM),
            )
        connection.commit()
    return schema_status()


def _table_available(connection: object) -> bool:
    row = connection.execute(
        """SELECT 1 FROM information_schema.tables
           WHERE table_schema='public' AND table_name=%s""",
        (ASSET_TABLE,),
    ).fetchone()
    return row is not None


def _image_meta(image_data: str, request_id: str) -> dict[str, Any] | None:
    match = _IMAGE_DATA.fullmatch(str(image_data or ""))
    if not match:
        return None
    mime = match.group(1).lower()
    digest = hashlib.sha256(str(image_data).encode()).hexdigest()
    suffix = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp", "image/gif": "gif"}[mime]
    return {
        "source": "chat_image",
        "kind": "image",
        "filename": f"smi-image-{request_id[:8]}.{suffix}",
        "mime": mime,
        "sha256": digest,
        "frame_count": 0,
    }


def record_chat_assets(
    connection: object,
    *,
    identity_id: object,
    conversation_id: object,
    request_id: object,
    image_data: object = "",
    media: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Index attachment metadata inside the same chat transaction.

    If the optional asset schema has not been applied yet, chat remains available
    and the result truthfully reports that indexing was skipped.
    """
    identity = _uuid(identity_id, "identity_id")
    conversation = _uuid(conversation_id, "conversation_id")
    request_value = _uuid(request_id, "request_id")
    if not _table_available(connection):
        return {
            "indexed": False,
            "asset_count": 0,
            "reason": "founder_asset_schema_pending",
            "raw_content_retained": False,
        }

    candidates: list[dict[str, Any]] = []
    image = _image_meta(str(image_data or ""), request_value)
    if image:
        candidates.append(image)

    media = media or {}
    if media.get("kind") and media.get("sha256"):
        candidates.append(
            {
                "source": "chat_attachment",
                "kind": str(media.get("kind")),
                "filename": str(media.get("filename") or "attachment")[:120],
                "mime": str(media.get("mime") or "")[:120],
                "sha256": str(media.get("sha256")),
                "frame_count": int(media.get("frame_count") or 0),
            }
        )

    asset_ids: list[str] = []
    for item in candidates:
        row = connection.execute(
            """INSERT INTO smi_founder_assets
               (identity_id,conversation_id,request_id,source,asset_kind,filename,
                mime_type,content_sha256,frame_count,raw_content_retained)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,FALSE)
               ON CONFLICT (identity_id,request_id,source,content_sha256)
               DO UPDATE SET filename=EXCLUDED.filename
               RETURNING asset_id""",
            (
                identity,
                conversation,
                request_value,
                item["source"],
                item["kind"],
                item["filename"],
                item["mime"],
                item["sha256"],
                item["frame_count"],
            ),
        ).fetchone()
        if row:
            asset_ids.append(str(row[0]))
    return {
        "indexed": bool(asset_ids),
        "asset_count": len(asset_ids),
        "asset_ids": tuple(asset_ids),
        "raw_content_retained": False,
    }



def record_studio_image_artifact(
    connection: object,
    *,
    identity_id: object,
    conversation_id: object,
    request_id: object,
    b64_json: object,
    mime_type: object = "image/png",
) -> dict[str, Any]:
    """Index one proven Studio image without retaining raw generated media."""
    identity = _uuid(identity_id, "identity_id")
    conversation = _uuid(conversation_id, "conversation_id")
    request_value = _uuid(request_id, "request_id")
    if not _table_available(connection):
        return {
            "indexed": False,
            "asset_count": 0,
            "reason": "founder_asset_schema_pending",
            "raw_content_retained": False,
        }
    owner = connection.execute(
        """SELECT 1 FROM smi_conversations
           WHERE conversation_id=%s AND identity_id=%s""",
        (conversation, identity),
    ).fetchone()
    if owner is None:
        raise ValueError("studio_conversation_not_owned")
    encoded = str(b64_json or "").strip()
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (ValueError, TypeError) as exc:
        raise ValueError("studio_image_artifact_invalid") from exc
    if not raw or len(raw) > 20 * 1024 * 1024:
        raise ValueError("studio_image_artifact_invalid")
    mime = str(mime_type or "image/png").strip().lower()
    if mime not in {"image/png", "image/jpeg", "image/webp"}:
        raise ValueError("studio_image_artifact_type_unsupported")
    suffix = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}[mime]
    digest = hashlib.sha256(raw).hexdigest()
    row = connection.execute(
        """INSERT INTO smi_founder_assets
           (identity_id,conversation_id,request_id,source,asset_kind,filename,
            mime_type,content_sha256,frame_count,raw_content_retained)
           VALUES (%s,%s,%s,'studio_generation','studio_image',%s,%s,%s,0,FALSE)
           ON CONFLICT (identity_id,request_id,source,content_sha256)
           DO UPDATE SET filename=EXCLUDED.filename
           RETURNING asset_id""",
        (
            identity,
            conversation,
            request_value,
            f"oap-studio-{request_value[:8]}.{suffix}",
            mime,
            digest,
        ),
    ).fetchone()
    return {
        "indexed": bool(row),
        "asset_count": 1 if row else 0,
        "asset_ids": (str(row[0]),) if row else (),
        "sha256": digest,
        "kind": "studio_image",
        "raw_content_retained": False,
        "owner_scoped": True,
    }


def list_assets(identity_id: object, *, limit: int = 100) -> dict[str, Any]:
    identity = _uuid(identity_id, "identity_id")
    safe_limit = max(1, min(int(limit or 100), 200))
    status = schema_status()
    if not status.get("schema_ready"):
        return {
            "component": "SMI Founder Library",
            "ready": False,
            "assets": (),
            "asset_count": 0,
            "raw_content_retained": False,
            "error": status.get("error"),
        }
    with postgres_db.connect(readonly=True) as connection:
        rows = connection.execute(
            """SELECT asset_id,conversation_id,request_id,source,asset_kind,
                      filename,mime_type,content_sha256,frame_count,created_at
               FROM smi_founder_assets
               WHERE identity_id=%s
               ORDER BY created_at DESC
               LIMIT %s""",
            (identity, safe_limit),
        ).fetchall()
    assets = tuple(
        {
            "asset_id": str(row[0]),
            "conversation_id": str(row[1]),
            "request_id": str(row[2]),
            "source": str(row[3]),
            "kind": str(row[4]),
            "filename": str(row[5]),
            "mime_type": str(row[6]),
            "sha256": str(row[7]),
            "frame_count": int(row[8]),
            "created_at": row[9].isoformat(),
            "raw_content_retained": False,
        }
        for row in rows
    )
    return {
        "component": "SMI Founder Library",
        "ready": True,
        "assets": assets,
        "asset_count": len(assets),
        "raw_content_retained": False,
        "owner_scoped": True,
        "human_authority_final": True,
    }
