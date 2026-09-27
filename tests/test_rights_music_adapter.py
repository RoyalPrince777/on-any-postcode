from uuid import uuid4

import pytest

from mission_control import music_evidence, rights_music_adapter


def _asset():
    return {
        "asset_id": str(uuid4()),
        "owner_identity_id": str(uuid4()),
        "kind": "audio",
        "content_sha256": "a" * 64,
        "source_reference": "oap:music:test",
    }


def _receipts(owner, release):
    rows = []
    previous = music_evidence.GENESIS_HASH
    for kind in (
        "source_page",
        "recording_rights",
        "composition_rights",
        "asset_provenance",
        "territory_permission",
        "attribution",
        "human_approval",
        "recovery_readback",
    ):
        row = music_evidence.build_receipt(
            owner_identity_id=owner,
            release_id=release,
            evidence_kind=kind,
            evidence_bytes=(kind + ":proof").encode(),
            territory="GB" if kind == "territory_permission" else None,
            previous_receipt_hash=previous,
        )
        previous = row["receipt_hash"]
        rows.append(row)
    return rows


def _request(asset_id):
    return {
        "asset_id": asset_id,
        "use": "stream",
        "territory": "GB",
        "channel": "OAP Music",
        "requested_at": "2026-09-27T00:00:00Z",
    }


def test_music_evidence_projects_without_inventing_authority_or_approval():
    asset = _asset()
    receipts = _receipts(asset["owner_identity_id"], str(uuid4()))
    result = rights_music_adapter.project_music_release(
        asset=asset,
        receipts=receipts,
        permitted_uses=["stream"],
        territories=["GB"],
    )
    assert result["private_music_handoff_ready"] is True
    assert result["grant"]["authority_verified"] is False
    assert result["grant"]["human_approved"] is False
    assert result["rights_verified_by_software"] is False
    assert result["public_distribution_enabled"] is False


def test_music_use_requires_explicit_trusted_authority_and_human_approval():
    asset = _asset()
    receipts = _receipts(asset["owner_identity_id"], str(uuid4()))
    review = rights_music_adapter.evaluate_music_use(
        asset=asset,
        receipts=receipts,
        request=_request(asset["asset_id"]),
        permitted_uses=["stream"],
        territories=["GB"],
    )
    assert review["decision"] == "REVIEW"

    allowed = rights_music_adapter.evaluate_music_use(
        asset=asset,
        receipts=receipts,
        request=_request(asset["asset_id"]),
        permitted_uses=["stream"],
        territories=["GB"],
        authority_verified=True,
        human_approved=True,
    )
    assert allowed["decision"] == "ALLOW"
    assert allowed["public_distribution_enabled"] is False


def test_incomplete_or_tampered_music_evidence_fails_closed():
    asset = _asset()
    receipts = _receipts(asset["owner_identity_id"], str(uuid4()))

    with pytest.raises(ValueError, match="music_evidence_incomplete"):
        rights_music_adapter.project_music_release(
            asset=asset,
            receipts=receipts[:-2],
            permitted_uses=["stream"],
            territories=["GB"],
        )

    receipts[2]["previous_receipt_hash"] = "f" * 64
    with pytest.raises(ValueError, match="music_evidence_chain_invalid"):
        rights_music_adapter.project_music_release(
            asset=asset,
            receipts=receipts,
            permitted_uses=["stream"],
            territories=["GB"],
        )


def test_wrong_territory_still_blocks_through_shared_rights_core():
    asset = _asset()
    receipts = _receipts(asset["owner_identity_id"], str(uuid4()))
    request = _request(asset["asset_id"])
    request["territory"] = "GH"
    result = rights_music_adapter.evaluate_music_use(
        asset=asset,
        receipts=receipts,
        request=request,
        permitted_uses=["stream"],
        territories=["GB"],
        authority_verified=True,
        human_approved=True,
    )
    assert result["decision"] == "BLOCK"
    assert "territory_not_granted" in result["reasons"]
