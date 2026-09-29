from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = (ROOT / "mission_control" / "templates" / "linkup.html").read_text()
INCOMING = (ROOT / "static" / "linkup_incoming.js").read_text()
OPTIONAL = (ROOT / "static" / "linkup_optional.js").read_text()
MESSENGER = (ROOT / "static" / "linkup_messenger.js").read_text()


def test_linkup_optional_features_are_not_eager_loaded():
    assert "filename='linkup_optional.js'" in TEMPLATE
    assert "filename='linkup_presence.js'" not in TEMPLATE
    assert "filename='linkup_voice.js'" not in TEMPLATE
    assert "filename='linkup_share.js'" not in TEMPLATE


def test_linkup_user_surface_hides_internal_green_gate_chrome():
    assert "7-Star Gate" not in TEMPLATE
    assert "linkup-stars-grid" not in TEMPLATE


def test_incoming_polling_pauses_when_page_is_hidden():
    assert "document.hidden" in INCOMING
    assert "visibilitychange" in INCOMING
    assert "setInterval(poll, 5000)" not in INCOMING


def test_optional_runtime_loads_on_engagement_or_idle():
    assert "oap:linkup-engaged" in OPTIONAL
    assert "requestIdleCallback" in OPTIONAL
    assert "/static/linkup_voice.js" in OPTIONAL
    assert "/static/linkup_presence.js" in OPTIONAL
    assert "/static/linkup_share.js" in OPTIONAL
    assert "oap:linkup-engaged" in MESSENGER
