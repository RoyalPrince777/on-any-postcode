import json

import pytest

from scripts import promote_render_core_image as promotion


def test_plan_is_exact_existing_service_and_immutable_image():
    plan = promotion.plan()
    assert plan["service_id"] == "srv-d8gfsv0jo6nc73egdlf0"
    assert plan["service_name"] == "on-any-postcode"
    assert plan["public_url"] == "https://on-any-postcode.onrender.com"
    assert "@sha256:" in plan["image"]
    assert plan["creates_new_service"] is False
    assert plan["replaces_environment"] is False
    assert plan["source_build_required"] is False
    assert plan["update_payload"] == {
        "image": {"name": promotion.IMAGE},
        "autoDeploy": "no",
    }
    assert plan["deploy_payload"] == {"imageUrl": promotion.IMAGE}


def test_dry_run_requires_no_credentials(monkeypatch):
    monkeypatch.delenv("OAP_RENDER_API_KEY", raising=False)
    monkeypatch.delenv("RENDER_API_KEY", raising=False)
    result = promotion.promote()
    assert result["dry_run"] is True
    assert result["applied"] is False


def test_apply_fails_closed_without_render_api_key(monkeypatch):
    monkeypatch.delenv("OAP_RENDER_API_KEY", raising=False)
    monkeypatch.delenv("RENDER_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="Render API key is not configured"):
        promotion.promote(apply=True)


def test_apply_updates_existing_service_then_deploys_exact_image(monkeypatch):
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
            return {"id": "dep-testreceipt"}
        raise AssertionError(method)

    monkeypatch.setattr(promotion, "_request", fake_request)
    result = promotion.promote(apply=True)

    assert result["applied"] is True
    assert result["deploy_id"] == "dep-testreceipt"
    assert calls == [
        ("GET", f"/services/{promotion.SERVICE_ID}", None),
        (
            "PATCH",
            f"/services/{promotion.SERVICE_ID}",
            {"image": {"name": promotion.IMAGE}, "autoDeploy": "no"},
        ),
        (
            "POST",
            f"/services/{promotion.SERVICE_ID}/deploys",
            {"imageUrl": promotion.IMAGE},
        ),
    ]


def test_apply_refuses_wrong_service_identity(monkeypatch):
    def fake_request(method, path, payload=None):
        return {
            "id": promotion.SERVICE_ID,
            "name": "wrong-service",
            "serviceDetails": {
                "url": promotion.PUBLIC_URL,
                "healthCheckPath": promotion.HEALTH_PATH,
            },
        }

    monkeypatch.setattr(promotion, "_request", fake_request)
    with pytest.raises(RuntimeError, match="Unexpected Render service name"):
        promotion.promote(apply=True)
