from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_review_ready():
    wrapper = (ROOT / "mission_control/templates/ollama_chat.html").read_text()
    assert "smi_product_identity.js" in wrapper
    assert "smi_canonical_controller.js" in wrapper
