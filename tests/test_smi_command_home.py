"""SMI command homepage preview contract; no live health claims."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_smi_command_home_route_is_isolated():
    app_source = (ROOT / "app.py").read_text(encoding="utf-8")
    assert '@app.get("/smi-home")' in app_source
    assert 'return render_template("smi_command_home.html")' in app_source
    assert '@app.get("/world")' in app_source


def test_smi_home_captain_and_world_controls():
    html = (ROOT / "templates" / "smi_command_home.html").read_text(encoding="utf-8")
    for label in ("Captain ALL IN", "Enter My World", "Explore OAP World",
                  "SOVEREIGN MEGAVERSE INTELLIGENCE", "Founder Final"):
        assert label in html
    assert 'aria-modal="true"' in html
    assert 'prefers-reduced-motion' in html
    assert 'data-open="captain"' in html
    assert 'data-open="menu"' in html


def test_smi_home_never_claims_synthetic_live_health():
    html = (ROOT / "templates" / "smi_command_home.html").read_text(encoding="utf-8")
    assert "No invented statistics" in html
    assert "All Systems Operational" not in html
    assert "100% System Health" not in html


def test_world_drawer_has_first_party_search_and_hidden_results():
    html = (ROOT / "templates" / "smi_command_home.html").read_text(encoding="utf-8")
    assert "Find OAP World destination" in html
    assert "search.addEventListener('input'" in html
    assert "a.hidden=" in html
    assert ".links a[hidden]{display:none}" in html


def test_search_is_keyboard_accessible_in_modal_drawer():
    html = (ROOT / "templates" / "smi_command_home.html").read_text(encoding="utf-8")
    assert "querySelectorAll('a,button,input')" in html
    assert "search||document.getElementById('close')" in html
    assert "previous?.focus()" in html
