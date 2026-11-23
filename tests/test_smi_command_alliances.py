"""Founder SMI alliance view reuses canonical agents, not fabricated workers."""
from pathlib import Path

from mission_control import agents, intelligence_alliances

ROOT = Path(__file__).resolve().parents[1]


def test_six_founder_alliances_preserve_passports_and_authority():
    before = tuple((x["agent_id"], x["name"]) for x in agents.AGENT_REGISTRY)
    board = intelligence_alliances.get_smi_command_alliances()
    rows = board["members"]
    assert board["brain"] == "SMI"
    assert board["scope"] == "founder_private_read_only"
    assert tuple(x["name"] for x in rows) == (
        "Shere Khan", "Agent Smiths", "Bagheera", "Octopus",
        "Queen Bee", "The Twins",
    )
    by_name = {x["name"]: x for x in rows}
    for name, passport in (
        ("Shere Khan", "JUNGLE-SHERE-KHAN-001"),
        ("Bagheera", "JUNGLE-BAGHEERA-001"),
        ("Octopus", "ANIMAL-OCTOPUS-001"),
    ):
        assert by_name[name]["passport_id"] == passport
        assert by_name[name]["passport_status"] == "registered"
        assert by_name[name]["runtime_verified"] is False
        assert by_name[name]["execution_granted"] is False
    for name in ("Agent Smiths", "Queen Bee", "The Twins"):
        assert by_name[name]["passport_id"] is None
        assert by_name[name]["passport_status"] == "advisory_only"
        assert by_name[name]["directory_url"] is None
        assert by_name[name]["runtime_verified"] is False
    assert by_name["Agent Smiths"]["members"] == (
        "Agent Smith", "Brown", "Jones", "Johnson", "Jackson", "Thompson"
    )
    assert by_name["The Twins"]["members"] == ("Twin One", "Twin Two")
    assert by_name["Queen Bee"]["members"] == ("Queen Bee",)
    assert by_name["Agent Smiths"]["allies"] == ("Bagheera", "Seraph", "Guardian")
    assert by_name["The Twins"]["allies"] == ("Fox", "Spider", "Architect")
    assert board["registered_agent_count_unchanged"] == agents.LOCKED_AGENT_COUNT
    assert tuple((x["agent_id"], x["name"]) for x in agents.AGENT_REGISTRY) == before
    assert board["can_approve"] is False
    assert board["can_execute"] is False
    assert board["workers_started"] is False
    assert board["independent_votes_proven"] is False
    assert board["guardian_hrm_required"] is True
    assert board["founder_final_required"] is True


def test_alliance_route_is_founder_only_and_no_store(client):
    response = client.get("/mission/smi/alliances/status")
    assert response.status_code in (302, 401, 403)
    assert "Shere Khan" not in response.get_data(as_text=True)
    source = (ROOT / "mission_control" / "views.py").read_text(encoding="utf-8")
    assert '@bp.get("/smi/alliances/status")\n@web_security.login_required(api=True, founder_only=True)' in source
    assert 'jsonify(intelligence_alliances.get_smi_command_alliances())' in source
    assert '_no_store(make_response(jsonify(intelligence_alliances' in source


def test_command_room_contains_single_read_only_alliance_view():
    ui = (ROOT / "mission_control" / "static" / "smi_command_centre.js").read_text(encoding="utf-8")
    css = (ROOT / "mission_control" / "static" / "smi_command_centre.css").read_text(encoding="utf-8")
    template = (ROOT / "mission_control" / "templates" / "ollama_chat.html").read_text(encoding="utf-8")
    assert '["🤝 Alliances","alliances"]' in ui
    assert 'const alliancePanel=document.createElement("section")' in ui
    assert 'universe.after(alliancePanel)' in ui
    assert 'refreshAllianceRoster()' in ui
    assert 'credentials:"same-origin"' in ui
    assert 'cache:"no-store"' in ui
    assert 'response.ok' in ui
    assert "no active agents inferred" in ui
    assert 'panel.dataset.alliancesOpen="false"' in ui
    assert 'new RegExp("^/mission/agents[?]family=' in ui
    assert 'data-alliances-open="true"' in css
    assert 'smi-command-alliance-panel:not([hidden])' in css
    assert "alliancesUrl:{{ url_for('mission_control.smi_command_alliances_status')|tojson }}" in template
    assert "Green. Guardian/HRM and Founder Final" in ui


def test_no_public_alliance_disclosure_in_studio_or_browser():
    for path in (
        ROOT / "templates" / "studio_public.html",
        ROOT / "templates" / "koradaso_internet.html",
    ):
        source = path.read_text(encoding="utf-8")
        assert "/mission/smi/alliances/status" not in source
