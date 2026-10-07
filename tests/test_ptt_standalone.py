from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_ptt_front_door_is_standalone_and_not_under_linkup():
    source = open("mission_control/ptt_routes.py", encoding="utf-8").read()
    template = open("mission_control/templates/ptt.html", encoding="utf-8").read()

    assert '@bp.get("/ptt")' in source
    assert 'data-oap-ptt-standalone="true"' in template
    assert 'data-oap-ptt-endpoint="/ptt"' in template
    assert 'data-oap-ptt-status-endpoint="/ptt/status"' in template
    assert "Hold to talk" in template
    assert 'href="/world"' in template
    assert "/the-link" not in template
    assert "/linkup" not in template


def test_ptt_front_door_reuses_existing_contact_and_voice_governance():
    source = open("mission_control/ptt_routes.py", encoding="utf-8").read()
    voice = open("mission_control/link_voice.py", encoding="utf-8").read()

    assert "link_relationships.list_for_identity" in source
    assert 'relation.get("status") != "accepted"' in source
    assert "product_store.linkup_dashboard" in source
    assert "link_youth_safety.require_contact_allowed" in voice
    assert "linkup_safety.blocked_between" in voice
    assert "accepted_between" in voice


def test_legacy_linkup_ptt_intent_redirects_to_standalone_ptt():
    app_source = open("app.py", encoding="utf-8").read()

    assert 'if str(request.args.get("intent") or "").strip().casefold() == "ptt":' in app_source
    assert 'return redirect("/ptt")' in app_source


def test_ptt_blueprint_is_registered():
    init_source = open("mission_control/__init__.py", encoding="utf-8").read()

    assert "from .ptt_routes import bp as ptt_bp" in init_source
    assert "app.register_blueprint(ptt_bp)" in init_source
