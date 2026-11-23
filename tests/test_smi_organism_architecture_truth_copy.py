"""Prevent anatomy registry validation being presented as live organism proof."""
from pathlib import Path


def test_organism_architecture_status_does_not_claim_runtime_green():
    template = (Path(__file__).resolve().parents[1] / "mission_control" / "templates" / "organism.html").read_text(encoding="utf-8")
    assert "Architecture boundaries consistent" in template
    assert "Registry consistency only." in template
    assert "worker heartbeat and device operation require separate runtime evidence" in template
    assert "Canonical boundaries verified" not in template
