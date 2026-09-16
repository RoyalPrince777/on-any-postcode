from pathlib import Path


def test_war_room_exposes_bounded_seven_x_without_claiming_runtime_or_execution():
    page = Path("mission_control/templates/war_room.html").read_text(encoding="utf-8")

    assert "7× DEEP DIVE" in page
    assert "Seven complete protocol passes" in page
    assert "seven accumulated research/review passes" in page
    assert "This surface performs no production write" in page
    assert "👑 Human Authority remains final" in page
    assert "No evidence = no Green. No test = no star." in page
