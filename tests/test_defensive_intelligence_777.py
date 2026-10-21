"""Negative boundary tests for the advisory-only defence core."""
from datetime import UTC, datetime

import pytest

from mission_control import defensive_intelligence_777 as defence


def observation(**overrides):
    data = {
        "source": "oap-test-node",
        "source_ownership": "oap_owned",
        "observed_at": datetime.now(UTC).isoformat(),
        "event_type": "hazard",
        "evidence_class": "observed",
        "evidence": ["local-test-record"],
        "first_party": {"observation": True},
    }
    data.update(overrides)
    return data


def test_founder_gate_denies_by_default():
    with pytest.raises(PermissionError):
        defence.assess(observation(), division="tactical")


def test_external_requires_separate_authorisation():
    with pytest.raises(PermissionError):
        defence.assess(observation(source_ownership="external_public", first_party={}), division="strategic", founder_authorised=True)


def test_external_cannot_claim_owned_observation():
    with pytest.raises(ValueError):
        defence.assess(observation(source_ownership="external_public"), division="strategic", founder_authorised=True, public_source_authorised=True)


def test_unknown_division_denied():
    with pytest.raises(ValueError):
        defence.assess(observation(), division="offensive", founder_authorised=True)


def test_unverified_denied():
    with pytest.raises(ValueError):
        defence.assess(observation(evidence_class="unverified"), division="cyber", founder_authorised=True)


def test_non_defensive_event_denied():
    with pytest.raises(ValueError):
        defence.assess(observation(event_type="targeting"), division="tactical", founder_authorised=True)


def test_owned_advisory_never_executes():
    result = defence.assess(observation(), division="earth_geoint", founder_authorised=True)
    assert result["advisory_only"] is True
    assert result["execution_granted"] is False
    assert result["production_ready"] is False


def test_authorised_public_remains_external():
    result = defence.assess(observation(source_ownership="external_public", first_party={}), division="strategic", founder_authorised=True, public_source_authorised=True)
    assert result["public_source_separately_labelled"] is True
    assert result["observation"]["first_party"]["observation"] is False
