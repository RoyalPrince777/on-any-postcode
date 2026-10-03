from pathlib import Path

PAGE = Path("mission_control/templates/war_room.html").read_text(encoding="utf-8")


def test_war_room_status_matrix_is_additive_and_exposes_canonical_mission_flow():
    for marker in (
        "War Room Status Matrix",
        "UI · UX · Buttons · Functions · Proof · Authority",
        "1 · Mission",
        "2 · Continue",
        "3 · Risk / Guardian",
        "4 · War Room / Judgement",
        "5 · Founder Final",
        "6 · Recovery / Rollback",
        "7 · Outcome / Learning",
        "data-wr-control-count",
        "data-wr-function-count",
    ):
        assert marker in PAGE


def test_war_room_upgrade_preserves_existing_governed_controls():
    for marker in (
        'data-action="smi-auto"',
        'data-depth="3"',
        'data-depth="7"',
        'data-depth="21"',
        "⚔️ WAR ROOM",
        "7× DEEP DIVE",
        "VOTE BOARD",
        'data-action="aegis-check"',
        'data-action="green-gate"',
        'data-proof="rollback-recovery"',
        'data-proof="runtime-guard"',
        'data-proof="isolation-recovery"',
        "js-complete-green",
        "js-founder-final",
        "RESEARCH",
        "Alignment",
        "Function Health",
        "HRM / JOOG",
        "Simulation chamber",
        "Seven canonical judge seats",
        "21 review lenses",
    ):
        assert marker in PAGE


def test_war_room_status_matrix_uses_existing_evidence_not_fake_percentages():
    assert "{{ war_room.summary.overall_evidence_score }}%" in PAGE
    assert "{{ war_room.summary.runtime_verified }}/{{ war_room.summary.rated_areas }}" in PAGE
    assert "{{ war_room.summary.operationally_certified }}/{{ war_room.summary.rated_areas }}" in PAGE
    assert "a visible button, high percentage, unanimous vote or attractive dashboard never creates proof" in PAGE
