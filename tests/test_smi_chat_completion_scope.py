from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_completion_slice_files_are_frontend_contract_and_tests_only():
    doc = (ROOT / "docs/SMI_CHAT_PRODUCT_COMPLETION.md").read_text()
    assert "does not change Founder authentication" in doc
    assert "database schema" in doc


def test_existing_governance_language_remains_on_founder_surface():
    base = (ROOT / "mission_control/templates/ollama_chat_base.html").read_text()
    assert "Human Authority remains final" in base
    assert "Aegis protects" in base
    assert "HRM remembers" in base
