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
    assert result["protocol_check_count"] == 700
    assert result["protocol_proven_count"] == 0
    assert result["protocol_green_gate_passed"] is False
    assert result["protocol_registry"]["counts"]["UNKNOWN"] == 700
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


def test_company_department_map_reuses_canonical_evidence_without_inventing_activity():
    evidence = {"states": {
        "market_commerce": {"state": "PROVEN"},
        "pricing_margin": {"state": "PROVEN"},
        "company_registry": {"state": "CONFLICTING"},
        "clothing_supplier": {"state": "UNAVAILABLE"},
        "print_on_demand_supplier": {"state": "PROVEN"},
        "music_catalogue": {"state": "PROVEN"},
        "artist_rights": {"state": "UNKNOWN"},
    }}
    result = company_intelligence_runtime.department_map(
        evidence, protocol_proven_count=28,
    )
    assert result["department_count"] == 8
    assert result["protocol_proven_count"] == 28
    assert result["operational_green"] is False
    assert result["read_only"] is True
    assert result["no_new_agent_or_brain"] is True
    nodes = {node["id"]: node for node in result["departments"]}
    assert set(nodes) == {
        "sales", "deals", "marketing", "customer", "operations",
        "back_office", "intelligence", "knowledge_base",
    }
    assert nodes["sales"]["source_state"] == "SOURCE_PROVEN"
    assert nodes["sales"]["operational_state"] == "UNKNOWN"
    assert nodes["back_office"]["source_state"] == "BLOCKED"
    assert nodes["operations"]["source_state"] == "BLOCKED"
    assert nodes["marketing"]["source_state"] == "UNKNOWN"
    assert nodes["deals"]["source_state"] == "UNKNOWN"
    assert all(node["execution_granted"] is False for node in nodes.values())
    assert all(node["active_agents_claimed"] is False for node in nodes.values())
    assert all(node["revenue_claimed"] is False for node in nodes.values())


def test_company_department_map_fails_closed_when_evidence_missing_or_invalid():
    for source in (None, [], {}, {"states": {"market_commerce": {
        "state": "NOT_AN_EVIDENCE_STATE",
    }}}):
        result = company_intelligence_runtime.department_map(source)
        assert len(result["departments"]) == 8
        assert all(
            node["source_state"] == "UNKNOWN"
            for node in result["departments"]
        )
        assert all(node["operational_state"] == "UNKNOWN"
                   for node in result["departments"])
        assert result["operational_green"] is False


def test_company_map_remains_collapsed_inside_existing_founder_only_page():
    from pathlib import Path
    from mission_control import company_intelligence_views

    html = Path("mission_control/templates/company_intelligence.html").read_text()
    assert '<details class="department-map"' in html
    assert 'runtime.department_map.departments' in html
    assert "Live activity: {{ department.operational_state }}" in html
    assert "No automatic execution" in html
    assert "/company-map" not in html
    assert "founder_only=True" in Path(
        company_intelligence_views.__file__
    ).read_text()
