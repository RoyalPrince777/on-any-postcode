from uuid import uuid4

from mission_control import rights_product_adapters


def _asset():
    return {
        "asset_id": str(uuid4()),
        "owner_identity_id": str(uuid4()),
        "kind": "audio",
        "content_sha256": "a" * 64,
        "source_reference": "oap:test:product",
    }


def _request(asset, use, channel, **overrides):
    row = {
        "asset_id": asset["asset_id"],
        "requester_identity_id": asset["owner_identity_id"],
        "use": use,
        "territory": "GB",
        "channel": channel,
        "requested_at": "2026-09-27T00:00:00Z",
    }
    row.update(overrides)
    return row


def _trusted():
    return {
        "evidence_hashes": ["b" * 64],
        "territories": ["GB"],
        "authority_verified": True,
        "authority_receipt_hash": "c" * 64,
        "human_approved": True,
        "human_approval_receipt_hash": "d" * 64,
    }


def test_records_media_tv_distribution_use_one_internal_contract_without_public_action():
    asset = _asset()
    cases = [
        (rights_product_adapters.evaluate_records_archive, "archive", "OAP Records"),
        (rights_product_adapters.evaluate_media_publish, "publish", "OAP Media"),
        (rights_product_adapters.evaluate_tv_broadcast, "broadcast", "OAP TV"),
        (rights_product_adapters.evaluate_distribution_handoff, "distribution", "OAP Distribution"),
    ]
    for evaluator, use, channel in cases:
        result = evaluator(asset=asset, request=_request(asset, use, channel), **_trusted())
        assert result["decision"] == "ALLOW"
        assert result["internal_eligibility_only"] is True
        assert result["public_action_enabled"] is False
        assert result["legal_validity_verified"] is False
        assert result["public_distribution_authorized"] is False


def test_product_adapters_fail_closed_for_wrong_owner_channel_and_territory():
    asset = _asset()
    wrong_owner = rights_product_adapters.evaluate_tv_broadcast(
        asset=asset,
        request=_request(asset, "broadcast", "OAP TV", requester_identity_id=str(uuid4())),
        **_trusted(),
    )
    assert wrong_owner["decision"] == "BLOCK"
    assert "requester_not_asset_owner" in wrong_owner["reasons"]

    wrong_channel = rights_product_adapters.evaluate_distribution_handoff(
        asset=asset,
        request=_request(asset, "distribution", "OAP Media"),
        **_trusted(),
    )
    assert wrong_channel["decision"] == "BLOCK"
    assert "channel_not_granted" in wrong_channel["reasons"]

    wrong_territory = rights_product_adapters.evaluate_media_publish(
        asset=asset,
        request=_request(asset, "publish", "OAP Media", territory="GH"),
        **_trusted(),
    )
    assert wrong_territory["decision"] == "BLOCK"
    assert "territory_not_granted" in wrong_territory["reasons"]


def test_product_adapter_status_preserves_public_and_legal_boundary():
    status = rights_product_adapters.status()
    assert status["records_internal_gate"] is True
    assert status["media_internal_gate"] is True
    assert status["tv_internal_gate"] is True
    assert status["distribution_internal_gate"] is True
    assert status["public_action_enabled"] is False
    assert status["legal_validity_verified"] is False
