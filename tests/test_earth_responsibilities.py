"""Earth Is Our Turf seven-capability governance contract tests."""
from oap.smi.earth_responsibilities import (
    CAPABILITY_KEYS,
    capability_publication_eligible,
    get_earth_capability,
    list_earth_capabilities,
)


def test_seven_distinct_responsibilities():
    assert len(CAPABILITY_KEYS) == 7
    assert len(set(CAPABILITY_KEYS)) == 7
    assert len(list_earth_capabilities()) == 7


def test_all_seven_fail_closed_and_remain_unverified():
    for capability in list_earth_capabilities():
        assert capability.implementation_status == "NOT_VERIFIED"
        assert capability.source_required
        assert capability.human_publication_review
        assert capability.permission_required
        assert not capability.personal_profiling_allowed
        assert not capability.autonomous_execution_allowed
        assert not capability_publication_eligible(
            capability.key, sources_verified=True,
            permission_verified=True, human_review_approved=True,
        )


def test_unknown_and_invalid_capabilities_have_no_authority():
    for value in ("unknown", "", None, {}, 7):
        assert get_earth_capability(value) is None
        assert not capability_publication_eligible(value)


def test_partial_evidence_cannot_authorise_publication():
    assert not capability_publication_eligible(
        "earth_pulse", sources_verified=True, permission_verified=True
    )
    assert not capability_publication_eligible("earth_pulse", human_review_approved=True)
