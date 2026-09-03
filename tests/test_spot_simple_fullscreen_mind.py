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


def test_ollama_chat_is_true_fullscreen_compact_and_preserves_controls():
    compact = (ROOT / "mission_control" / "templates" / "ollama_chat.html").read_text()
    base = (ROOT / "mission_control" / "templates" / "ollama_chat_base.html").read_text()
    combined = compact + base

    assert "position:fixed!important;inset:0!important" in compact
    assert "height:100dvh!important" in compact
    assert "min-height:30px!important" in compact
    assert "max-height:88px!important" in compact
    assert "composerInput.rows=1" in compact
    assert "Shift+Enter" not in compact  # keyboard behavior is implemented, not exposed as noisy UI copy.
    assert "event.key==='Enter'&&!event.shiftKey" in compact
    assert "mobile-chats-toggle" in compact
    assert "Working safely" in compact
    assert "private reasoning is never exposed" in compact

    for control_id in (
        "plus-button",
        "code-button",
        "speaker-button",
        "mic-button",
        "stop-button",
        "send",
        "thinking",
        "history-list",
    ):
        assert f'id="{control_id}"' in combined
