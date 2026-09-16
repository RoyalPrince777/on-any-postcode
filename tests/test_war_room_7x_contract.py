from pathlib import Path

from mission_control import smi_deep_dive_protocol


def test_seven_x_is_seven_accumulated_passes_not_a_depth_mode():
    status = smi_deep_dive_protocol.status()
    seven_x = status["seven_x"]
    assert seven_x["is_depth_mode"] is False
    assert [item["name"] for item in seven_x["passes"]] == [
        "Discovery",
        "Verification",
        "Alternatives",
        "Adversarial",
        "Systems",
        "Consequence",
        "Synthesis",
    ]
    assert status["protocol_loop"] == (
        "Observe",
        "Classify",
        "Verify",
        "Fix / Plan",
        "Retest",
        "Record",
        "Learn",
    )


def test_war_room_keeps_execution_and_auth_locked():
    locks = smi_deep_dive_protocol.status()["locks"]
    assert locks["read_only"] is True
    assert locks["production_write"] is False
    assert locks["deploy"] is False
    assert locks["auth_change"] is False
    assert locks["permission_change"] is False
    assert locks["human_authority_final"] is True


def test_war_room_ui_has_clear_research_vote_challenge_and_output_contract():
    page = Path("mission_control/templates/war_room.html").read_text(encoding="utf-8")
    for marker in (
        "7× DEEP DIVE",
        "Research intelligence",
        "Vote board",
        "Challenge room",
        "Seven-Star Gate",
        "Guardian · End Review · SMI Judgement",
        "Clear output",
        "No fabricated tally",
        "Human Authority remains final",
    ):
        assert marker in page
