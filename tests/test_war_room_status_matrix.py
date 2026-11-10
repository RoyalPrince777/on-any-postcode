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


def test_war_room_existing_page_contains_multiselect_divisions():
    assert 'id="smi-division-command"' in PAGE
    assert 'name="smi-division"' in PAGE
    assert 'id="smi-command-thinking"' in PAGE
    assert 'id="smi-command-extra"' in PAGE
    assert '/mission/war-room/divisions/route' in PAGE
    assert 'No agents executed.' in PAGE


def test_smi_auto_action_uses_selected_division_route_before_review():
    assert "const chosen = [...document.querySelectorAll('input[name=\"smi-division\"]:checked')]" in PAGE
    assert "if (!routeResponse.ok) throw new Error" in PAGE
    assert "'🟣 SMI AUTO · ' + selectedPlan.thinking_depth" in PAGE


def test_smi_cc_is_an_alias_of_existing_war_room_not_a_second_application():
    assert 'id="smi-cc"' in PAGE
    assert '/mission/smi-cc#smi-cc' in PAGE
    from app import app
    cc = next(rule for rule in app.url_map.iter_rules() if rule.rule == "/mission/smi-cc")
    old = next(rule for rule in app.url_map.iter_rules() if rule.rule == "/mission/war-room")
    assert cc.endpoint == old.endpoint
    assert "GET" in cc.methods and "GET" in old.methods


def test_smi_cc_submits_bounded_mission_context_without_execution():
    assert "mission: document.querySelector('.mission')?.value || ''" in PAGE
    assert "notes: document.getElementById('smi-command-extra').value" in PAGE
    import inspect

    from mission_control import views
    route = inspect.getsource(views.war_room_divisions_route)
    assert 'len(mission) > 2000' in route
    assert 'len(notes) > 2000' in route
    assert '"invalid_mission"' in route
    assert 'route_divisions' in route


def test_smi_cc_does_not_present_selected_21_checks_as_executed():
    assert "Thinking plan: ' + selectedPlan.selected_checks.length + ' checks selected · 0 verified executed" in PAGE
    assert 'Agent execution: NONE · Independent votes: NOT VERIFIED' in PAGE
    assert 'not equivalent to Thinking checks' in PAGE


def test_smi_dynamic_cc_uses_existing_war_room_with_minimal_front_door():
    assert "request.path == '/mission/smi-cc'" in PAGE
    assert "smi-dynamic-cc" in PAGE
    assert 'main.w>section:not(#smi-cc)' in PAGE
    assert '<section class="panel" id="smi-cc">' in PAGE
    assert "SMI Dynamic CC · ONE BRAIN" in PAGE
    assert "Send SMI your mission" in PAGE
    assert 'href="/mission/ollama"' in PAGE
    assert 'href="/mission/smi/status"' in PAGE
    assert 'href="/mission/war-room"' in PAGE
    for review in (
        "Truth Mode", "Red Team", "Devil’s Advocate", "Expose",
        "Verification", "Guardian", "Recovery"
    ):
        assert review in PAGE
    assert "not separate agents" in PAGE
    assert "Routing prepares a governed plan" in PAGE
    assert 'maxlength="2000" aria-label="War Room mission"' in PAGE
    assert PAGE.count('id="smi-cc"') == 1
