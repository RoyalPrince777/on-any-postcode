import pytest

from scripts import promote_render_smi_image as promotion


def test_smi_plan_is_exact_existing_service_and_motion_fix_image():
    plan = promotion.plan()
    assert plan["service_id"] == "srv-da6tp615efls73ct81q0"
    assert plan["service_name"] == "oap-smi"
    assert plan["public_url"] == "https://oap-smi.onrender.com"
    assert plan["runtime_target"] == "smi_gateway:app"
    assert plan["image"].endswith(
        "sha256:e23632e68641d7bdf8bc6f1e23596336537aec4cf101a748b229acddd70d8622"
    )
    assert plan["creates_new_service"] is False
    assert plan["replaces_environment"] is False
    assert plan["source_build_required"] is False


def test_smi_dry_run_needs_no_credentials(monkeypatch):
    monkeypatch.delenv("OAP_RENDER_API_KEY", raising=False)
    monkeypatch.delenv("RENDER_API_KEY", raising=False)
    result = promotion.promote()
    assert result["dry_run"] is True
    assert result["applied"] is False


def test_smi_apply_fails_closed_without_api_key(monkeypatch):
    monkeypatch.delenv("OAP_RENDER_API_KEY", raising=False)
    monkeypatch.delenv("RENDER_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="Render API key is not configured"):
        promotion.promote(apply=True)


def test_smi_apply_updates_existing_service_then_deploys(monkeypatch):
    calls = []
    current = {
        "id": promotion.SERVICE_ID,
        "name": promotion.SERVICE_NAME,
        "serviceDetails": {
            "url": promotion.PUBLIC_URL,
            "healthCheckPath": promotion.HEALTH_PATH,
        },
    }

    def fake_request(method, path, payload=None):
        calls.append((method, path, payload))
        if method == "GET":
            return dict(current)
        if method == "PATCH":
            return {**current, "imagePath": promotion.IMAGE}
        if method == "POST":
            return {"id": "dep-smi-proof"}
        raise AssertionError(method)

    monkeypatch.setattr(promotion, "_request", fake_request)
    result = promotion.promote(apply=True)
    assert result["applied"] is True
    assert result["deploy_id"] == "dep-smi-proof"
    assert calls == [
        ("GET", f"/services/{promotion.SERVICE_ID}", None),
        (
            "PATCH",
            f"/services/{promotion.SERVICE_ID}",
            {"image": {"url": promotion.IMAGE}, "autoDeploy": "no"},
        ),
        (
            "POST",
            f"/services/{promotion.SERVICE_ID}/deploys",
            {"imageUrl": promotion.IMAGE},
        ),
    ]
