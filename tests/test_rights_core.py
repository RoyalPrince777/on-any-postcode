from uuid import uuid4

import pytest

from mission_control import rights_core


def _sha(seed="a"):
    return (seed * 64)[:64]


def _asset(**overrides):
    row = {
        "asset_id": str(uuid4()),
        "owner_identity_id": str(uuid4()),
        "kind": "audio",
        "content_sha256": _sha("a"),
        "source_reference": "oap:test",
    }
    row.update(overrides)
    return row


def _grant(asset, **overrides):
    row = {
        "grant_id": str(uuid4()),
        "asset_id": asset["asset_id"],
        "owner_identity_id": asset["owner_identity_id"],
        "grantor_reference": "authority:test",
        "right_type": "stream",
        "permitted_uses": ["stream"],
        "territories": ["GB"],
        "permitted_channels": ["OAP Music"],
        "valid_from": "2026-01-01T00:00:00Z",
        "valid_until": "2027-01-01T00:00:00Z",
        "derivatives_allowed": False,
        "commercial_use_allowed": False,
        "attribution_required": True,
        "evidence_hashes": [_sha("b")],
        "authority_verified": True,
        "authority_receipt_hash": _sha("c"),
        "human_approved": True,
        "human_approval_receipt_hash": _sha("d"),
        "revoked": False,
    }
    row.update(overrides)
    return row


def _request(asset, **overrides):
    row = {
        "asset_id": asset["asset_id"],
        "requester_identity_id": asset["owner_identity_id"],
        "use": "stream",
        "territory": "GB",
        "channel": "OAP Music",
        "requested_at": "2026-09-27T00:00:00Z",
        "derivative": False,
    }
    row.update(overrides)
    return row


def test_exact_scoped_grant_allows_but_never_claims_verified_rights():
    asset = _asset()
    result = rights_core.evaluate_use(
        asset=asset, grants=[_grant(asset)], request=_request(asset)
    )
    assert result["decision"] == "ALLOW"
    assert result["attribution_required"] is True
    assert result["evidence_hashes"] == [_sha("b")]
    assert result["authority_receipt_hashes"] == [_sha("c")]
    assert result["human_approval_receipt_hashes"] == [_sha("d")]
    assert result["rights_verified_by_software"] is False
    assert result["public_distribution_authorized"] is False
    assert result["human_authority_final"] is True
    assert len(result["decision_hash"]) == 64


def test_owner_channel_territory_use_and_time_fail_closed():
    asset = _asset()
    other = str(uuid4())
    cases = [
        (_grant(asset), _request(asset, requester_identity_id=other), "requester_not_asset_owner"),
        (_grant(asset, permitted_channels=["OAP TV"]), _request(asset), "channel_not_granted"),
        (_grant(asset, territories=["GH"]), _request(asset), "territory_not_granted"),
        (_grant(asset, right_type="recording", permitted_uses=["archive"]), _request(asset), "use_not_granted"),
        (_grant(asset, valid_until="2026-01-02T00:00:00Z"), _request(asset), "grant_expired"),
    ]
    for grant, request, reason in cases:
        result = rights_core.evaluate_use(asset=asset, grants=[grant], request=request)
        assert result["decision"] == "BLOCK"
        assert reason in result["reasons"]


def test_right_type_use_window_and_receipt_contract_rejects_malformed_grants():
    asset = _asset()
    bad = [
        {"right_type": "stream", "permitted_uses": ["broadcast"]},
        {"valid_from": "2027-01-01T00:00:00Z", "valid_until": "2026-01-01T00:00:00Z"},
        {"authority_verified": True, "authority_receipt_hash": None},
        {"human_approved": True, "human_approval_receipt_hash": None},
    ]
    for override in bad:
        with pytest.raises(ValueError):
            rights_core.canonical_grant(_grant(asset, **override))


def test_unverified_authority_or_missing_human_approval_requires_review():
    asset = _asset()
    for grant, reason in (
        (_grant(asset, authority_verified=False, authority_receipt_hash=None), "grantor_authority_unverified"),
        (_grant(asset, human_approved=False, human_approval_receipt_hash=None), "human_approval_missing"),
    ):
        result = rights_core.evaluate_use(asset=asset, grants=[grant], request=_request(asset))
        assert result["decision"] == "REVIEW"
        assert reason in result["reasons"]


def test_revocation_requires_receipt_and_blocks():
    asset = _asset()
    with pytest.raises(ValueError, match="revocation_receipt_required"):
        rights_core.canonical_grant(_grant(asset, revoked=True))
    result = rights_core.evaluate_use(
        asset=asset,
        grants=[_grant(asset, revoked=True, revocation_receipt_hash=_sha("e"))],
        request=_request(asset),
    )
    assert result["decision"] == "BLOCK"
    assert "grant_revoked" in result["reasons"]


def test_derivative_requires_allowed_scope_and_valid_lineage():
    parent = _asset()
    child = _asset(owner_identity_id=parent["owner_identity_id"], parent_asset_id=parent["asset_id"], content_sha256=_sha("e"))
    grant = _grant(
        child,
        right_type="recording",
        permitted_uses=["derivative"],
        permitted_channels=["OAP Studio"],
        derivatives_allowed=True,
    )
    request = _request(child, use="derivative", channel="OAP Studio", derivative=True)
    allowed = rights_core.evaluate_use(
        asset=child, grants=[grant], request=request, lineage_assets=[parent, child]
    )
    assert allowed["decision"] == "ALLOW"
    missing = rights_core.evaluate_use(
        asset=child, grants=[grant], request=request, lineage_assets=[child]
    )
    assert missing["decision"] == "BLOCK"
    assert "asset_missing" in missing["reasons"]


def test_lineage_cycle_is_detected():
    a_id, b_id = str(uuid4()), str(uuid4())
    owner = str(uuid4())
    a = {"asset_id": a_id, "owner_identity_id": owner, "kind": "image", "content_sha256": _sha("f"), "parent_asset_id": b_id}
    b = {"asset_id": b_id, "owner_identity_id": owner, "kind": "image", "content_sha256": _sha("1"), "parent_asset_id": a_id}
    result = rights_core.lineage_chain(a_id, [a, b])
    assert result["lineage_valid"] is False
    assert result["reason"] == "lineage_cycle"


def test_malformed_or_self_asserted_grant_never_unlocks_use():
    asset = _asset()
    malformed = _grant(asset)
    malformed["evidence_hashes"] = []
    result = rights_core.evaluate_use(
        asset=asset,
        grants=[malformed, {"rights_verified": True, "asset_id": asset["asset_id"]}],
        request=_request(asset),
    )
    assert result["decision"] == "BLOCK"
    assert result["rights_verified_by_software"] is False


def test_status_exposes_software_gates_but_not_distribution_completion():
    state = rights_core.status()
    assert state["owner_authorization_required"] is True
    assert state["channel_aware"] is True
    assert state["right_type_use_bound"] is True
    assert state["authority_receipt_bound"] is True
    assert state["human_approval_receipt_bound"] is True
    assert state["revocation_receipt_bound"] is True
    assert state["rights_verified_by_software"] is False
    assert state["distribution_integration_complete"] is False
