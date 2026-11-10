from flask import Flask

from mission_control import company_intelligence_runtime, company_intelligence_views


def test_runtime_projection_reuses_real_music_market_evidence(monkeypatch):
    monkeypatch.setenv("OAP_COMPANY_REGISTRY_EVIDENCE_STATE", "CONFLICTING")
    monkeypatch.setenv("OAP_COMPANY_REGISTRY_EVIDENCE_AT", "2026-10-02T16:00:00+00:00")
    monkeypatch.setenv(
        "OAP_COMPANY_REGISTRY_EVIDENCE_REF",
        "https://find-and-update.company-information.service.gov.uk/company/14753133",
    )
    monkeypatch.setenv("OAP_PRICING_MARGIN_EVIDENCE_REF", "oap:test:margin")
    monkeypatch.setenv("OAP_PRICING_MARGIN_EVIDENCE_AT", "2026-10-02T16:00:00+00:00")

    monkeypatch.setattr(
        company_intelligence_runtime.product_core_services,
        "tune_dashboard",
        lambda identity_id: {
            "releases": [{"release_id": "11111111-1111-1111-1111-111111111111"}]
        },
    )
    monkeypatch.setattr(
        company_intelligence_runtime.product_core_services,
        "commerce_dashboard",
        lambda identity_id: {
            "storefront": {"storefront_id": "s"},
            "products": [{"product_id": "p"}],
            "orders": [],
        },
    )
    monkeypatch.setattr(
        company_intelligence_runtime.market_supplier_network.STORE,
        "owner_bindings",
        lambda seller_identity_id: [
            {"state": "READY", "evidence_reference": "supplier-proof"}
        ],
    )

    class Store:
        def read_receipts(self, **kwargs):
            return [
                {"evidence_kind": kind}
                for kind in (
                    "source_page",
                    "recording_rights",
                    "composition_rights",
                    "asset_provenance",
                    "territory_permission",
                    "attribution",
                    "human_approval",
                    "recovery_readback",
                )
            ]

    monkeypatch.setattr(
        company_intelligence_runtime.music_evidence,
        "MusicEvidenceStore",
        Store,
    )
    monkeypatch.setattr(
        company_intelligence_runtime.music_evidence,
        "private_distribution_gate",
        lambda receipts, recovery_readback_proven=False: {
            "private_handoff_ready": recovery_readback_proven
        },
    )

    result = company_intelligence_runtime.projection(
        "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    )

    assert result["software_green"] is True
    assert result["evidence"]["states"]["company_registry"]["state"] == "CONFLICTING"
    assert result["evidence"]["states"]["artist_rights"]["state"] == "PROVEN"
    assert result["evidence"]["states"]["music_catalogue"]["state"] == "PROVEN"
    assert result["evidence"]["states"]["clothing_supplier"]["state"] == "PROVEN"
    assert result["evidence"]["states"]["print_on_demand_supplier"]["state"] == "PROVEN"
    assert result["evidence"]["states"]["pricing_margin"]["state"] == "PROVEN"
    assert result["evidence"]["states"]["market_commerce"]["state"] == "PROVEN"
    assert result["proven_count"] == 6
    assert result["operational_green"] is False
    assert result["full_green"] is False


def test_runtime_never_invents_margin_or_supplier_green(monkeypatch):
    monkeypatch.delenv("OAP_PRICING_MARGIN_EVIDENCE_REF", raising=False)
    monkeypatch.delenv("OAP_PRICING_MARGIN_EVIDENCE_AT", raising=False)
    monkeypatch.setattr(
        company_intelligence_runtime.product_core_services,
        "tune_dashboard",
        lambda identity_id: {"releases": []},
    )
    monkeypatch.setattr(
        company_intelligence_runtime.product_core_services,
        "commerce_dashboard",
        lambda identity_id: {"storefront": None, "products": [], "orders": []},
    )
    monkeypatch.setattr(
        company_intelligence_runtime.market_supplier_network.STORE,
        "owner_bindings",
        lambda seller_identity_id: [],
    )

    result = company_intelligence_runtime.projection(
        "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    )

    assert result["evidence"]["states"]["pricing_margin"]["state"] == "UNKNOWN"
    assert result["evidence"]["states"]["clothing_supplier"]["state"] == "UNKNOWN"
    assert result["evidence"]["states"]["print_on_demand_supplier"]["state"] == "UNKNOWN"
    assert result["evidence"]["states"]["market_commerce"]["state"] == "UNKNOWN"
    assert result["operational_green"] is False


def test_company_intelligence_routes_exist():
    app = Flask(__name__)
    app.secret_key = "test"
    app.register_blueprint(company_intelligence_views.bp, url_prefix="/mission")
    rules = {rule.rule for rule in app.url_map.iter_rules()}

    assert "/mission/company-intelligence" in rules
    assert "/mission/company-intelligence/status" in rules
