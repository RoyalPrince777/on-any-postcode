"""Fail-closed checks for the evidence-first War Room read-only projection."""
from pathlib import Path

from mission_control.smi_war_room_front_projection import front_review_projection

TEMPLATE = Path(__file__).resolve().parents[1] / "mission_control/templates/war_room.html"
VIEWS = Path(__file__).resolve().parents[1] / "mission_control/views.py"


def test_seven_registered_rule_lenses_are_not_real_votes_or_stars():
    info = front_review_projection({
        "canonical_judges": tuple("abcdefg"),
        "canonical_count": 7,
        "all_judges_present": True,
    })
    assert info["rule_lenses_registered"] == 7
    assert info["actual_vote_count"] is None
    assert info["mission_stars_certified"] is None
    assert info["mission_signals_proven"] is None
    assert info["signal_denominator"] == 21
    assert info["founder_final_proven"] is None


def test_broken_registry_fails_closed():
    for broken in (
        {"canonical_judges": tuple("abcdefg"), "canonical_count": 7},
        {"canonical_judges": tuple("aaaaaaa"), "canonical_count": 7,
         "all_judges_present": True},
        {"canonical_judges": tuple("abcdefg"), "canonical_count": True,
         "all_judges_present": True},
    ):
        assert front_review_projection(broken)["rule_lenses_registered"] is None


def test_founder_route_and_front_template_use_projection_without_fake_votes():
    source = VIEWS.read_text(encoding="utf-8")
    html = TEMPLATE.read_text(encoding="utf-8")
    route = source.split("def war_room_dashboard():", 1)[1].split(
        "@bp.get", 1
    )[0]
    assert "front_review=smi_war_room_front_projection.front_review_projection()" in route
    front = html.split('id="war-room-front-summary"', 1)[1].split(
        '<section class="grid status">', 1
    )[0]
    assert "front_review.rule_lenses_registered" in front
    assert "front_review.signal_denominator" in front
    assert "front_review.star_denominator" in front
    assert "Not independently executed votes" in front
    assert "Not determined by seat count" in front
