from __future__ import annotations

import pytest

from mission_control import ecosystem_handoff


def test_ecosystem_path_is_locked_and_ordered():
    status = ecosystem_handoff.path_status()

    assert status["stage_ids"] == (
        "the_link",
        "market",
        "media_distribution",
        "oap_store",
    )
    assert status["hard_locks"] == {
        "payment_capture": False,
        "external_distribution": False,
        "automatic_install": False,
        "permission_transfer": False,
        "authority_transfer": False,
    }
    assert status["human_authority_final"] is True


def test_link_to_market_handoff_requires_governed_context():
    result = ecosystem_handoff.handoff(
        "the_link",
        "market",
        evidence={"identity": True, "merchant_or_creator_context": True},
    )

    assert result["destination"] == "/the-spot/market"
    assert result["evidence_proven"] is True
    assert result["permission_transferred"] is False
    assert result["authority_transferred"] is False
    assert result["payment_captured"] is False


def test_media_to_store_handoff_requires_certification_and_package_proof():
    result = ecosystem_handoff.handoff(
        "media_distribution",
        "oap_store",
        evidence={
            "identity": True,
            "certification": True,
            "package_proof": True,
        },
    )

    assert result["destination"] == "service:ownpost-store"
    assert result["external_distribution_performed"] is False
    assert result["automatic_install_performed"] is False


def test_handoff_fails_closed_when_rights_proof_is_missing():
    with pytest.raises(
        ecosystem_handoff.HandoffBlocked,
        match="missing_handoff_evidence:rights_proof",
    ):
        ecosystem_handoff.handoff(
            "market",
            "media_distribution",
            evidence={
                "identity": True,
                "creator_context": True,
                "rights_proof": False,
            },
        )


def test_handoff_cannot_skip_a_product_boundary():
    with pytest.raises(
        ecosystem_handoff.HandoffBlocked,
        match="adjacent_handoff_required",
    ):
        ecosystem_handoff.handoff(
            "the_link",
            "oap_store",
            evidence={
                "identity": True,
                "certification": True,
                "package_proof": True,
            },
        )
