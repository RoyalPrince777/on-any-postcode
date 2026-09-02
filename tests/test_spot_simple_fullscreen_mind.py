from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_spot_is_simple_dashboard_without_inline_forms():
    html = (ROOT / "mission_control" / "templates" / "spot.html").read_text()
    assert "Open what you need" in html
    assert "More in The Spot" in html
    assert "Browse first; open a form only when you choose an action." in html
    assert "<form" not in html
    for slug in (
        "pulse",
        "signal",
        "maps-weather-travel",
        "movement-delivery",
        "events",
        "market",
        "discovery",
        "my-world",
    ):
        assert slug in html


def test_ollama_chat_is_full_viewport_and_preserves_controls():
    html = (ROOT / "mission_control" / "templates" / "ollama_chat.html").read_text()
    assert "height:100dvh" in html
    assert "max-width:none" in html
    assert ".smi-hero{display:none}" in html
    assert "max-height:none" in html
    assert 'id="plus-button"' in html
    assert 'id="mic-button"' in html
    assert 'id="stop-button"' in html
    assert 'id="send"' in html
    assert 'id="thinking"' in html
    assert 'id="history-list"' in html
    assert "Code proposal mode" in html
