from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
PUBLIC = ROOT / "templates" / "studio_public.html"
PRIVATE_VIEWS = ROOT / "mission_control" / "views.py"


def test_public_studio_route_exists_without_private_authority():
    app = APP.read_text(encoding="utf-8")
    page = PUBLIC.read_text(encoding="utf-8")
    assert '@app.get("/studio")' in app
    assert "OAP Studio Intelligence" in page
    assert "Public AI experience" in page
    assert "What can OAP help you create?" in page
    assert "disabled" in page


def test_koradaso_intelligence_reuses_public_studio_without_private_authority(client):
    """KORADASO is a scoped presentation, not a second brain or private gateway."""
    response = client.get("/studio?source=koradaso")
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "<title>KORADASO Intelligence</title>" in page
    assert "One public SMI" in page
    assert 'id="smi-update"' in page
    assert page.count('data-smi-prompt="') == 7
    assert "fetch('/studio/chat'" in page
    assert "/mission/" not in page
    assert "Private operational controls remain separate and inaccessible." in page
    standard = client.get("/studio")
    assert standard.status_code == 200
    assert "<title>OAP Studio Intelligence</title>" in standard.get_data(as_text=True)
    app = APP.read_text(encoding="utf-8")
    assert 'request.args.get("source") == "koradaso"' in app
    assert 'render_template("studio_public.html"' not in app  # same template, scoped flag


def test_public_studio_does_not_expose_private_smi_controls():
    page = PUBLIC.read_text(encoding="utf-8")
    for forbidden in (
        "/mission/studio/generate",
        "/mission/studio/status",
        "/mission/ollama",
        "Sovereign Megaverse Intelligence",
        "War Room",
        "JOOG/HRM",
        "private agents",
        "infrastructure",
        "Founder controls",
    ):
        assert forbidden not in page
    assert "Private operational controls remain separate and inaccessible." in page
    assert 'id="smi-update"' in page  # Public refresh only, no Founder authority.
    assert "/mission/" not in page


def test_public_smi_seven_recommendations_prefill_real_chat_not_unready_media():
    page = PUBLIC.read_text(encoding="utf-8")
    assert page.count('data-smi-prompt="') == 7
    for title in ("Explain", "Research", "Truth Check", "Compare",
                  "Plan", "Write", "Code Help"):
        assert f"<strong>{title}</strong>" in page
    assert "document.querySelectorAll('[data-smi-prompt]')" in page
    assert "input.value=button.getAttribute('data-smi-prompt')" in page
    assert "input.focus()" in page
    assert "Replace the current unsent message" in page
    assert "fetch('/studio/chat'" in page
    assert 'type="button" data-smi-prompt=' in page
    assert '<div class="tool"><strong>Imagine' not in page
    assert '<div class="tool"><strong>Bring Alive' not in page



def test_koradaso_public_smi_local_response_preserves_public_authority(monkeypatch):
    """Mock the real public gateway, never a live or offline model claim."""
    from mission_control import public_studio_runtime, oap_inference_gateway

    called = {}
    monkeypatch.setattr(public_studio_runtime, "_allow", lambda key: True)

    def local(message, history, brain, *, code_mode=False):
        called["brain"] = brain
        called["message"] = message
        return "Local first-party response"

    def unused_bridge(*args, **kwargs):
        raise AssertionError("Local success must not call the bridge")

    monkeypatch.setattr(oap_inference_gateway, "_call_local_public", local)
    monkeypatch.setattr(oap_inference_gateway, "_call_bridge_public", unused_bridge)

    result = public_studio_runtime.ask(
        "Explain this topic clearly: local search", rate_key="test-koradaso",
    )
    assert result["answer"] == "Local first-party response"
    assert result["brain"] == "SMI"
    assert result["smi_surface"] == "public"
    assert result["private_smi_used"] is False
    assert result["execution_authority"] is False
    assert result["memory_saved"] is False
    assert called["brain"]["surface"] == "public"
    assert called["brain"]["execution_authority"] is False
    assert called["brain"]["private_memory_allowed"] is False


