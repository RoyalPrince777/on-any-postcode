from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "mission_control/templates/ollama_chat.html"
CSS = ROOT / "mission_control/static/smi_review_cards.css"


def test_review_style_is_additive_and_loaded_after_existing_styles():
    page = WRAPPER.read_text(encoding="utf-8")
    assert "smi_review_cards.css" in page
    assert page.index("smi_command_centre.css") < page.index("smi_review_cards.css")
    for asset in ("smi_chat_final.js", "smi_chat_compat.js", "smi_canonical_controller.js", "smi_interaction_layer.js"):
        assert asset in page


def test_review_styles_are_scoped_and_mobile_safe():
    css = CSS.read_text(encoding="utf-8")
    for required in (".msg.assistant", "overflow-x:auto", ".receipt-card", "prefers-reduced-motion", "@media(max-width:600px)"):
        assert required in css
    assert "display:none" not in css

def test_styles_target_the_actual_smi_message_renderer():
    renderer = (ROOT / "mission_control/static/smi_chat_final.js").read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")
    for actual in ("md-h", "md-p", "md-list", "md-quote", "code-block", "md-inline-code", "md-link"):
        assert actual in renderer
        assert actual in css
    assert ".msg.receipt-card" in css
    assert ".smi-command-centre{" not in css
    assert ".composer{" not in css
    assert ".attach-menu{" not in css
