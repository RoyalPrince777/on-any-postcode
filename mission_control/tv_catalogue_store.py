"""OAP TV owner-scoped, local SQLite draft catalogue. Never publishes or serves media."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .tv_cinema_catalogue import catalogue_item, private_catalogue

MAX_OWNER_LENGTH = 128


class PrivateCatalogueError(ValueError):
    """A caller supplied invalid draft catalogue authority."""


def _owner(value: object) -> str:
    if (not isinstance(value, str) or not 1 <= len(value) <= MAX_OWNER_LENGTH
            or not value.isascii() or not all(c.isalnum() or c in "-_" for c in value)):
        raise PrivateCatalogueError("invalid_owner_identity")
    return value


class PrivateTvCatalogueStore:
    """Caller must supply authenticated owner from trusted server-side identity."""

    def __init__(self, db_path: Path):
        if not isinstance(db_path, Path):
            raise PrivateCatalogueError("invalid_db_path")
        self.db_path = db_path

    def _connect(self):
        connection = sqlite3.connect(self.db_path, timeout=5)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS oap_tv_drafts (
                owner_id TEXT NOT NULL,
                item_id TEXT NOT NULL,
                item_json TEXT NOT NULL,
                PRIMARY KEY (owner_id, item_id)
            )
        """)
        return connection

    def save_draft(self, owner_id: str, row: object) -> dict[str, object]:
        owner = _owner(owner_id)
        item = catalogue_item(row)
        if item is None:
            raise PrivateCatalogueError("invalid_draft")
        # Only normalised, fail-closed fields enter storage.
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO oap_tv_drafts (owner_id,item_id,item_json) VALUES (?,?,?) "
                "ON CONFLICT(owner_id,item_id) DO UPDATE SET item_json=excluded.item_json",
                (owner, item["item_id"], json.dumps(item, sort_keys=True)),
            )
        return item

    def list_drafts(self, owner_id: str) -> dict[str, object]:
        owner = _owner(owner_id)
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT item_json FROM oap_tv_drafts WHERE owner_id=? ORDER BY item_id LIMIT 100",
                (owner,),
            ).fetchall()
        # Stored JSON cannot establish media or publishing authority.
        drafts = [json.loads(row[0]) for row in rows]
        converted = []
        for row in drafts:
            item = dict(row)
            item["item_id"] = str(item["item_id"]).removeprefix("oap:tv:")
            if "series_id" in item:
                item["series_id"] = str(item["series_id"]).removeprefix("oap:tv:")
            converted.append(item)
        return private_catalogue(converted)
