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
        "source_page", "recording_rights", "composition_rights",
        "asset_provenance", "territory_permission", "attribution",
        "human_approval", "recovery_readback",
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


def _request(asset, **overrides):
    row = {
        "asset_id": asset["asset_id"],
        "requester_identity_id": asset["owner_identity_id"],
        "use": "stream",
        "territory": "GB",
        "channel": "OAP Music",
        "requested_at": "2026-09-27T00:00:00Z",
    }
    row.update(overrides)
    return row


def test_music_projection_is_stable_and_does_not_infer_authority():
    asset = _asset()
    receipts = _receipts(asset["owner_identity_id"], str(uuid4()))
    a = rights_music_adapter.project_music_release(
        asset=asset, receipts=receipts, permitted_uses=["stream"], territories=["GB"]
    )
    b = rights_music_adapter.project_music_release(
        asset=asset, receipts=receipts, permitted_uses=["stream"], territories=["GB"]
    )
    assert a["grant"]["grant_id"] == b["grant"]["grant_id"]
    assert a["private_music_handoff_ready"] is True
    assert a["grant"]["authority_verified"] is False
    assert a["grant"]["human_approved"] is False
    assert a["rights_verified_by_software"] is False
    assert a["public_distribution_enabled"] is False


def test_music_use_requires_explicit_authority_and_human_receipts():
    asset = _asset()
    receipts = _receipts(asset["owner_identity_id"], str(uuid4()))
    review = rights_music_adapter.evaluate_music_use(
        asset=asset, receipts=receipts, request=_request(asset),
        permitted_uses=["stream"], territories=["GB"],
    )
    assert review["decision"] == "REVIEW"

    allowed = rights_music_adapter.evaluate_music_use(
        asset=asset, receipts=receipts, request=_request(asset),
        permitted_uses=["stream"], territories=["GB"],
        authority_verified=True, authority_receipt_hash="c" * 64,
        human_approved=True, human_approval_receipt_hash="d" * 64,
    )
    assert allowed["decision"] == "ALLOW"
    assert allowed["public_distribution_enabled"] is False


def test_music_owner_channel_and_territory_fail_closed():
    asset = _asset()
    receipts = _receipts(asset["owner_identity_id"], str(uuid4()))
    common = dict(
        asset=asset, receipts=receipts, permitted_uses=["stream"], territories=["GB"],
        authority_verified=True, authority_receipt_hash="c" * 64,
        human_approved=True, human_approval_receipt_hash="d" * 64,
    )
    owner_block = rights_music_adapter.evaluate_music_use(
        request=_request(asset, requester_identity_id=str(uuid4())), **common
    )
    assert owner_block["decision"] == "BLOCK"
    assert "requester_not_asset_owner" in owner_block["reasons"]

    channel_block = rights_music_adapter.evaluate_music_use(
        request=_request(asset, channel="OAP TV"), **common
    )
    assert channel_block["decision"] == "BLOCK"
    assert "channel_not_granted" in channel_block["reasons"]

    territory_block = rights_music_adapter.evaluate_music_use(
        request=_request(asset, territory="GH"), **common
    )
    assert territory_block["decision"] == "BLOCK"
    assert "territory_not_granted" in territory_block["reasons"]


def test_incomplete_or_tampered_music_evidence_fails_closed():
    asset = _asset()
    receipts = _receipts(asset["owner_identity_id"], str(uuid4()))
    with pytest.raises(ValueError, match="music_evidence_incomplete"):
        rights_music_adapter.project_music_release(
            asset=asset, receipts=receipts[:-2],
            permitted_uses=["stream"], territories=["GB"],
        )
    receipts[2]["previous_receipt_hash"] = "f" * 64
    with pytest.raises(ValueError, match="music_evidence_chain_invalid"):
        rights_music_adapter.project_music_release(
            asset=asset, receipts=receipts,
            permitted_uses=["stream"], territories=["GB"],
        )
