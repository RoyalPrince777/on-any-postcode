"""Fox recovery is advisory and never performs a route change."""
import pytest

from oap.smi.fox_recovery import FoxRecoveryRequest, propose_fox_recovery


def request(evidence=("route timeout",), fallbacks=("local cached route",)):
    return FoxRecoveryRequest("koradaso-map", "akan_core", "route_failure", evidence, fallbacks)


def test_missing_evidence_fails_closed():
    plan = propose_fox_recovery(request(evidence=()))
    assert plan.action == "hold_missing_evidence"
    assert plan.selected_fallback is None


def test_no_approved_fallback_fails_closed():
    plan = propose_fox_recovery(request(fallbacks=()))
    assert plan.action == "hold_no_approved_fallback"


def test_approved_fallback_remains_only_a_proposal():
    plan = propose_fox_recovery(request())
    assert plan.action == "propose_approved_fallback_for_human_review"
    assert plan.selected_fallback == "local cached route"
    assert plan.advisory_only and not plan.authority_granted
    assert not plan.route_changed and not plan.runtime_verified
    assert plan.family_ownership_unchanged
    assert plan.requesting_family == "akan_core"


@pytest.mark.parametrize("mission,family,kind", [
    ("", "akan_core", "route_failure"),
    ("koradaso", "", "route_failure"),
    ("koradaso", "akan_core", ""),
])
def test_missing_identity_is_rejected(mission, family, kind):
    with pytest.raises(ValueError):
        propose_fox_recovery(FoxRecoveryRequest(mission, family, kind, ("failure",)))
