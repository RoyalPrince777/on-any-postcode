from __future__ import annotations

import pytest

from mission_control import distribution_700

CELLS = distribution_700.protocol_cells()
assert len(CELLS) == 700


@pytest.mark.parametrize(("lane", "lens", "evidence_test"), CELLS)
def test_distribution_700_each_protocol_cell_passes_and_fails_closed(
    lane: str,
    lens: str,
    evidence_test: str,
):
    passed = distribution_700.review_cell(
        lane,
        lens,
        evidence_test,
        evidence_present=True,
    )
    failed = distribution_700.review_cell(
        lane,
        lens,
        evidence_test,
        evidence_present=False,
    )

    assert passed == {
        "lane": lane,
        "lens": lens,
        "evidence_test": evidence_test,
        "passed": True,
        "state": "PASS",
        "execution_allowed": False,
        "human_authority_final": True,
    }
    assert failed["passed"] is False
    assert failed["state"] == "FAIL"
    assert failed["execution_allowed"] is False
    assert failed["human_authority_final"] is True


def _full_evidence():
    return {name: True for name in distribution_700.EVIDENCE_TESTS}


def test_distribution_700_is_exactly_seven_by_ten_by_ten():
    status = distribution_700.status()

    assert status["distribution_lane_count"] == 7
    assert status["intelligence_lens_count"] == 10
    assert status["evidence_test_count"] == 10
    assert status["protocol_check_count"] == 700
    assert status["unique_protocol_cells"] == 700
    assert status["protocol_is_checks_not_stages"] is True
    assert len(set(CELLS)) == 700


def test_distribution_700_covers_whole_oap_distribution_lanes():
    assert distribution_700.DISTRIBUTION_LANES == (
        "music",
        "tv_media",
        "sport",
        "clothing",
        "creator",
        "market_fulfilment",
        "local_post",
    )

    status = distribution_700.status()
    assert status["existing_distribution_intelligence_reused"] is True
    assert status["canonical_world_id"] == "civilisation"


@pytest.mark.parametrize("lane", distribution_700.DISTRIBUTION_LANES)
def test_each_distribution_lane_requires_all_evidence_before_proven(lane: str):
    complete = distribution_700.evaluate_lane_evidence(lane, _full_evidence())
    assert complete["passed"] == 10
    assert complete["required"] == 10
    assert complete["evidence_ready"] is True
    assert complete["state"] == "PROVEN"
    assert complete["external_execution_enabled"] is False
    assert complete["public_delivery_claim_allowed"] is False

    for missing in distribution_700.EVIDENCE_TESTS:
        evidence = _full_evidence()
        evidence[missing] = False
        incomplete = distribution_700.evaluate_lane_evidence(lane, evidence)
        assert incomplete["passed"] == 9
        assert incomplete["evidence_ready"] is False
        assert incomplete["state"] == "INCOMPLETE"
        assert incomplete["external_execution_enabled"] is False


def test_public_delivery_claim_requires_adapter_and_destination_receipt():
    evidence = _full_evidence()

    without_adapter = distribution_700.evaluate_lane_evidence("tv_media", evidence)
    assert without_adapter["public_delivery_claim_allowed"] is False

    evidence["authenticated_destination_adapter"] = True
    evidence["destination_delivery_receipt"] = True
    with_both = distribution_700.evaluate_lane_evidence("tv_media", evidence)
    assert with_both["public_delivery_claim_allowed"] is True
    assert with_both["external_execution_enabled"] is False


def test_lane_policies_preserve_rights_supply_and_logistics_boundaries():
    status = distribution_700.status()
    policies = status["lane_policies"]

    assert policies["music"]["rights_evidence_required"] is True
    assert policies["music"]["external_platform_assumed"] is False
    assert policies["tv_media"]["broadcast_or_stream_permission_required"] is True
    assert policies["sport"]["footage_rights_required"] is True
    assert policies["clothing"]["supplier_or_production_evidence_required"] is True
    assert policies["creator"]["creator_ownership_or_license_required"] is True
    assert policies["market_fulfilment"]["canonical_order_required"] is True
    assert policies["market_fulfilment"]["dispatch_receipt_required_for_dispatch_claim"] is True
    assert policies["local_post"]["parcel_or_booking_identity_required"] is True
    assert policies["local_post"]["recovery_readback_required"] is True


def test_distribution_700_never_claims_execution_authority():
    status = distribution_700.status()

    assert status["external_execution_enabled"] is False
    assert status["publishing_authority_granted"] is False
    assert status["payment_authority_granted"] is False
    assert status["dispatch_authority_granted"] is False
    assert status["carrier_handoff_authority_granted"] is False
    assert status["human_authority_final"] is True
    assert status["full_green"] is False
    assert status["no_fake_green"] is True


@pytest.mark.parametrize(
    ("lane", "lens", "evidence_test"),
    [
        ("unknown", "truth", "source_reference"),
        ("music", "unknown", "source_reference"),
        ("music", "truth", "unknown"),
    ],
)
def test_invalid_protocol_cell_dimensions_are_rejected(
    lane: str,
    lens: str,
    evidence_test: str,
):
    with pytest.raises(ValueError):
        distribution_700.review_cell(
            lane,
            lens,
            evidence_test,
            evidence_present=True,
        )
