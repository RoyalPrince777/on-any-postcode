from uuid import uuid4

import pytest

from mission_control import rights_core, rights_persistence


def _asset():
    return {
        "asset_id": str(uuid4()),
        "owner_identity_id": str(uuid4()),
        "kind": "audio",
        "content_sha256": "a" * 64,
        "source_reference": "oap:test:rights-persistence",
    }


def _decision(asset):
    grant = {
        "grant_id": str(uuid4()),
        "asset_id": asset["asset_id"],
        "owner_identity_id": asset["owner_identity_id"],
        "grantor_reference": "authority:test",
        "right_type": "stream",
        "permitted_uses": ["stream"],
        "territories": ["GB"],
        "permitted_channels": ["OAP Music"],
        "evidence_hashes": ["b" * 64],
        "authority_verified": True,
        "authority_receipt_hash": "c" * 64,
        "human_approved": True,
        "human_approval_receipt_hash": "d" * 64,
    }
    request = {
        "asset_id": asset["asset_id"],
        "requester_identity_id": asset["owner_identity_id"],
        "use": "stream",
        "territory": "GB",
        "channel": "OAP Music",
        "requested_at": "2026-09-28T00:00:00Z",
    }
    return rights_core.evaluate_use(asset=asset, grants=[grant], request=request)


def test_decision_integrity_verifier_accepts_canonical_rights_decision():
    asset = _asset()
    decision = _decision(asset)
    check = rights_persistence.verify_decision(decision)
    assert check["verified"] is True
    assert check["decision_hash"] == decision["decision_hash"]


def test_decision_integrity_verifier_rejects_tampering():
    asset = _asset()
    decision = _decision(asset)
    decision["territory"] = "GH"
    assert rights_persistence.verify_decision(decision)["verified"] is False


def test_receipt_hash_binds_owner_asset_decision_and_previous_head():
    owner = str(uuid4())
    asset = str(uuid4())
    a = rights_persistence.decision_receipt_hash(
        owner_identity_id=owner,
        asset_id=asset,
        decision_hash="a" * 64,
    )
    b = rights_persistence.decision_receipt_hash(
        owner_identity_id=owner,
        asset_id=asset,
        decision_hash="a" * 64,
        previous_receipt_hash="b" * 64,
    )
    assert len(a) == 64
    assert len(b) == 64
    assert a != b


def test_recovery_manifest_round_trip_detects_changes():
    payload = {
        "asset_id": str(uuid4()),
        "head_hash": "a" * 64,
        "grant_ids": [str(uuid4())],
    }
    digest = rights_persistence.payload_digest(payload)
    assert rights_persistence.verify_recovery_manifest(payload, digest)["verified"] is True
    payload["head_hash"] = "b" * 64
    assert rights_persistence.verify_recovery_manifest(payload, digest)["verified"] is False


def test_schema_requires_explicit_human_authority_and_supports_dry_run():
    with pytest.raises(RuntimeError, match="Explicit human approval required"):
        rights_persistence.init_schema()

    preview = rights_persistence.init_schema(assume_yes=True, dry_run=True)
    assert preview["dry_run"] is True
    assert preview["migration"] == rights_persistence.RIGHTS_PERSISTENCE_MIGRATION_VERSION
    assert preview["tables"] == 4


def test_status_never_claims_public_or_legal_authority(monkeypatch):
    monkeypatch.setattr(
        rights_persistence,
        "schema_status",
        lambda: {"schema_ready": False},
    )
    state = rights_persistence.status()
    assert state["migration_applied"] is False
    assert state["public_action_enabled"] is False
    assert state["legal_validity_verified"] is False
    assert state["human_authority_final"] is True
