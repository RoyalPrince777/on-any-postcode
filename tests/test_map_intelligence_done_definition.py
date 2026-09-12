from pathlib import Path


def test_done_definition_separates_repository_and_production_green():
    text = Path("docs/OAP_MAP_INTELLIGENCE_DONE_DEFINITION.md").read_text(encoding="utf-8").casefold()
    assert "ci passes" in text
    assert "separate deployment" in text
    assert "live proof" in text
