"""First-party OAP Music catalogue selection and storage planning.

Metadata discovery is not permission to stream, sell or download recordings.
Pure functions only: no network, database writes, or runtime permissions.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

GEOGRAPHY = ("global", "continent", "country", "region", "borough", "postcode")
SELECTABLE = ("artist", "release", "recording", "genre", "country", "decade")
RIGHTS_STATES = ("discovery_only", "review", "licensed", "unavailable")


@dataclass(frozen=True)
class CatalogueSelection:
    kind: str
    identifier: str
    featured: bool = False

    def __post_init__(self) -> None:
        if self.kind not in SELECTABLE:
            raise ValueError("unknown_selection_kind")
        if not isinstance(self.identifier, str) or not self.identifier.strip():
            raise ValueError("invalid_selection_identifier")


@dataclass(frozen=True)
class CatalogueEntry:
    canonical_id: str
    artist_ids: tuple[str, ...]
    countries: tuple[str, ...]
    genres: tuple[str, ...]
    decades: tuple[str, ...]
    rights_state: str = "discovery_only"

    def __post_init__(self) -> None:
        if not isinstance(self.canonical_id, str) or not self.canonical_id.strip():
            raise ValueError("invalid_catalogue_id")
        if self.rights_state not in RIGHTS_STATES:
            raise ValueError("invalid_rights_state")

    @property
    def can_play(self) -> bool:
        return self.rights_state == "licensed"

    @property
    def can_sell(self) -> bool:
        # Actual commercial rights must be checked separately per territory/use.
        return False


def select_entries(
    entries: Iterable[CatalogueEntry],
    selections: Iterable[CatalogueSelection],
) -> tuple[CatalogueEntry, ...]:
    """Union founder choices; deduplicate by canonical ID, not geography."""
    chosen = tuple(selections)
    result: dict[str, CatalogueEntry] = {}
    for entry in entries:
        if any(
            (s.kind == "artist" and s.identifier in entry.artist_ids)
            or (s.kind in {"release", "recording"} and s.identifier == entry.canonical_id)
            or (s.kind == "genre" and s.identifier in entry.genres)
            or (s.kind == "country" and s.identifier in entry.countries)
            or (s.kind == "decade" and s.identifier in entry.decades)
            for s in chosen
        ):
            result.setdefault(entry.canonical_id, entry)
    return tuple(result.values())


def estimate_metadata_bytes(records: int, average_bytes: int = 1024) -> int:
    """Raw estimate only; excludes indexes, backups, artwork and audio."""
    if isinstance(records, bool) or not isinstance(records, int) or records < 0:
        raise ValueError("invalid_record_count")
    if isinstance(average_bytes, bool) or not isinstance(average_bytes, int) or average_bytes <= 0:
        raise ValueError("invalid_record_size")
    return records * average_bytes
