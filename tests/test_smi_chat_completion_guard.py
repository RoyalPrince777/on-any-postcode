from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_completion_guard():
    wrapper = (ROOT / "mission_control/templates/ollama_chat.html").read_text()
    controller = (ROOT / "mission_control/static/smi_canonical_controller.js").read_text()
    assert "smi_product_identity.js" in wrapper
    assert "singleSubmitOwner:true" in controller
