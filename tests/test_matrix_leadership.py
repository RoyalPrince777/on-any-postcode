"""Mission leadership votes never replace SMI and Captain ALL IN authority."""

import pytest

from mission_control.matrix_leadership import propose_personnel_change, recommend_lead


def test_mission_lead_votes_are_recommendations_only():
    decision = recommend_lead(
        "catalogue_verification",
        ("fox", "octopus", "neo"),
        nominations=("octopus",),
        votes=(("neo", "octopus"), ("fox", "octopus")),
    )
    assert decision.recommended_lead == "octopus"
    assert decision.captain == "captain_all_in"
    assert decision.command == "smi"
    assert decision.approved is False
    assert decision.execution_authorised is False
    assert set(decision.supporting_agents) == {"fox", "neo"}


def test_agent_can_nominate_itself_but_cannot_appoint_itself():
    result = recommend_lead("routing", ("fox", "neo"), nominations=("fox",))
    assert result.recommended_lead == "fox"
    assert result.approved is False


@pytest.mark.parametrize(
    "kwargs,expected",
    [
        ({"nominations": ("gorilla",)}, "ineligible_nomination"),
        ({"votes": (("neo", "fox"), ("neo", "fox"))}, "duplicate_vote"),
        ({"votes": (("neo", "gorilla"),)}, "ineligible_vote"),
    ],
)
def test_invalid_lead_selection_fails_closed(kwargs, expected):
    with pytest.raises(ValueError, match=expected):
        recommend_lead("routing", ("fox", "neo"), **kwargs)


def test_help_request_is_allowed_without_evidence():
    request = propose_personnel_change("fox", "help")
    assert request["status"] == "pending_smi_captain_review"
    assert request["executed"] is False


def test_promotion_and_termination_require_evidence_and_review():
    for action in ("promotion", "termination_review"):
        with pytest.raises(ValueError, match="personnel_change_requires_evidence"):
            propose_personnel_change("fox", action)
        request = propose_personnel_change("fox", action, evidence=("reviewed outcome",))
        assert request["approved"] is False
        assert request["executed"] is False
