"""Studio handoff must not turn a metadata record into invented raw media."""
from __future__ import annotations

from mission_control import smi_founder_assets

OWNER = "11111111-1111-4111-8111-111111111111"
OTHER = "22222222-2222-4222-8222-222222222222"
ASSET = "33333333-3333-4333-8333-333333333333"


class Result:
    def __init__(self, row):
        self.row = row

    def fetchone(self):
        return self.row


class Store:
    def __init__(self, *, table=True, owner=OWNER):
        self.table = table
        self.owner = owner
        self.queries = []

    def execute(self, sql, params=()):
        self.queries.append((sql, params))
        if "information_schema.tables" in sql:
            return Result((1,) if self.table else None)
        if "FROM smi_founder_assets WHERE identity_id=%s AND asset_id=%s" in sql:
            if params != (self.owner, ASSET):
                return Result(None)
            return Result((ASSET, "chat_image", "image", "approved.png", "image/png", False))
        raise AssertionError(f"Unexpected SQL: {sql}")


def test_known_asset_requires_fresh_upload_not_false_reuse():
    store = Store()
    result = smi_founder_assets.prepare_studio_handoff(
        store, identity_id=OWNER, asset_id=ASSET
    )
    assert result["asset_known"] is True
    assert result["original_available"] is False
    assert result["handoff_state"] == "fresh_upload_required"
    assert result["studio_execution_granted"] is False
    assert result["publishing_granted"] is False
    assert result["distribution_granted"] is False
    assert "bytes" not in result and "download_url" not in result
    assert store.queries[-1][1] == (OWNER, ASSET)


def test_other_owner_cannot_discover_asset_metadata():
    result = smi_founder_assets.prepare_studio_handoff(
        Store(owner=OWNER), identity_id=OTHER, asset_id=ASSET
    )
    assert result["asset_known"] is False
    assert result["handoff_state"] == "not_found"
    assert "filename" not in result


def test_missing_asset_fails_closed():
    result = smi_founder_assets.prepare_studio_handoff(
        Store(owner=OTHER), identity_id=OWNER, asset_id=ASSET
    )
    assert result["original_available"] is False
    assert result["handoff_state"] == "not_found"


def test_missing_optional_index_does_not_claim_media_reuse():
    store = Store(table=False)
    result = smi_founder_assets.prepare_studio_handoff(
        store, identity_id=OWNER, asset_id=ASSET
    )
    assert result["handoff_state"] == "index_unavailable"
    assert result["original_available"] is False
    assert len(store.queries) == 1


def test_founder_library_lists_metadata_as_not_reusable(monkeypatch):
    from contextlib import nullcontext
    from datetime import datetime, timezone

    class LibraryStore:
        def execute(self, sql, params=()):
            if "FROM smi_founder_assets" in sql:
                class Rows:
                    def fetchall(self):
                        return [(
                            ASSET, "44444444-4444-4444-8444-444444444444",
                            "55555555-5555-4555-8555-555555555555",
                            "chat_image", "image", "approved.png", "image/png",
                            "a" * 64, 0, datetime(2026, 9, 21, tzinfo=timezone.utc),
                        )]
                return Rows()
            raise AssertionError(f"Unexpected SQL: {sql}")

    monkeypatch.setattr(
        smi_founder_assets, "schema_status", lambda: {"schema_ready": True}
    )
    monkeypatch.setattr(
        smi_founder_assets.postgres_db,
        "connect",
        lambda readonly=False: nullcontext(LibraryStore()),
    )

    result = smi_founder_assets.list_assets(OWNER)
    assert result["asset_count"] == 1
    asset = result["assets"][0]
    assert asset["original_available"] is False
    assert asset["studio_handoff_state"] == "fresh_upload_required"
    assert asset["studio_execution_granted"] is False
    assert asset["raw_content_retained"] is False
