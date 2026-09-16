from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_completion_slice_has_canonical_identity_and_truth_record():
    assert (ROOT / "mission_control/static/smi_product_identity.js").exists()
    assert (ROOT / "docs/SMI_CHAT_PRODUCT_COMPLETION.md").exists()
    wrapper = (ROOT / "mission_control/templates/ollama_chat.html").read_text()
    assert "smi_product_identity.js" in wrapper
