"""Evidence-first War Room front must not manufacture mission certification."""
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parents[1] / "mission_control/templates/war_room.html"


def test_alignment_precedes_older_status_and_vote_board():
    html = TEMPLATE.read_text(encoding="utf-8")
    assert html.index('id="war-room-front-summary"') < html.index('class="grid status"')
    assert html.index('id="war-room-front-summary"') < html.index('id="vote-board"')


def test_front_summary_scopes_metrics_and_does_not_fake_review_results():
    html = TEMPLATE.read_text(encoding="utf-8")
    front = html.split('id="war-room-front-summary"', 1)[1].split(
        '<section class="grid status">', 1
    )[0]
    for criterion in (
        "Truth", "Function", "Security", "Stability",
        "Integration", "Compliance", "Learning",
    ):
        assert f"☆ {criterion}" in front
    for quarter in ("25% · Recovery", "50% · Runtime Guard",
                    "75% · Aegis Isolation", "100% · Green Gate + Founder Final"):
        assert quarter in front
    assert "PORTFOLIO EVIDENCE · NOT MISSION COMPLETION" in front
    assert "Not verified for this mission" in front
    assert "Not assessed for this mission" in front
    assert "not inferred" in front
    assert "0/7" not in front
    assert "7/7 passed" not in front
