from __future__ import annotations

from pathlib import Path

import pytest

from mission_control import smi_founder_assets

ROOT = Path(__file__).resolve().parents[1]


class FakeConnection:
    def __init__(self, *, table_ready: bool = True):
        self.table_ready = table_ready
        self.inserts = []

    def execute(self, sql, params=()):
        if "information_schema.tables" in sql:
            return FakeResult((1,) if self.table_ready else None)
        if "INSERT INTO smi_founder_assets" in sql:
            self.inserts.append((sql, params))
            return FakeResult((f"00000000-0000-0000-0000-{len(self.inserts):012d}",))
        raise AssertionError(f"Unexpected SQL: {sql}")


class FakeResult:
    def __init__(self, row):
        self.row = row

    def fetchone(self):
        return self.row


def test_founder_asset_schema_is_metadata_only_and_owner_scoped():
    schema = "\n".join(smi_founder_assets.ASSET_SCHEMA_STATEMENTS)

    assert "identity_id UUID NOT NULL REFERENCES oap_identities" in schema
    assert "conversation_id UUID NOT NULL REFERENCES smi_conversations" in schema
    assert "content_sha256 TEXT NOT NULL" in schema
    assert "raw_content_retained BOOLEAN NOT NULL DEFAULT FALSE" in schema
    assert "CHECK (raw_content_retained=FALSE)" in schema
    assert "BYTEA" not in schema
    assert "image_bytes" not in schema


def test_founder_asset_migration_requires_explicit_human_approval():
    with pytest.raises(RuntimeError, match="Explicit human approval"):
        smi_founder_assets.init_schema()

    dry = smi_founder_assets.init_schema(assume_yes=True, dry_run=True)
    assert dry["dry_run"] is True
    assert dry["migration"] == smi_founder_assets.ASSET_MIGRATION_VERSION
    assert dry["raw_content_retained"] is False


def test_chat_asset_index_fails_open_for_chat_but_truthfully_reports_pending_schema():
    connection = FakeConnection(table_ready=False)

    result = smi_founder_assets.record_chat_assets(
        connection,
        identity_id="00000000-0000-0000-0000-000000000001",
        conversation_id="00000000-0000-0000-0000-000000000002",
        request_id="00000000-0000-0000-0000-000000000003",
        media={
            "kind": "document",
            "filename": "plan.pdf",
            "mime": "application/pdf",
            "sha256": "a" * 64,
            "frame_count": 0,
        },
    )

    assert result == {
        "indexed": False,
        "asset_count": 0,
        "reason": "founder_asset_schema_pending",
        "raw_content_retained": False,
    }
    assert connection.inserts == []


def test_chat_asset_index_records_only_secret_safe_metadata():
    connection = FakeConnection(table_ready=True)

    result = smi_founder_assets.record_chat_assets(
        connection,
        identity_id="00000000-0000-0000-0000-000000000001",
        conversation_id="00000000-0000-0000-0000-000000000002",
        request_id="00000000-0000-0000-0000-000000000003",
        image_data="data:image/png;base64,ZmFrZQ==",
        media={
            "kind": "document",
            "filename": "plan.pdf",
            "mime": "application/pdf",
            "sha256": "b" * 64,
            "frame_count": 0,
        },
    )

    assert result["indexed"] is True
    assert result["asset_count"] == 2
    assert result["raw_content_retained"] is False
    assert len(connection.inserts) == 2
    serialized = repr(connection.inserts)
    assert "ZmFrZQ==" not in serialized
    assert "raw_content_retained" in serialized


def test_master_workspace_exposes_founder_library_without_false_green():
    base = (ROOT / "mission_control" / "templates" / "ollama_chat_base.html").read_text()
    wrapper = (ROOT / "mission_control" / "templates" / "ollama_chat.html").read_text()
    final = (ROOT / "mission_control" / "static" / "smi_chat_final.js").read_text()

    assert 'data-oap-action="founder-library"' in base
    assert "Founder Library" in base
    assert "founderLibraryUrl" in wrapper
    assert "cfg.founderLibraryUrl" in final
    assert "d?.ready===false" in final
    assert "d?.green===false" in final
    assert "d?.schema_ready===false" in final
    assert "founderLibrary:true" in final


def test_chat_runtime_indexes_assets_inside_governed_transaction():
    runtime = (ROOT / "mission_control" / "smi_chat_runtime_core.py").read_text()

    assert "smi_founder_assets.record_chat_assets(" in runtime
    assert '"founder_assets": founder_assets' in runtime
    assert '"founder_assets_indexed"' in runtime
    assert '"raw_media_retained": False' in runtime
