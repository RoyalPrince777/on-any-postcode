import uuid
from pathlib import Path

from mission_control import web_security

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
    assert "<strong>No sign-in.</strong>" in body
    assert "Create pairing code" in body
    assert "Join PTT" in body
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


def _csrf_for(client):
    token = "ptt-guest-csrf-token-value-1234567890"
    with client.session_transaction() as current_session:
        current_session[web_security.CSRF_SESSION_KEY] = token
    return token


def test_anonymous_ptt_can_create_pairing_code(anonymous_client, monkeypatch):
    from mission_control import ptt_routes

    identity = str(uuid.uuid4())
    monkeypatch.setattr(
        ptt_routes.ptt_guest,
        "create_invite",
        lambda: {
            "identity_id": identity,
            "code": "12345678",
            "expires_at": "2099-01-01T00:00:00+00:00",
        },
    )
    token = _csrf_for(anonymous_client)
    response = anonymous_client.post(
        "/ptt/pair/create",
        json={},
        headers={"X-OAP-CSRF": token},
    )
    assert response.status_code == 201
    assert response.get_json()["code"] == "12345678"
    with anonymous_client.session_transaction() as current_session:
        assert current_session[ptt_routes.PTT_GUEST_ID_KEY] == identity
        assert current_session[ptt_routes.PTT_GUEST_CODE_KEY] == "12345678"


def test_anonymous_ptt_can_join_pairing_code(anonymous_client, monkeypatch):
    from mission_control import ptt_routes

    identity = str(uuid.uuid4())
    peer = str(uuid.uuid4())
    observed = {}
    monkeypatch.setattr(
        ptt_routes.ptt_guest,
        "join_invite",
        lambda code, existing: observed.update(code=code, existing=existing) or {
            "active": True,
            "identity_id": identity,
            "peer_id": peer,
            "relationship_id": str(uuid.uuid4()),
            "expires_at": "2099-01-01T00:00:00+00:00",
        },
    )
    token = _csrf_for(anonymous_client)
    response = anonymous_client.post(
        "/ptt/pair/join",
        json={"code": "12345678"},
        headers={"X-OAP-CSRF": token},
    )
    assert response.status_code == 200
    assert response.get_json()["active"] is True
    assert response.get_json()["peer_id"] == peer
    assert observed["code"] == "12345678"
    with anonymous_client.session_transaction() as current_session:
        assert current_session[ptt_routes.PTT_GUEST_ID_KEY] == identity


def test_ptt_pair_status_and_stop_are_no_sign_in(anonymous_client, monkeypatch):
    from mission_control import ptt_routes

    identity = str(uuid.uuid4())
    peer = str(uuid.uuid4())
    with anonymous_client.session_transaction() as current_session:
        current_session[ptt_routes.PTT_GUEST_ID_KEY] = identity
    monkeypatch.setattr(
        ptt_routes.ptt_guest,
        "invite_state",
        lambda who, code: {
            "active": True,
            "identity_id": who,
            "peer_id": peer,
            "code": None,
            "expires_at": "2099-01-01T00:00:00+00:00",
        },
    )
    monkeypatch.setattr(ptt_routes.ptt_guest, "stop", lambda who: who == identity)

    status = anonymous_client.get("/ptt/pair/status")
    assert status.status_code == 200
    assert status.get_json()["active"] is True
    assert status.get_json()["peer_id"] == peer

    token = _csrf_for(anonymous_client)
    stopped = anonymous_client.post(
        "/ptt/pair/stop",
        json={},
        headers={"X-OAP-CSRF": token},
    )
    assert stopped.status_code == 200
    assert stopped.get_json()["stopped"] is True


def test_ptt_guest_ui_exposes_talk_history_and_disconnect(monkeypatch, anonymous_client):
    from mission_control import ptt_routes

    identity = str(uuid.uuid4())
    peer = str(uuid.uuid4())
    with anonymous_client.session_transaction() as current_session:
        current_session[ptt_routes.PTT_GUEST_ID_KEY] = identity
    monkeypatch.setattr(
        ptt_routes.ptt_guest,
        "invite_state",
        lambda who, code: {
            "active": True,
            "identity_id": who,
            "peer_id": peer,
            "code": None,
            "expires_at": "2099-01-01T00:00:00+00:00",
        },
    )

    response = anonymous_client.get("/ptt")
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "CONNECTED · TEMPORARY PTT" in body
    assert "HOLD TO TALK" in body
    assert 'data-oap-voice-list' in body
    assert 'action="/ptt/pair/stop"' in body


def test_standalone_ptt_browser_runtime_uses_ptt_readiness_and_guest_endpoints():
    source = _read("static/linkup_voice.js")
    assert 'const transportReady = kind === "ptt" ? state.pttReady : state.ready;' in source
    assert 'const listEndpoint = standalonePtt ? "/ptt/voice" : "/linkup/voice";' in source
    assert 'const mediaBase = standalonePtt ? "/ptt/voice" : "/linkup/voice";' in source
    assert 'window.setInterval(() => renderVoiceList(peerId), 2000);' in source
