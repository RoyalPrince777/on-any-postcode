"""OAP TV response planning never bypasses Founder or media proof gates."""
from unittest.mock import patch

import pytest

from mission_control.tv_private_response_plan import plan_founder_private_response


def trusted(**overrides):
    values = dict(founder_authenticated=True, owner_identity_matches=True,
                  rights_decision={}, entitlement_proven=True,
                  storage_integrity_proven=True, server_evidence_verified=True,
                  media_size=100, range_header="bytes=10-19")
    values.update(overrides)
    return values


@pytest.mark.parametrize("field", [
    "founder_authenticated", "owner_identity_matches", "entitlement_proven",
    "storage_integrity_proven", "server_evidence_verified",
])
def test_denies_missing_proof_even_when_range_valid(field):
    args = trusted(**{field: False})
    result = plan_founder_private_response(**args)
    assert result["allowed"] is False
    assert result["media_bytes_served"] is False
    assert "status" not in result


def test_rights_denial_precedes_range_processing():
    result = plan_founder_private_response(**trusted())
    assert result["allowed"] is False
    assert "canonical_rights_allow_not_proven" in result["blockers"]


def test_no_range_calculation_when_auth_denied():
    with patch("mission_control.tv_private_response_plan.parse_single_range") as parse:
        result = plan_founder_private_response(**trusted(founder_authenticated=False))
    assert result["allowed"] is False
    parse.assert_not_called()


@pytest.mark.parametrize("size", [0, -1, True, None])
def test_invalid_size_denied_after_authorization(size):
    with patch("mission_control.tv_private_response_plan.authorize_private_playback",
               return_value={"allowed": True, "blockers": []}):
        result = plan_founder_private_response(**trusted(media_size=size))
    assert result["allowed"] is False


def test_authorized_partial_range_never_claims_media_was_served():
    with patch("mission_control.tv_private_response_plan.authorize_private_playback",
               return_value={"allowed": True, "blockers": []}):
        result = plan_founder_private_response(**trusted())
    assert result["status"] == 206
    assert result["content_range"] == "bytes 10-19/100"
    assert result["media_bytes_served"] is False
    assert result["public_playback_enabled"] is False


def test_authorized_invalid_range_does_not_serve_bytes():
    with patch("mission_control.tv_private_response_plan.authorize_private_playback",
               return_value={"allowed": True, "blockers": []}):
        result = plan_founder_private_response(**trusted(range_header="bytes=200-"))
    assert result["status"] == 416
    assert result["allowed"] is False
    assert result["media_bytes_served"] is False
