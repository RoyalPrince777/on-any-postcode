"""Founder entrance -> Personal SMI -> OAP Lab: bounded, truthful regression gate.

These checks demonstrate repository/rendered-document behaviour. A passing suite
does not claim device-level certification, external service success or Human
Authority's final decision.
"""
from html.parser import HTMLParser
from pathlib import Path

from flask import render_template

from mission_control import ollama_chat

ROOT = Path(__file__).resolve().parents[1]


class _DocumentShape(HTMLParser):
    def __init__(self):
        super().__init__()
        self.open_tags = []
        self.tags = []
        self.scripts_after_body = False
        self.body_closed = False

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        if tag == "script" and self.body_closed:
            self.scripts_after_body = True

    def handle_endtag(self, tag):
        if tag == "body":
            self.body_closed = True


def _render_chat(anonymous_client):
    with anonymous_client.application.test_request_context("/mission/ollama"):
        return render_template(
            "ollama_chat.html",
            chat=ollama_chat.get_public_ollama_chat(),
            oap_csrf_token="test-csrf",
        )


def test_truth_dedicated_founder_entry_reaches_chat_without_public_leak(anonymous_client):
    generic = anonymous_client.get("/auth")
    assert generic.status_code == 200
    assert "/mission/ollama" not in generic.get_data(as_text=True)

    dedicated = anonymous_client.get("/auth?next=/mission/ollama")
    assert dedicated.status_code == 200
    body = dedicated.get_data(as_text=True)
    assert 'name="next" value="/mission/ollama"' in body
    assert 'name="password" type="password"' in body
    assert 'name="csrf_token"' in body
    assert 'name="email"' not in body


def test_function_smi_has_one_well_formed_rendered_document(anonymous_client):
    html = _render_chat(anonymous_client)
    shape = _DocumentShape()
    shape.feed(html)
    assert shape.tags.count("html") == 1
    assert shape.tags.count("head") == 1
    assert shape.tags.count("body") == 1
    assert not shape.scripts_after_body
    assert html.rstrip().endswith("</html>")
    assert html.index("smi_chat_final.css") < html.index("</head>")
    assert html.index("smi_canonical_controller.js") < html.index("smi_command_centre.js")
    for control_id in ("plus-button", "attach-menu", "file-button", "image-button", "stop-button"):
        assert html.count('id="' + control_id + '"') == 1


def test_security_oap_lab_and_private_inspection_fail_closed(anonymous_client):
    for path in ("/mission/oap-lab", "/mission/founder-library"):
        response = anonymous_client.get(path, follow_redirects=False)
        assert response.status_code != 200
        assert "OAP Lab" not in response.get_data(as_text=True)


def test_stability_chat_first_and_mobile_entrance_guard():
    controller = (ROOT / "mission_control/static/smi_command_centre.js").read_text()
    auth = (ROOT / "templates/auth.html").read_text()
    assert 'toggle.addEventListener("click",()=>setOpen(!active))' in controller
    assert "setOpen(true);" not in controller
    assert "background-position:35% top" in auth
    assert "min-height:calc(100dvh - 112px)" in auth
    assert ":focus-visible" in auth


def test_integration_oap_lab_uses_existing_organs_not_new_brain(anonymous_client):
    with anonymous_client.application.test_request_context("/mission/oap-lab"):
        html = render_template(
            "oap_lab.html",
            research={"stage_count": 7, "capability_count": 10},
        )
    for label in ("Research Intelligence", "Matrix + War Room",
                  "Evidence before Green", "Founder asset index", "Human Lab"):
        assert label in html
    assert 'href="/mission/ollama"' in html
    assert 'href="/mission/war-room"' in html
    assert 'href="/mission/founder-library"' in html
    assert "not yet a full research-notebook" in html
    assert "another brain" in html


def test_compliance_do_not_grant_execution_from_research():
    from oap.smi import research_intelligence

    status = research_intelligence.status()
    assert status["consequential_execution_authority"] is False
    assert status["guardian_required"] is True
    assert status["human_authority_final"] is True


