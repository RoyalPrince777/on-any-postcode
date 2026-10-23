from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_ptt_front_door_is_standalone_and_not_under_linkup():
    source = _read("mission_control/ptt_routes.py")
    template = _read("mission_control/templates/ptt.html")

    assert '@bp.get("/ptt")' in source
    assert 'data-oap-ptt-standalone="true"' in template
    assert 'data-oap-ptt-endpoint="/ptt"' in template
    assert 'data-oap-ptt-status-endpoint="/ptt/status"' in template
    assert 'oap_manifest_url = "/ptt/manifest.webmanifest"' in template
    assert "Install OAP PTT" in template
    assert "Hold to talk" in template
    assert 'href="/world"' in template
    assert "/the-link" not in template
    assert "/linkup" not in template


def test_ptt_front_door_is_public_install_shell_without_sign_in(anonymous_client):
    response = anonymous_client.get("/ptt")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "Install OAP PTT" in body
    assert "No sign-in required to install OAP PTT." in body
    assert "Temporary device-to-device pairing is not connected yet" in body
    assert 'rel="manifest" href="/ptt/manifest.webmanifest"' in body
    assert response.headers["Cache-Control"] == "no-store"


def test_ptt_front_door_reuses_existing_contact_and_voice_governance():
    source = _read("mission_control/ptt_routes.py")
    voice = _read("mission_control/link_voice.py")

    assert "link_relationships.list_for_identity" in source
    assert 'relation.get("status") != "accepted"' in source
    assert "product_store.linkup_dashboard" in source
    assert "link_youth_safety.require_contact_allowed" in voice
    assert "linkup_safety.blocked_between" in voice
    assert "accepted_between" in voice


def test_legacy_linkup_ptt_intent_redirects_to_standalone_ptt():
    app_source = _read("app.py")

    assert 'if str(request.args.get("intent") or "").strip().casefold() == "ptt":' in app_source
    assert 'return redirect("/ptt")' in app_source


def test_ptt_blueprint_is_registered():
    init_source = _read("mission_control/__init__.py")

    assert "from .ptt_routes import bp as ptt_bp" in init_source
    assert "app.register_blueprint(ptt_bp)" in init_source


def test_ptt_contacts_api_reuses_canonical_accepted_contact_source():
    source = _read("mission_control/ptt_routes.py")

    assert '@bp.get("/ptt/contacts")' in source
    assert "@web_security.login_required(api=True)" in source
    assert "web_security.authenticated_identity()" in source
    assert "jsonify(contacts=_accepted_contacts(identity_id))" in source
    assert 'response.headers["Cache-Control"] = "no-store"' in source


def test_ptt_contacts_api_rejects_anonymous_access(anonymous_client):
    response = anonymous_client.get("/ptt/contacts")
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "authentication_required"
    assert response.headers["Cache-Control"] == "no-store"


def test_ptt_contacts_api_returns_only_canonical_contacts(client, monkeypatch):
    from mission_control import ptt_routes

    expected = [
        {
            "identity_id": "22222222-2222-4222-8222-222222222222",
            "display_name": "OAP Contact",
            "card_id": "OAP-CARD-2222",
        }
    ]
    observed = {}

    def fake_contacts(identity_id):
        observed["identity_id"] = identity_id
        return expected

    monkeypatch.setattr(ptt_routes, "_accepted_contacts", fake_contacts)
    response = client.get("/ptt/contacts")

    assert response.status_code == 200
    assert response.get_json() == {"contacts": expected}
    assert observed["identity_id"] == "11111111-1111-4111-8111-111111111111"
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
