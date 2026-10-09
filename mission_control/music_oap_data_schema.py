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
