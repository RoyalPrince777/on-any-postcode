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


def discover_public_data(*, genre: str | None = None, language: str | None = None,
                         country: str | None = None, limit: int = 50) -> list[dict[str, object]]:
    """Read-only, rights-gated discovery; country filters require publication consent."""
    from .music_catalogue_metadata import normalize_metadata

    try:
        effective_limit = min(100, max(1, int(limit)))
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid_limit") from exc
    filters: list[str] = []
    params: list[object] = []
    for name, value in (("genre", genre), ("language", language), ("country", country)):
        if value is None:
            continue
        validated = normalize_metadata({name: value})[name]
        if name == "country":
            filters.append("d.location_publication_consent IS TRUE AND d.country=%s")
        elif name == "genre":
            filters.append("lower(d.genre)=lower(%s)")
        else:
            filters.append("d.language=%s")
        params.append(validated)
    sql = public_discovery_projection()
    if filters:
        sql += " AND " + " AND ".join(filters)
    sql += " ORDER BY r.created_at DESC,t.position ASC LIMIT %s"
    params.append(effective_limit)
    with postgres_db.connect(readonly=True) as connection:
        rows = connection.execute(sql, tuple(params)).fetchall()
    return [
        {"track_id": str(row[0]), "track_title": str(row[1]),
         "release_id": str(row[2]), "release_title": str(row[3]),
         "genre": row[4], "language": row[5], "country": row[6],
         "instruments": row[7] if row[7] is not None else [],
         "playback_enabled": False}
        for row in rows
    ]


def oap_data_schema_status() -> dict[str, object]:
    """Read-only verification of the recorded migration and physical table."""
    result: dict[str, object] = {
        "migration": OAP_DATA_MIGRATION_VERSION,
        "schema_ready": False,
        "error": "oap_data_schema_unverified",
    }
    if not postgres_db.postgres_status().get("initialized"):
        result["error"] = "base_postgres_not_ready"
        return result
    try:
        with postgres_db.connect(readonly=True) as connection:
            migration = connection.execute(
                "SELECT checksum FROM oap_schema_migrations WHERE version=%s",
                (OAP_DATA_MIGRATION_VERSION,),
            ).fetchone()
            table = connection.execute(
                "SELECT to_regclass('public.oap_music_track_data')"
            ).fetchone()
            indexes = connection.execute(
                """SELECT indexname FROM pg_indexes
                   WHERE schemaname='public' AND tablename='oap_music_track_data'"""
            ).fetchall()
            columns = connection.execute(
                """SELECT column_default, is_nullable FROM information_schema.columns
                   WHERE table_schema='public' AND table_name='oap_music_track_data'
                     AND column_name='location_publication_consent'"""
            ).fetchone()
            foreign_key = connection.execute(
                """SELECT 1 FROM pg_constraint
                   WHERE conrelid='public.oap_music_track_data'::regclass
                     AND contype='f' AND confrelid='public.oap_music_tracks'::regclass"""
            ).fetchone()
        if migration is None or str(migration[0]) != OAP_DATA_MIGRATION_CHECKSUM:
            result["error"] = "oap_data_migration_not_verified"
        elif table is None or table[0] is None:
            result["error"] = "oap_data_table_missing"
        elif not {
            "ix_oap_music_data_genre",
            "ix_oap_music_data_language",
            "ix_oap_music_data_country_consented",
        }.issubset({row[0] for row in indexes}):
            result["error"] = "oap_data_indexes_missing"
        elif columns is None or columns[1] != "NO" or "false" not in str(columns[0]).lower():
            result["error"] = "oap_data_consent_default_invalid"
        elif foreign_key is None:
            result["error"] = "oap_data_foreign_key_missing"
        else:
            result["schema_ready"] = True
            result["error"] = None
    except Exception:  # noqa: BLE001
        result["error"] = "oap_data_store_unavailable"
    return result
