from pathlib import Path


TEMPLATE = (
    Path(__file__).resolve().parents[1]
    / "mission_control"
    / "templates"
    / "planetary_domains.html"
)


def test_domain_command_panels_and_relationship_matrix_are_rendered():
    template = TEMPLATE.read_text(encoding="utf-8")
    assert 'class="command-grid"' in template
    assert "selected.command.items()" in template
    assert 'id="relationships-title"' in template
    assert "planetary.cross_domain_relationships" in template


def test_relationship_matrix_preserves_truth_boundary():
    template = TEMPLATE.read_text(encoding="utf-8")
    assert "no causal or live-runtime claim" in template