def test_learning_seven_star_work_has_explicit_provenance():
    lab = (ROOT / "mission_control/templates/oap_lab.html").read_text()
    wrapper = (ROOT / "mission_control/templates/ollama_chat.html").read_text()
    assert "not proof of end-to-end research" in lab
    assert "Simulated findings never grant execution authority" in lab
    assert '{% extends "ollama_chat_base.html" %}' in wrapper
    assert "{% block smi_extra_head %}" in wrapper
    assert "{% block smi_extra_body %}" in wrapper


def test_founder_can_open_actual_lab_route(client):
    response = client.get("/mission/oap-lab", follow_redirects=False)
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    page = response.get_data(as_text=True)
    assert "<h1>OAP Lab</h1>" in page
    assert "Research Intelligence" in page
    assert "Matrix + War Room" in page
    assert "Human Lab · planned division." in page


def test_signed_in_non_founder_cannot_open_lab(client, monkeypatch):
    from mission_control import neon_auth

    def ordinary_user(_cookie_header):
        return neon_auth.AuthResult(
            status_code=200,
            payload={
                "session": {"id": "non-founder-test"},
                "user": {
                    "id": "22222222-2222-4222-8222-222222222222",
                    "name": "OAP member",
                    "email": "ordinary-member@example.test",
                    "emailVerified": False,
                },
            },
        )

    monkeypatch.setattr(neon_auth, "get_session", ordinary_user)
    result = client.get("/mission/oap-lab", follow_redirects=False)
    assert result.status_code == 403
    assert result.get_json()["error"]["code"] == "human_authority_required"
    assert result.headers["Cache-Control"] == "no-store"


def test_plus_upload_aria_and_escape_focus_contract():
    base = (ROOT / "mission_control/templates/ollama_chat_base.html").read_text()
    canonical = (ROOT / "mission_control/static/smi_canonical_controller.js").read_text()

    assert 'aria-controls="attach-menu" aria-expanded="false"' in base
    assert base.count("plusButton.setAttribute('aria-expanded','false');") >= 3
    assert "imageInput.click()" in base
    assert "mediaInput.click()" in base
    assert "cameraInput.click()" in base
    assert "if(event.key!=='Escape'||!oapAttachMenu?.classList.contains('show'))return;" in canonical
    assert "oapCloseAttach();oapPlus?.focus();" in canonical
    assert canonical.count("oapPlus.addEventListener('click'") == 1


def test_upload_preparation_blocks_premature_send_and_stale_callbacks():
    base = (ROOT / "mission_control/templates/ollama_chat_base.html").read_text()
    controller = (ROOT / "mission_control/static/smi_canonical_controller.js").read_text()

    assert "let imagePreparing=false,attachmentPreparing=false,imagePrepareToken=0,mediaPrepareToken=0;" in base
    assert "const token=++imagePrepareToken" in base
    assert "const token=++mediaPrepareToken" in base
    assert "if(token!==imagePrepareToken)return;" in base
    assert "if(token!==mediaPrepareToken)return;selectedAttachment=prepared;" in base
    assert "++imagePrepareToken;++mediaPrepareToken;imagePreparing=false;attachmentPreparing=false" in base
    assert "if((typeof imagePreparing!=='undefined'&&imagePreparing)" in controller
    assert "(typeof attachmentPreparing!=='undefined'&&attachmentPreparing))" in controller
    assert "Preparing attachment · send after the preview appears" in controller

    submit = controller.index("async function oapSubmit(")
    guard = controller.index("Preparing attachment · send after the preview appears", submit)
    fetch = controller.index("await fetch(streamUrl", submit)
    assert submit < guard < fetch


def test_founder_form_fingerprint_distinguishes_passwords_after_flask_parsing(
    anonymous_client,
):
    from flask import request
    from mission_control import web_security

    limiter = web_security.SlidingWindowLimiter(
        limit=10,
        window_seconds=300,
        fingerprint_request_body=True,
    )
    app = anonymous_client.application
    signatures = []
    for password in ("wrong-alpha", "wrong-beta", "wrong-alpha"):
        with app.test_request_context(
            "/auth/sign-in",
            method="POST",
            data={"next": "/mission/ollama", "password": password},
        ):
            assert request.form["password"] == password
            signatures.append(limiter._request_fingerprint())
    assert signatures[0] != signatures[1]
    assert signatures[0] == signatures[2]
    assert all("wrong-" not in fingerprint for fingerprint in signatures)
