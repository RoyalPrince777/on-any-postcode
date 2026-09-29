import pytest

from mission_control import music_entitlements

OWNER = "11111111-1111-4111-8111-111111111111"
ASSET = "22222222-2222-4222-8222-222222222222"


def test_entitlement_schema_is_public_free_only_and_revocable():
    schema = "\n".join(music_entitlements.SCHEMA_STATEMENTS)
    assert music_entitlements.MUSIC_ENTITLEMENT_MIGRATION_VERSION == "0015_oap_music_entitlements"
    assert "oap_music_entitlements" in schema
    assert "PUBLIC_FREE" in schema
    assert "rights_decision_hash CHAR(64) NOT NULL" in schema
    assert "active BOOLEAN NOT NULL DEFAULT TRUE" in schema


def test_public_entitlement_requires_canonical_rights_allow(monkeypatch):
    store = music_entitlements.MusicEntitlementStore()
    monkeypatch.setattr(
        store._rights,
        "evaluate_platform_use",
        lambda **_kwargs: {
            "decision": {
                "decision": "REVIEW",
                "evidence_hashes": ["a" * 64],
                "authority_receipt_hashes": [],
                "human_approval_receipt_hashes": [],
                "public_distribution_authorized": False,
            }
        },
    )
    with pytest.raises(PermissionError, match="canonical_rights_allow_required"):
        store.create_public_free(
            owner_identity_id=OWNER,
            asset_id=ASSET,
            territory="GB",
        )


def test_public_gate_fails_closed_when_asset_is_stopped(monkeypatch):
    class Result:
        def __init__(self, row):
            self.row = row
        def fetchone(self):
            return self.row

    class Connection:
        calls = 0
        def __enter__(self):
            return self
        def __exit__(self, *_args):
            return False
        def execute(self, sql, _params=()):
            if "FROM oap_music_entitlements" in sql:
                return Result((
                    "33333333-3333-4333-8333-333333333333",
                    OWNER,
                    None,
                    None,
                    "d" * 64,
                ))
            if "SELECT stopped FROM oap_music_assets" in sql:
                return Result((True,))
            return Result(None)

    monkeypatch.setattr(
        music_entitlements.postgres_db,
        "connect",
        lambda **_kwargs: Connection(),
    )
    result = music_entitlements.MusicEntitlementStore().public_gate(
        asset_id=ASSET,
        territory="GB",
        requested_at="2026-09-29T13:00:00+00:00",
    )
    assert result["allowed"] is False
    assert result["reason"] == "music_asset_stopped_or_missing"
    assert result["media_delivery_performed"] is False


def test_public_gate_allows_only_active_time_valid_entitlement(monkeypatch):
    class Result:
        def __init__(self, row):
            self.row = row
        def fetchone(self):
            return self.row

    class Connection:
        def __enter__(self):
            return self
        def __exit__(self, *_args):
            return False
        def execute(self, sql, _params=()):
            if "FROM oap_music_entitlements" in sql:
                return Result((
                    "33333333-3333-4333-8333-333333333333",
                    OWNER,
                    None,
                    None,
                    "d" * 64,
                ))
            if "SELECT stopped FROM oap_music_assets" in sql:
                return Result((False,))
            return Result(None)

    monkeypatch.setattr(
        music_entitlements.postgres_db,
        "connect",
        lambda **_kwargs: Connection(),
    )
    result = music_entitlements.MusicEntitlementStore().public_gate(
        asset_id=ASSET,
        territory="GB",
        requested_at="2026-09-29T13:00:00+00:00",
    )
    assert result["allowed"] is True
    assert result["rights_decision_hash"] == "d" * 64
    assert result["media_delivery_performed"] is False
    assert result["payment_capture_performed"] is False
