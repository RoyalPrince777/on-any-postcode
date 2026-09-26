"""Cryptographic recovery/read-back manifests for OAP Music Civilization.

This module snapshots first-party metadata state by canonical JSON digest. It
does not restore production data automatically. A verified manifest proves that
a read-back matches the captured metadata bytes; it does not prove copyright,
playback or external distribution.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from uuid import UUID

from . import postgres_db

RECOVERY_MIGRATION_VERSION = "0011_oap_music_recovery_manifest"

SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_music_recovery_manifests (
        manifest_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        release_id UUID NOT NULL REFERENCES oap_music_releases(release_id)
            ON DELETE CASCADE,
        manifest_sha256 TEXT NOT NULL CHECK (length(manifest_sha256)=64),
        manifest_json JSONB NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE INDEX IF NOT EXISTS ix_music_recovery_owner_release_created
        ON oap_music_recovery_manifests(
            owner_identity_id,release_id,created_at DESC
        )""",
)


def _uuid(value: object, name: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"invalid_{name}") from exc


def canonical_manifest_bytes(payload: object) -> bytes:
    if not isinstance(payload, Mapping):
        raise TypeError("invalid_manifest")
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def manifest_digest(payload: object) -> str:
    return hashlib.sha256(canonical_manifest_bytes(payload)).hexdigest()


def verify_manifest(payload: object, claimed_sha256: object) -> dict[str, object]:
    if not isinstance(claimed_sha256, str) or len(claimed_sha256) != 64:
        return {
            "verified": False,
            "manifest_sha256": None,
            "playback_enabled": False,
            "external_distribution_enabled": False,
        }
    actual = manifest_digest(payload)
    return {
        "verified": actual == claimed_sha256,
        "manifest_sha256": actual,
        "playback_enabled": False,
        "external_distribution_enabled": False,
    }


class MusicRecoveryStore:
    """Owner-scoped immutable metadata snapshots and read-back verification."""

    def ensure_schema(self) -> None:
        with postgres_db.connect() as connection:
            for statement in SCHEMA_STATEMENTS:
                connection.execute(statement)
            connection.commit()

    def capture(
        self, *, owner_identity_id: object, release_id: object, payload: object
    ) -> dict[str, object]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        release = _uuid(release_id, "release_id")
        raw = canonical_manifest_bytes(payload)
        digest = hashlib.sha256(raw).hexdigest()
        if len(raw) > 2_000_000:
            raise ValueError("recovery_manifest_too_large")
        with postgres_db.connect() as connection:
            owned = connection.execute(
                """SELECT 1 FROM oap_music_releases
                   WHERE release_id=%s AND owner_identity_id=%s FOR UPDATE""",
                (release, owner),
            ).fetchone()
            if owned is None:
                raise PermissionError("recovery_release_not_owned")
            row = connection.execute(
                """INSERT INTO oap_music_recovery_manifests(
                   owner_identity_id,release_id,manifest_sha256,manifest_json)
                   VALUES (%s,%s,%s,%s::jsonb)
                   RETURNING manifest_id,created_at""",
                (owner, release, digest, raw.decode("utf-8")),
            ).fetchone()
            connection.commit()
        return {
            "manifest_id": str(row[0]),
            "release_id": release,
            "manifest_sha256": digest,
            "created_at": row[1].isoformat(),
            "restore_performed": False,
        }

    def read_and_verify(
        self, *, owner_identity_id: object, manifest_id: object
    ) -> dict[str, object]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        manifest = _uuid(manifest_id, "manifest_id")
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT release_id,manifest_sha256,manifest_json,created_at
                   FROM oap_music_recovery_manifests
                   WHERE manifest_id=%s AND owner_identity_id=%s""",
                (manifest, owner),
            ).fetchone()
        if row is None:
            raise PermissionError("recovery_manifest_not_owned")
        payload = row[2]
        check = verify_manifest(payload, str(row[1]))
        return {
            "manifest_id": manifest,
            "release_id": str(row[0]),
            "manifest_sha256": str(row[1]),
            "created_at": row[3].isoformat(),
            "readback_verified": check["verified"],
            "restore_performed": False,
            "playback_enabled": False,
            "external_distribution_enabled": False,
        }