def test_koradaso_public_smi_providers_unavailable_fail_closed(monkeypatch):
    import pytest
    from mission_control import public_studio_runtime, oap_inference_gateway

    monkeypatch.setattr(public_studio_runtime, "_allow", lambda key: True)
    monkeypatch.setattr(oap_inference_gateway, "FALLBACK_ENABLED", False)

    def offline(*args, **kwargs):
        raise RuntimeError("provider_offline")

    monkeypatch.setattr(oap_inference_gateway, "_call_local_public", offline)
    monkeypatch.setattr(oap_inference_gateway, "_call_bridge_public", offline)
    with pytest.raises(public_studio_runtime.PublicStudioUnavailable) as exc:
        public_studio_runtime.ask("Truth-check the available evidence", rate_key="test-koradaso")
    assert str(exc.value) == "public_smi_unavailable"


def test_private_studio_generation_remains_founder_only():
    views = PRIVATE_VIEWS.read_text(encoding="utf-8")
    assert '@bp.post("/studio/generate")' in views
    assert "login_required(api=True, founder_only=True)" in views


def test_public_chat_endpoint_is_bounded():
    app = APP.read_text(encoding="utf-8")
    runtime = (ROOT / "mission_control" / "public_studio_runtime.py").read_text(encoding="utf-8")
    page = PUBLIC.read_text(encoding="utf-8")

    assert '@app.post("/studio/chat")' in app
    assert "web_security.csrf_valid(request)" in app
    assert "public_studio_runtime.ask" in app
    assert "PublicStudioRateLimited" in app
    assert "Cache-Control" in app

    assert "no identity creation" in runtime
    assert "no JOOG/HRM write" in runtime
    assert "private_smi_used" in runtime
    assert '"private_smi_used": False' in runtime
    assert '"execution_authority": False' in runtime
    assert "OPENAI_API_KEY" in runtime

    assert "fetch('/studio/chat'" in page
    assert "'X-OAP-CSRF':csrf" in page
    assert "/mission/" not in page


def test_public_chat_intelligence_is_bounded():
    runtime = (ROOT / "mission_control" / "public_studio_runtime.py").read_text(encoding="utf-8")
    app = APP.read_text(encoding="utf-8")
    page = PUBLIC.read_text(encoding="utf-8")

    assert "def _chat_mode(" in runtime
    assert "def _bounded_history(" in runtime
    assert "history[-8:]" in runtime
    assert "intelligence_lenses.public_route" in runtime
    assert '"execution_authority": False' in runtime
    assert '"private_reasoning_exposed": False' in runtime
    assert "history=payload.get(\"history\")" in app
    assert "const history=[];" in page
    assert "history.slice(-8)" in page
    assert "Chat Intelligence" in page


def test_specialist_intelligence_router_marks_unready_media():
    runtime = (ROOT / "mission_control" / "public_studio_runtime.py").read_text(encoding="utf-8")
    page = PUBLIC.read_text(encoding="utf-8")

    for name in (
        "Research Intelligence",
        "Creation Intelligence",
        "Code Intelligence",
        "Learning Intelligence",
        "Planning Intelligence",
        "Language Intelligence",
        "Location Intelligence",
        "Movement Intelligence",
        "Commerce Intelligence",
        "Creator Intelligence",
        "Safety Intelligence",
        "Truth-Light Intelligence",
        "Tool Intelligence",
    ):
        assert name in runtime

    for locked in (
        '"image": {"label": "Image Intelligence", "ready": False}',
        '"video": {"label": "Video Intelligence", "ready": False}',
        '"audio": {"label": "Audio Intelligence", "ready": False}',
        '"file": {"label": "File Intelligence", "ready": False}',
        '"voice": {"label": "Voice Intelligence", "ready": False}',
    ):
        assert locked in runtime

    assert "def _specialist_route(" in runtime
    assert "s.ready===false?' 🔒':''" in page


def test_public_studio_routes_through_shared_smi_gateway():
    runtime = (ROOT / "mission_control" / "public_studio_runtime.py").read_text(encoding="utf-8")
    gateway = (ROOT / "mission_control" / "oap_inference_gateway.py").read_text(encoding="utf-8")

    assert "oap_inference_gateway as smi_inference" in runtime
    assert "smi_inference.generate_public(" in runtime
    assert '"brain": "SMI"' in runtime
    assert '"smi_surface": "public"' in runtime

    assert "def generate_public(" in gateway
    assert '"surface"] = "public"' in gateway
    assert '"execution_authority"] = False' in gateway
    assert '"private_memory_allowed"] = False' in gateway
    assert "PUBLIC_SMI_SYSTEM" in gateway
    assert "public users have " in gateway
    assert "no Founder authority" in gateway
