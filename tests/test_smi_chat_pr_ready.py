from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_pr_ready_contract():
    wrapper = (ROOT / "mission_control/templates/ollama_chat.html").read_text()
    assert "smi_product_identity.js" in wrapper
    assert "smi_canonical_controller.js" in wrapper
    assert (ROOT / "docs/SMI_CHAT_PRODUCT_COMPLETION.md").exists()
