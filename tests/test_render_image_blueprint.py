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
        "sha256:706fc5700049b0be2a7d7df2e755e5fe160c61c33dbc2d454d772fd6ddd519b6"
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


def test_core_image_release_manifest_matches_live_linkup_runtime():
    import json

    manifest = json.loads(
        (ROOT / "deploy" / "render-core-release.json").read_text()
    )
    assert manifest["release_commit"] == (
        "9bf7aba26beda0ea2f1ea6d192a7585d0b7cd6d8"
    )
    assert manifest["image"]["immutable_ref"] == (
        "ghcr.io/royalprince777/on-any-postcode-runtime@"
        "sha256:706fc5700049b0be2a7d7df2e755e5fe160c61c33dbc2d454d772fd6ddd519b6"
    )
    assert manifest["service"]["render_service_id"] == (
        "srv-d8gfsv0jo6nc73egdlf0"
    )
    assert manifest["service"]["public_url"] == (
        "https://on-any-postcode.onrender.com"
    )


def _smi_block() -> str:
    content = (ROOT / "render.yaml").read_text()
    start = content.index("  - type: web\n    name: oap-smi\n")
    tail = content[start + 1 :]
    next_service = tail.find("\n  - type:")
    return content[start:] if next_service < 0 else content[start : start + 1 + next_service]


def test_smi_render_blueprint_uses_exact_motion_fix_image():
    block = _smi_block()
    assert "runtime: image" in block
    assert (
        "ghcr.io/royalprince777/on-any-postcode-runtime@"
        "sha256:e23632e68641d7bdf8bc6f1e23596336537aec4cf101a748b229acddd70d8622"
    ) in block
    assert 'value: "smi_gateway:app"' in block
    assert "buildCommand:" not in block
    assert "startCommand:" not in block
    assert "repo:" not in block
    assert "branch:" not in block
