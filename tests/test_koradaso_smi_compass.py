"""KORADASO Compass: one first-party public SMI handoff, no new brain.

These tests cover live Flask template routing and code-level handoff boundaries.
Browser/device runtime proof remains an independent release gate.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "templates" / "koradaso_internet.html"
PUBLIC = ROOT / "templates" / "studio_public.html"


def test_compass_uses_existing_public_studio_and_does_not_submit_on_navigation(client):
    homepage = client.get("/koradaso")
    assert homepage.status_code == 200
    home = homepage.get_data(as_text=True)
    assert 'href="/studio?source=koradaso"' in home
    assert ">Ask SMI</a>" in home
    assert 'sessionStorage.setItem("koradaso.smi_draft.v1",draft)' in home
    assert 'sessionStorage.removeItem("koradaso.smi_draft.v1")' in home
    assert 'if(draft&&draft.length<=600)' in home
    assert 'window.location.assign("/studio?source=koradaso")' not in home
    assert "fetch('/studio/chat'" not in home

    assistant = client.get("/studio?source=koradaso")
    assert assistant.status_code == 200
    assert assistant.headers.get("Cache-Control") == "no-store"
    page = assistant.get_data(as_text=True)
    assert '<title>SMI · KORADASO Intelligence</title>' in page
    assert "KORADASO COMPASS" in page
    assert "Postcode → Global" in page
    assert "Ask SMI. Explore your world." in page
    assert "sessionStorage.getItem('koradaso.smi_draft.v1')" in page
    assert "sessionStorage.removeItem('koradaso.smi_draft.v1')" in page
    assert "input.value=draft.trim()" in page
    assert "if(koradasoMode)" in page
    assert "fetch('/studio/chat'" in page
    assert "submitStudio()" in page
    assert "/mission/" not in page


def test_compass_is_not_a_second_brain_or_founder_route(client):
    page = client.get("/studio").get_data(as_text=True)
    assert '<title>OAP Studio Intelligence</title>' in page
    assert "KORADASO COMPASS" not in page
    assert "Ask SMI. Explore your world." not in page
    assert "Private operational controls remain separate and inaccessible." in page
    source = PUBLIC.read_text(encoding="utf-8")
    for forbidden in (
        "/mission/smi", "/mission/ollama", "/mission/studio/generate",
        "getUserMedia", "localStorage.setItem('smi", "new SMI brain",
    ):
        assert forbidden not in source
    home = HOME.read_text(encoding="utf-8")
    assert 'class="public-smi" href="/studio?source=koradaso"' in home


def test_compass_keeps_seven_existing_suggestions_not_fake_tools(client):
    page = client.get("/studio?source=koradaso").get_data(as_text=True)
    assert page.count('data-smi-prompt="') == 7
    for prompt in ("Explain", "Research", "Truth Check", "Compare", "Plan", "Write", "Code Help"):
        assert f"<strong>{prompt}</strong>" in page
    assert "No live web access is implied" in page
    assert "Connection not checked" in page
    assert "never forwards this chat to an external AI fallback" in page
