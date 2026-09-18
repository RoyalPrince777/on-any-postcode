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


def test_public_studio_does_not_expose_private_smi_controls():
    page = PUBLIC.read_text(encoding="utf-8")
    for forbidden in (
        "/mission/studio/generate",
        "/mission/studio/status",
        "/mission/ollama",
        "Sovereign Megaverse Intelligence",
        "SMI",
        "War Room",
        "JOOG/HRM",
        "private agents",
        "infrastructure",
        "Founder controls",
    ):
        assert forbidden not in page
    assert "Private operational controls remain separate and inaccessible." in page


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
