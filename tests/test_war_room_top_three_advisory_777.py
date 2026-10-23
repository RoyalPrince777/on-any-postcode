"""Top-three War Room council: advisory-only contract regression.

These checks deliberately do not create votes, agent identities, permissions,
or a new command hierarchy. They guard the existing review boundary.
"""

from mission_control import war_room
from oap.war_room.engine import WarRoomEngine


TOP_THREE_ADVISORY_ROLES = (
    ("Captain ALL IN", "mission coordination"),
    ("Gyata", "leadership challenge"),
    ("Fox", "independent discovery"),
)


def test_top_three_are_distinct_advisory_perspectives_only():
    assert len(TOP_THREE_ADVISORY_ROLES) == 3
    assert len({name for name, _ in TOP_THREE_ADVISORY_ROLES}) == 3
    assert all(role for _, role in TOP_THREE_ADVISORY_ROLES)


def test_advisory_council_cannot_claim_founder_decision_authority():
    status = WarRoomEngine().status()
    assert status["decision_authority"] is False
    assert status["production_control_ready"] is False
    assert any(
        boundary["components"] == "War Room / Human Authority"
        and boundary["resolution"]
        == "War Room reviews consequences; Human Authority alone decides."
        for boundary in war_room.RESOLVED_BOUNDARIES
    )


def test_review_lenses_keep_protection_and_memory_independent():
    owners = {lens["owner"] for lens in war_room.REVIEW_LENSES}
    assert "Guardian" in owners
    assert "HRM" in owners
    assert "Sovereign" in owners
