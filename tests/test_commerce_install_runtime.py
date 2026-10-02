import json
from pathlib import Path

from mission_control import commerce_install, product_core_views


def test_commerce_installer_covers_required_first_party_schemas(monkeypatch):
    calls = []

    def fake(name):
        def init(*, assume_yes=False, dry_run=False):
            calls.append((name, assume_yes, dry_run))
            return {"schema_ready": not dry_run, "dry_run": dry_run}
        return init

    monkeypatch.setattr(
        commerce_install,
        "COMPONENTS",
        tuple((name, fake(name)) for name, _ in commerce_install.COMPONENTS),
    )
    monkeypatch.setattr(
        commerce_install.sika_secure_provider_runtime,
        "configuration_status",
        lambda kind: {"configuration_complete": kind == "payment"},
    )
    result = commerce_install.install(assume_yes=True, dry_run=False)
    assert result["schema_ready"] is True
    assert {name for name, _, _ in calls} == {
        "supplier_network",
        "payment_orchestrator",
        "payment_submission_evidence",
        "distribution_runtime",
        "provider_receipts",
    }
    assert all(assume_yes and not dry_run for _, assume_yes, dry_run in calls)
    assert result["secret_values_exposed"] is False


def test_commerce_installer_requires_explicit_human_authority():
    try:
        commerce_install.install()
    except RuntimeError as exc:
        assert "Explicit human approval" in str(exc)
    else:
        raise AssertionError("installer must fail closed")


def test_provider_execution_routes_are_registered(client):
    rules = {rule.rule: set(rule.methods) for rule in client.application.url_map.iter_rules()}
    assert rules["/mission/organs/market/install-status"] >= {"GET"}
    assert rules["/mission/organs/market/install"] >= {"POST"}
    assert rules["/mission/organs/market/payments/<payment_id>/execute"] >= {"POST"}
    assert rules["/mission/organs/market/payments/provider/webhook"] >= {"POST"}
    assert rules["/mission/organs/market/pod/<subject_id>/execute"] >= {"POST"}
    assert rules["/mission/organs/market/pod/provider/webhook"] >= {"POST"}


def test_provider_routes_never_embed_secret_values():
    source = Path("mission_control/product_core_views.py").read_text(encoding="utf-8")
    assert "OAP_PAYMENT_PROVIDER_TOKEN" not in source
    assert "OAP_POD_PROVIDER_TOKEN" not in source
    assert "super-secret-token" not in source


def test_market_projection_still_exposes_secret_free_runtime(monkeypatch):
    monkeypatch.setattr(
        product_core_views.product_core_services,
        "commerce_dashboard",
        lambda identity_id: {
            "organ": "OAP Commerce Core",
            "storefront": None,
            "products": [],
            "orders": [],
        },
    )
    monkeypatch.setattr(
        product_core_views.market_sika_pod_runtime,
        "status",
        lambda: {"internal_orchestration_ready": True, "secret_values_exposed": False},
    )
    projected = product_core_views._market_projection(
        "00000000-0000-0000-0000-000000000001"
    )
    assert projected["sika_pod_runtime"]["secret_values_exposed"] is False
    assert "token" not in json.dumps(projected).lower()
