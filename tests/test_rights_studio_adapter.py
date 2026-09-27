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


def _request(asset_id, territory="GB"):
    return {
        "asset_id": asset_id,
        "use": "publish",
        "territory": territory,
        "channel": "OAP Media",
        "requested_at": "2026-09-27T00:00:00Z",
    }


def test_studio_generation_proof_does_not_unlock_publication():
    record = _record()
    result = rights_studio_adapter.evaluate_studio_publish(
        record=record,
        request=_request(record["asset_id"]),
        evidence_hashes=["b" * 64],
        territories=["GB"],
    )
    assert result["decision"] == "REVIEW"
    assert result["generation_proof_is_not_rights_proof"] is True
    assert result["public_publish_enabled"] is False


def test_studio_publish_requires_explicit_authority_and_human_approval():
    record = _record()
    result = rights_studio_adapter.evaluate_studio_publish(
        record=record,
        request=_request(record["asset_id"]),
        evidence_hashes=["b" * 64],
        territories=["GB"],
        authority_verified=True,
        human_approved=True,
    )
    assert result["decision"] == "ALLOW"
    assert result["public_publish_enabled"] is False


def test_studio_wrong_territory_and_missing_evidence_fail_closed():
    record = _record()
    blocked = rights_studio_adapter.evaluate_studio_publish(
        record=record,
        request=_request(record["asset_id"], territory="GH"),
        evidence_hashes=["b" * 64],
        territories=["GB"],
        authority_verified=True,
        human_approved=True,
    )
    assert blocked["decision"] == "BLOCK"
    assert "territory_not_granted" in blocked["reasons"]

    with pytest.raises(ValueError, match="missing_evidence"):
        rights_studio_adapter.evaluate_studio_publish(
            record=record,
            request=_request(record["asset_id"]),
            evidence_hashes=[],
            territories=["GB"],
            authority_verified=True,
            human_approved=True,
        )


def test_only_real_studio_generation_assets_are_accepted():
    record = _record()
    record["source"] = "chat_attachment"
    with pytest.raises(ValueError, match="studio_asset_source_required"):
        rights_studio_adapter.canonical_studio_asset(record)
