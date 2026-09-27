from datetime import datetime, timezone
from uuid import uuid4

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


def _grant(asset_id, **overrides):
    row = {
        "grant_id": str(uuid4()),
        "asset_id": asset_id,
        "grantor_reference": "authority:test",
        "right_type": "stream",
        "permitted_uses": ["stream"],
        "territories": ["GB"],
        "valid_from": "2026-01-01T00:00:00Z",
        "valid_until": "2027-01-01T00:00:00Z",
        "derivatives_allowed": False,
        "commercial_use_allowed": False,
        "attribution_required": True,
        "evidence_hashes": [_sha("b")],
        "authority_verified": True,
        "human_approved": True,
        "revoked": False,
    }
    row.update(overrides)
    return row


def _request(asset_id, **overrides):
    row = {
        "asset_id": asset_id,
        "use": "stream",
        "territory": "GB",
        "channel": "OAP Music",
        "requested_at": "2026-09-27T00:00:00Z",
        "derivative": False,
    }
    row.update(overrides)
    return row


def test_exact_scoped_grant_allows_but_never_claims_software_verified_rights():
    asset = _asset()
    result = rights_core.evaluate_use(
        asset=asset,
        grants=[_grant(asset["asset_id"])],
        request=_request(asset["asset_id"]),
    )
    assert result["decision"] == "ALLOW"
    assert result["attribution_required"] is True
    assert result["evidence_hashes"] == [_sha("b")]
    assert result["rights_verified_by_software"] is False
    assert result["human_authority_final"] is True
    assert len(result["decision_hash"]) == 64


def test_expired_revoked_wrong_territory_and_wrong_use_fail_closed():
    asset = _asset()
    cases = [
        (_grant(asset["asset_id"], valid_until="2026-01-02T00:00:00Z"), "grant_expired"),
        (_grant(asset["asset_id"], revoked=True), "grant_revoked"),
        (_grant(asset["asset_id"], territories=["GH"]), "territory_not_granted"),
        (_grant(asset["asset_id"], permitted_uses=["archive"]), "use_not_granted"),
    ]
    for grant, reason in cases:
        result = rights_core.evaluate_use(
            asset=asset, grants=[grant], request=_request(asset["asset_id"])
        )
        assert result["decision"] == "BLOCK"
        assert reason in result["reasons"]


def test_unverified_authority_or_missing_human_approval_requires_review():
    asset = _asset()
    for grant, reason in (
        (_grant(asset["asset_id"], authority_verified=False), "grantor_authority_unverified"),
        (_grant(asset["asset_id"], human_approved=False), "human_approval_missing"),
    ):
        result = rights_core.evaluate_use(
            asset=asset, grants=[grant], request=_request(asset["asset_id"])
        )
        assert result["decision"] == "REVIEW"
        assert reason in result["reasons"]


def test_derivative_requires_allowed_scope_and_valid_lineage():
    parent = _asset()
    child = _asset(parent_asset_id=parent["asset_id"], content_sha256=_sha("c"))
    blocked = rights_core.evaluate_use(
        asset=child,
        grants=[_grant(child["asset_id"], derivatives_allowed=False)],
        request=_request(child["asset_id"], derivative=True),
        lineage_assets=[parent, child],
    )
    assert blocked["decision"] == "BLOCK"
    assert "derivative_not_allowed" in blocked["reasons"]

    allowed = rights_core.evaluate_use(
        asset=child,
        grants=[_grant(child["asset_id"], derivatives_allowed=True)],
        request=_request(child["asset_id"], derivative=True),
        lineage_assets=[parent, child],
    )
    assert allowed["decision"] == "ALLOW"
    assert allowed["lineage"]["lineage_valid"] is True

    missing_parent = rights_core.evaluate_use(
        asset=child,
        grants=[_grant(child["asset_id"], derivatives_allowed=True)],
        request=_request(child["asset_id"], derivative=True),
        lineage_assets=[child],
    )
    assert missing_parent["decision"] == "BLOCK"
    assert "asset_missing" in missing_parent["reasons"]


def test_lineage_cycle_is_detected():
    a_id, b_id = str(uuid4()), str(uuid4())
    owner = str(uuid4())
    a = {
        "asset_id": a_id, "owner_identity_id": owner, "kind": "image",
        "content_sha256": _sha("d"), "parent_asset_id": b_id,
    }
    b = {
        "asset_id": b_id, "owner_identity_id": owner, "kind": "image",
        "content_sha256": _sha("e"), "parent_asset_id": a_id,
    }
    result = rights_core.lineage_chain(a_id, [a, b])
    assert result["lineage_valid"] is False
    assert result["reason"] == "lineage_cycle"


def test_malformed_or_self_asserted_grant_never_unlocks_use():
    asset = _asset()
    malformed = _grant(asset["asset_id"])
    malformed["evidence_hashes"] = []
    result = rights_core.evaluate_use(
        asset=asset,
        grants=[malformed, {"rights_verified": True, "asset_id": asset["asset_id"]}],
        request=_request(asset["asset_id"]),
    )
    assert result["decision"] == "BLOCK"
    assert result["rights_verified_by_software"] is False


def test_commercial_use_requires_explicit_commercial_permission():
    asset = _asset()
    request = _request(asset["asset_id"], use="commercial_use")
    grant = _grant(
        asset["asset_id"],
        right_type="distribution",
        permitted_uses=["commercial_use"],
        commercial_use_allowed=False,
    )
    result = rights_core.evaluate_use(asset=asset, grants=[grant], request=request)
    assert result["decision"] == "BLOCK"
    assert "commercial_use_not_allowed" in result["reasons"]


def test_status_keeps_universal_integration_truthfully_open():
    state = rights_core.status()
    assert state["canonical_asset_contract"] is True
    assert state["territory_aware"] is True
    assert state["time_aware"] is True
    assert state["rights_verified_by_software"] is False
    assert state["distribution_integration_complete"] is False
    assert state["universal_persistence_complete"] is False
