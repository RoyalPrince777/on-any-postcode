from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

JS = ROOT / "mission_control" / "static" / "smi_noise_strip.js"
CSS = ROOT / "mission_control" / "static" / "smi_noise_strip.css"
TEMPLATE = ROOT / "mission_control" / "templates" / "ollama_chat.html"


def test_noise_strip_js_is_local_ui_only():
    js = JS.read_text(encoding="utf-8")
    forbidden = (
        "fetch(",
        "XMLHttpRequest",
        "WebSocket",
        "EventSource",
        "navigator.sendBeacon",
        "document.cookie",
        "localStorage",
        "sessionStorage",
        "eval(",
        "new Function",
        "location.href",
        "location.assign",
        "location.replace",
        "window.open(",
    )
    for token in forbidden:
        assert token not in js


def test_noise_strip_does_not_own_routes_or_credentials():
    js = JS.read_text(encoding="utf-8")
    template = TEMPLATE.read_text(encoding="utf-8")

    assert "csrfToken" not in js
    assert "Authorization" not in js
    assert "credentials:" not in js
    assert "warRoomUrl" in template
    assert "greenGateUrl" in template
    assert "proposalBranchUrl" in template
    assert "executeUrl" in template


def test_noise_strip_css_only_hides_known_duplicate_chrome():
    css = CSS.read_text(encoding="utf-8")
    hidden_selectors = (
        ".status-row .mode-tools",
        "#display-name",
        ".attach-section-label",
        ".attach-divider",
        ".attach-note",
        ".chat-head #provider-state",
        ".thinking-log",
    )
    for selector in hidden_selectors:
        assert selector in css

    for protected in (
        "#plus-button",
        "#mic-button",
        "#pause-button",
        "#stop-button",
        "#send",
        "#attach-menu",
        "#studio-creation-strip",
    ):
        assert protected in css


def test_noise_strip_preserves_upgrade_only_control_contract():
    js = JS.read_text(encoding="utf-8")

    assert "upgradeOnly:true" in js
    assert "addEventListener('keydown'" not in js
    assert "canonical controller" in js
    assert "Control check failed" in js
