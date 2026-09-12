from pathlib import Path


def test_summary_names_single_surface_and_backend_boundary():
    text = Path("docs/OAP_MAP_INTELLIGENCE_SUMMARY.md").read_text(encoding="utf-8").casefold()
    assert "one canonical surface" in text
    assert "protected backend" in text
    assert "does not deploy production" in text
