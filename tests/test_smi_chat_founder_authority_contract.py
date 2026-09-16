from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_founder_surface_keeps_human_authority_language():
    base = (ROOT / "mission_control/templates/ollama_chat_base.html").read_text()
    controller = (ROOT / "mission_control/static/smi_canonical_controller.js").read_text()
    assert "Human Authority remains final" in base
    assert "Response stopped by Human Authority" in controller


def test_completion_doc_does_not_expand_execution_authority():
    doc = (ROOT / "docs/SMI_CHAT_PRODUCT_COMPLETION.md").read_text()
    assert "execution authority" in doc
    assert "does not change" in doc
