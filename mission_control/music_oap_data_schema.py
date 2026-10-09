"""Additive OAP Data catalogue storage contract.

DDL only: no automatic migration, publication, payment or playback authority.
"""
from __future__ import annotations

OAP_DATA_SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_music_track_data (
        track_id UUID PRIMARY KEY REFERENCES oap_music_tracks(track_id) ON DELETE CASCADE,
        genre TEXT,
        language TEXT,
        country TEXT,
        isrc TEXT,
        instruments JSONB NOT NULL DEFAULT '[]'::jsonb,
        location_publication_consent BOOLEAN NOT NULL DEFAULT FALSE,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CHECK (genre IS NULL OR length(genre) BETWEEN 1 AND 80),
        CHECK (language IS NULL OR language ~ '^[a-z]{2,3}(-[a-z0-9]{2,8}){0,3}$'),
        CHECK (country IS NULL OR country ~ '^[A-Z]{2}$'),
        CHECK (isrc IS NULL OR isrc ~ '^[A-Z]{2}[A-Z0-9]{3}[0-9]{7}$'),
        CHECK (jsonb_typeof(instruments) = 'array'),
        CHECK (jsonb_array_length(instruments) <= 12)
    )""",
    """CREATE INDEX IF NOT EXISTS ix_oap_music_data_genre
       ON oap_music_track_data (lower(genre)) WHERE genre IS NOT NULL""",
    """CREATE INDEX IF NOT EXISTS ix_oap_music_data_language
       ON oap_music_track_data (language) WHERE language IS NOT NULL""",
    """CREATE INDEX IF NOT EXISTS ix_oap_music_data_country_consented
       ON oap_music_track_data (country)
       WHERE location_publication_consent IS TRUE AND country IS NOT NULL""",
)


def public_discovery_projection() -> str:
    """SQL for approved releases only; never exposes unconsented geography."""
    return """
        SELECT t.track_id, t.title, r.release_id, r.title AS release_title,
               d.genre, d.language,
               CASE WHEN d.location_publication_consent IS TRUE
                    THEN d.country ELSE NULL END AS country,
               d.instruments
        FROM oap_music_tracks t
        JOIN oap_music_releases r ON r.release_id = t.release_id
        LEFT JOIN oap_music_track_data d ON d.track_id = t.track_id
        WHERE r.state = 'PUBLISHED' AND r.rights_status = 'VERIFIED'
    """


# Versioned independently: never mutate the checksum of the applied 0006 migration.
import hashlib

from . import postgres_db

OAP_DATA_MIGRATION_VERSION = "0007_music_oap_data"
OAP_DATA_MIGRATION_CHECKSUM = hashlib.sha256(
    "\n".join(OAP_DATA_SCHEMA_STATEMENTS).encode()
).hexdigest()


def init_oap_data_schema(*, assume_yes: bool = False, dry_run: bool = False) -> dict[str, object]:
    """Explicit additive migration; fail closed on checksum drift."""
    if not assume_yes:
        raise RuntimeError("Explicit human approval required: pass --yes")
    if not postgres_db.postgres_status().get("initialized"):
        raise RuntimeError("Base PostgreSQL schema must be ready first")
    if dry_run:
        return {"dry_run": True, "migration": OAP_DATA_MIGRATION_VERSION,
                "checksum": OAP_DATA_MIGRATION_CHECKSUM}
    with postgres_db.connect() as connection:
        connection.execute("SELECT pg_advisory_xact_lock(%s)", (25800007,))
        parent = connection.execute(
            "SELECT 1 FROM oap_schema_migrations WHERE version=%s",
            ("0006_music_market_post_office",),
        ).fetchone()
        if parent is None:
            raise RuntimeError("Music product-core migration required first")
        row = connection.execute(
            "SELECT checksum FROM oap_schema_migrations WHERE version=%s",
            (OAP_DATA_MIGRATION_VERSION,),
        ).fetchone()
        if row is not None and str(row[0]) != OAP_DATA_MIGRATION_CHECKSUM:
            raise RuntimeError("Applied OAP Data migration checksum mismatch")
        if row is None:
            for statement in OAP_DATA_SCHEMA_STATEMENTS:
                connection.execute(statement)
            connection.execute(
                "INSERT INTO oap_schema_migrations(version,checksum) VALUES (%s,%s)",
                (OAP_DATA_MIGRATION_VERSION, OAP_DATA_MIGRATION_CHECKSUM),
            )
        connection.commit()
    return {"migration": OAP_DATA_MIGRATION_VERSION,
            "checksum": OAP_DATA_MIGRATION_CHECKSUM, "applied": True}
