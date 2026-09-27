from uuid import uuid4

import pytest

from mission_control import rights_studio_adapter


def _record():
    return {
        "asset_id": str(uuid4()),
        "identity_id": str(uuid4()),
        "request_id": str(uuid4()),
        "source": "studio_generation",
        "asset_kind": "studio_image",
        "content_sha256": "a" * 64,
    }


def _request(record, **overrides):
    row = {
        "asset_id": record["asset_id"],
        "requester_identity_id": record["identity_id"],
        "use": "publish",
        "territory": "GB",
        "channel": "OAP Media",
        "requested_at": "2026-09-27T00:00:00Z",
    }
    row.update(overrides)
    return row


def test_studio_generation_proof_does_not_unlock_publication():
    record = _record()
    result = rights_studio_adapter.evaluate_studio_publish(
        record=record, request=_request(record),
        evidence_hashes=["b" * 64], territories=["GB"],
    )
    assert result["decision"] == "REVIEW"
    assert result["generation_proof_is_not_rights_proof"] is True
    assert result["public_publish_enabled"] is False


def test_studio_publish_requires_explicit_receipts_and_stable_grant():
    record = _record()
    kwargs = dict(
        record=record, request=_request(record),
        evidence_hashes=["b" * 64], territories=["GB"],
        authority_verified=True, authority_receipt_hash="c" * 64,
        human_approved=True, human_approval_receipt_hash="d" * 64,
    )
    a = rights_studio_adapter.evaluate_studio_publish(**kwargs)
    b = rights_studio_adapter.evaluate_studio_publish(**kwargs)
    assert a["decision"] == "ALLOW"
    assert a["matching_grant_ids"] == b["matching_grant_ids"]
    assert a["public_publish_enabled"] is False


def test_studio_owner_channel_territory_and_missing_evidence_fail_closed():
    record = _record()
    common = dict(
        record=record, evidence_hashes=["b" * 64], territories=["GB"],
        authority_verified=True, authority_receipt_hash="c" * 64,
        human_approved=True, human_approval_receipt_hash="d" * 64,
    )
    wrong_owner = rights_studio_adapter.evaluate_studio_publish(
        request=_request(record, requester_identity_id=str(uuid4())), **common
    )
    assert wrong_owner["decision"] == "BLOCK"

    wrong_channel = rights_studio_adapter.evaluate_studio_publish(
        request=_request(record, channel="OAP TV"), **common
    )
    assert wrong_channel["decision"] == "BLOCK"
    assert "channel_not_granted" in wrong_channel["reasons"]

    wrong_territory = rights_studio_adapter.evaluate_studio_publish(
        request=_request(record, territory="GH"), **common
    )
    assert wrong_territory["decision"] == "BLOCK"

    with pytest.raises(ValueError, match="missing_evidence"):
        rights_studio_adapter.evaluate_studio_publish(
            record=record, request=_request(record),
            evidence_hashes=[], territories=["GB"],
        )


def test_only_real_studio_generation_assets_are_accepted():
    record = _record()
    record["source"] = "chat_attachment"
    with pytest.raises(ValueError, match="studio_asset_source_required"):
        rights_studio_adapter.canonical_studio_asset(record)
