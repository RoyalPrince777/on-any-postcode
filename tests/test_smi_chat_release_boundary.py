from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_release_boundary_requires_ci_and_device_proof_after_source_build():
    doc = (ROOT / "docs/SMI_CHAT_PRODUCT_COMPLETION.md").read_text()
    assert "source-level passing test" in doc
    assert "live handset proof" in doc
    assert "production-proven" in doc
