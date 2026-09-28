from __future__ import annotations

from scripts import release_preflight


def test_release_preflight_fails_closed_without_render_credential(monkeypatch):
    monkeypatch.delenv("OAP_RENDER_API_KEY", raising=False)
    monkeypatch.delenv("RENDER_API_KEY", raising=False)

    result = release_preflight.status()

    assert result["read_only_preflight"] is True
    assert result["provider_authority_available"] is False
    assert result["image_promotion_ready"] is False
    assert result["recommended_path"] == "hold_no_mutation"
    assert "render_image_update_authority_missing" in result["blockers"]
    assert result["rules"]["no_fake_green"] is True


def test_release_preflight_recognizes_image_promotion_authority(monkeypatch):
    monkeypatch.setenv("OAP_RENDER_API_KEY", "configured-for-test")

    result = release_preflight.status()

    assert result["core_release_contract_valid"] is True
    assert result["smi_release_contract_valid"] is True
    assert result["provider_authority_available"] is True
    assert result["image_promotion_ready"] is True
    assert result["recommended_path"] == "immutable_image_promotion"


def test_release_preflight_accepts_deploy_hook(monkeypatch):
    monkeypatch.delenv("OAP_RENDER_API_KEY", raising=False)
    monkeypatch.delenv("RENDER_API_KEY", raising=False)
    monkeypatch.setenv(
        "RENDER_DEPLOY_HOOK_URL",
        "https://api.render.com/deploy/srv-d8gfsv0jo6nc73egdlf0?key=test",
    )

    result = release_preflight.status()

    assert result["render_api_credential_available"] is False
    assert result["render_deploy_hook_available"] is True
    assert result["provider_authority_available"] is True
    assert result["image_promotion_ready"] is True
