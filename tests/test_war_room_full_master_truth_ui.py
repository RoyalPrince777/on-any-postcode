from pathlib import Path


def test_war_room_ui_never_treats_presence_as_readiness():
    page = Path("mission_control/templates/war_room.html").read_text(encoding="utf-8")

    assert "No evidence = no Green" in page
    assert "proven · conflicting · stale · unavailable · unknown" in page
    assert "⚪ Check current run" in page
    assert "7/7 is a Green Gate candidate only" in page


def test_war_room_ui_exposes_canonical_read_only_controls():
    page = Path("mission_control/templates/war_room.html").read_text(encoding="utf-8")

    for control in (
        "▶ RUN",
        "🔬 RESEARCH",
        "⚔️ CHALLENGE",
        "7× DEEP DIVE",
        "■ STOP",
        "↔ Counter / Compare",
        "🔎 Evidence",
        "🛡 Guardian",
        "🐘 HRM / JOOG",
    ):
        assert control in page

    assert 'method="post"' not in page.lower()
    assert "This surface performs no production write" in page
    assert "Human Authority remains final" in page


def test_war_room_ui_shows_safe_protocol_not_private_reasoning():
    page = Path("mission_control/templates/war_room.html").read_text(encoding="utf-8")

    for stage in (
        "Observe",
        "Classify",
        "Verify",
        "Fix/Plan",
        "Retest",
        "Record",
        "Learn",
    ):
        assert stage in page
    assert "Private chain-of-thought is never displayed" in page
