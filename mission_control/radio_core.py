"""First-party OAP Radio contract layered on OAP Music and the Universal Player.

Radio owns station/show/schedule/rotation metadata only. It never creates a
second media player, grants music rights, fetches audio, starts a broadcast or
claims an external delivery. Rotation can become eligible only from a canonical
OAP Music item whose independent player rights gate is already allowed.
"""
from __future__ import annotations

from collections.abc import Mapping
from uuid import UUID

from . import entertainment_catalogue

RADIO_MIGRATION_VERSION = "0008_oap_radio_core"
STATION_STATES = frozenset({"DRAFT", "REVIEW_REQUIRED", "ACTIVE", "ARCHIVED"})
SHOW_STATES = frozenset({"DRAFT", "SCHEDULED", "ACTIVE", "ARCHIVED"})
MAX_TEXT = 180

SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_radio_stations (
        station_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        name TEXT NOT NULL,
        slug TEXT NOT NULL,
        state TEXT NOT NULL DEFAULT 'DRAFT'
            CHECK (state IN ('DRAFT','REVIEW_REQUIRED','ACTIVE','ARCHIVED')),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(owner_identity_id,slug)
    )""",
    """CREATE INDEX IF NOT EXISTS ix_radio_station_owner_created
        ON oap_radio_stations(owner_identity_id,created_at DESC)""",
    """CREATE TABLE IF NOT EXISTS oap_radio_shows (
        show_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        station_id UUID NOT NULL REFERENCES oap_radio_stations(station_id)
            ON DELETE CASCADE,
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        title TEXT NOT NULL,
        state TEXT NOT NULL DEFAULT 'DRAFT'
            CHECK (state IN ('DRAFT','SCHEDULED','ACTIVE','ARCHIVED')),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS oap_radio_schedule (
        schedule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        station_id UUID NOT NULL REFERENCES oap_radio_stations(station_id)
            ON DELETE CASCADE,
        show_id UUID NOT NULL REFERENCES oap_radio_shows(show_id)
            ON DELETE CASCADE,
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        starts_at TIMESTAMPTZ NOT NULL,
        ends_at TIMESTAMPTZ NOT NULL CHECK (ends_at > starts_at),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE INDEX IF NOT EXISTS ix_radio_schedule_station_start
        ON oap_radio_schedule(station_id,starts_at)""",
    """CREATE TABLE IF NOT EXISTS oap_radio_rotation (
        rotation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        station_id UUID NOT NULL REFERENCES oap_radio_stations(station_id)
            ON DELETE CASCADE,
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        track_id UUID NOT NULL REFERENCES oap_music_tracks(track_id)
            ON DELETE RESTRICT,
        position INTEGER NOT NULL CHECK (position > 0),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(station_id,position)
    )""",
)


def _uuid(value: object, name: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"invalid_{name}") from exc


def _text(value: object, name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"invalid_{name}")
    cleaned = " ".join(value.split())
    if not cleaned or len(cleaned) > MAX_TEXT:
        raise ValueError(f"invalid_{name}")
    return cleaned


def station_projection(record: object) -> dict[str, object] | None:
    """Allowlist one owner-scoped station metadata record."""
    if not isinstance(record, Mapping):
        return None
    try:
        station_id = _uuid(record.get("station_id"), "station_id")
        name = _text(record.get("name"), "name")
    except (TypeError, ValueError):
        return None
    state = record.get("state")
    if state not in STATION_STATES:
        return None
    return {
        "station_id": station_id,
        "name": name,
        "state": state,
        "broadcast_live": False,
        "public_stream_url": None,
    }


def rotation_gate(music_item: object) -> dict[str, object]:
    """Reuse the canonical Music rights gate; caller flags cannot bypass it."""
    item = music_item if isinstance(music_item, Mapping) else {}
    rights = entertainment_catalogue.rights_gate(item)
    return {
        "rotation_eligible": bool(rights.get("allowed") is True),
        "rights": rights,
        "player_owner": entertainment_catalogue.PLAYER_OWNER,
        "audio_fetch_performed": False,
        "broadcast_started": False,
        "external_distribution_performed": False,
        "human_authority_final": True,
    }


def radio_contract() -> dict[str, object]:
    """Describe the bounded first-party Radio organ and one shared player."""
    return {
        "organ": "OAP Radio",
        "owner": "OAP",
        "mode": "first_party_fail_closed",
        "capabilities": (
            "stations",
            "shows",
            "schedule",
            "rotation",
            "now_playing",
            "history",
            "stop",
        ),
        "music_source": "OAP Music",
        "player": entertainment_catalogue.universal_player_contract(),
        "dedicated_media_player_created": False,
        "broadcast_enabled": False,
        "public_streaming_enabled": False,
        "external_distribution_enabled": False,
        "rights_verified_by_radio": False,
        "human_authority_final": True,
    }
