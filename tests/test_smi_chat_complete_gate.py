from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_complete_gate():
    wrapper = (ROOT / "mission_control/templates/ollama_chat.html").read_text()
    doc = (ROOT / "docs/SMI_CHAT_PRODUCT_COMPLETION.md").read_text()
    assert "Sovereign Megaverse Intelligence" in wrapper
    assert "Human Authority" in doc
