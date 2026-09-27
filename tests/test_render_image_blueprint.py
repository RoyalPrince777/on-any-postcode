from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _core_block() -> str:
    content = (ROOT / "render.yaml").read_text()
    start = content.index("  - type: web\n    name: on-any-postcode\n")
    tail = content[start + 1 :]
    next_service = tail.find("\n  - type:")
    return content[start:] if next_service < 0 else content[start : start + 1 + next_service]


def test_core_render_blueprint_uses_immutable_first_party_runtime_image():
    block = _core_block()
    assert "runtime: image" in block
    assert (
        "ghcr.io/royalprince777/on-any-postcode-runtime@"
        "sha256:fc6cedcabba587a2cff3090f6ff680b223ce09313257a8d1f445f683142d9c7b"
    ) in block
    assert 'value: "app:app"' in block
    assert "buildCommand:" not in block
    assert "startCommand:" not in block
    assert "repo:" not in block
    assert "branch:" not in block


def test_core_image_blueprint_preserves_database_and_health_contract():
    block = _core_block()
    assert "healthCheckPath: /healthz" in block
    assert "key: DATABASE_URL" in block
    assert "name: oap-smi-hrm-fallback" in block
    assert "property: connectionString" in block


def test_image_release_manifest_matches_first_party_music_release():
    import json

    manifest = json.loads(
        (ROOT / "deploy" / "render-image-release.json").read_text()
    )
    assert manifest["release_commit"] == (
        "351ae499187f14c92af750bad2f9a05afa8b4c4a"
    )
    assert manifest["image"]["immutable_ref"] == (
        "ghcr.io/royalprince777/on-any-postcode-runtime@"
        "sha256:fc6cedcabba587a2cff3090f6ff680b223ce09313257a8d1f445f683142d9c7b"
    )
    assert manifest["services"]["core"]["render_service_id"] == (
        "srv-d8gfsv0jo6nc73egdlf0"
    )
    assert manifest["services"]["core"]["public_url"] == (
        "https://on-any-postcode.onrender.com"
    )
