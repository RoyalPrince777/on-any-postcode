from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_smi_live_chat_uses_status_free_artwork_and_hides_status_surfaces():
    wrapper = (ROOT / "mission_control/templates/ollama_chat.html").read_text(encoding="utf-8")
    css = (ROOT / "mission_control/static/smi_live_chat_dashboard.css").read_text(encoding="utf-8")
    assert "oap/smi_live_chat_dashboard.jpg" in wrapper
    assert ".chatbox::before" in css
    assert "clip-path:polygon(63.4% 20%,77.5% 20%,77.5% 67%" in css
    assert ".chatbox::before{display:none}" in css
    assert "visibleLiveStatus:false" in wrapper
    assert "Live Intelligence Monitor" not in wrapper
    assert ".smi-status-backdrop,.smi-dashboard-layer{display:none!important}" in css
