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

    assert result["readiness"]["code_present"]["state"] == "PRESENT"
    assert result["readiness"]["ci_verified"]["state"] == "UNKNOWN"
    assert result["readiness"]["production_verified"]["state"] == "UNKNOWN"
    assert "software_green" not in result
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
    def receipt(state):
        return {
            "state": state, "valid": True,
            "source_reference": "oap:test:canonical",
            "observed_at": "2026-11-20T10:00:00+00:00",
        }

    evidence = {"states": {
        "market_commerce": receipt("PROVEN"),
        "pricing_margin": receipt("PROVEN"),
        "company_registry": receipt("CONFLICTING"),
        "clothing_supplier": receipt("UNAVAILABLE"),
        "print_on_demand_supplier": receipt("PROVEN"),
        "music_catalogue": receipt("PROVEN"),
        "artist_rights": receipt("UNKNOWN"),
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
    assert result["priority_department"] == "Operations"
    assert "clothing supplier" in result["priority_next_proof"]
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
        assert result["priority_department"] == "Sales"



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



def test_swot_first_uses_only_normalised_source_evidence():
    ingest = company_intelligence_runtime.company_evidence_ingestion.ingest_snapshot
    observed = "2026-11-20T09:00:00+00:00"
    evidence = ingest([
        {
            "domain": "market_commerce", "state": "PROVEN",
            "source_reference": "oap:test:market",
            "observed_at": observed,
        },
        {
            "domain": "company_registry", "state": "CONFLICTING",
            "source_reference": "oap:test:registry",
            "observed_at": observed,
        },
    ])
    departments = company_intelligence_runtime.department_map(evidence)
    swot = company_intelligence_runtime.swot_first_review(
        evidence, departments, {"receipt_chain_verified": False},
    )
    assert [item["domain"] for item in swot["strengths"]] == ["market_commerce"]
    assert swot["source_proven"] == 1
    assert swot["source_unresolved"] == 6
    assert any(item["domain"] == "company_registry"
               for item in swot["threats"])
    assert any(item["domain"] == "artist_rights"
               and item["state"] == "UNKNOWN"
               for item in swot["weaknesses"])
    assert swot["opportunities"]
    assert all(item["state"] == "PROPOSED"
               for item in swot["opportunities"])
    assert swot["live_operations_verified"] is False
    assert swot["independent_agent_votes_claimed"] is False
    assert swot["execution_granted"] is False
    assert swot["full_green"] is False


def test_swot_first_does_not_promote_invalid_or_missing_receipts():
    invalid = {"states": {
        "market_commerce": {
            "state": "PROVEN", "source_reference": "oap:unsigned",
            "observed_at": "2026-11-20T09:00:00+00:00", "valid": False,
        },
    }}
    result = company_intelligence_runtime.swot_first_review(
        invalid, company_intelligence_runtime.department_map(invalid),
        {"receipt_chain_verified": True},
    )
    assert result["strengths"] == ()
    assert len(result["weaknesses"]) == 7
    assert result["threats"] == ()
    assert result["protocol_receipt_chain_verified"] is True
    assert result["live_operations_verified"] is False
    assert result["full_green"] is False
    assert company_intelligence_runtime.swot_first_review(
        None, None, None,
    )["source_unresolved"] == 7


def test_truth_mode_swot_precedes_company_map_without_fake_green():
    from pathlib import Path

    html = Path("mission_control/templates/company_intelligence.html").read_text()
    assert html.index("Truth Mode:") < html.index('id="swot-first-title"')
    assert html.index('id="swot-first-title"') < html.index(
        'id="company-department-map"'
    )
    assert "runtime.swot_first.strengths" in html
    assert "runtime.swot_first.weaknesses" in html
    assert "runtime.swot_first.opportunities" in html
    assert "runtime.swot_first.threats" in html
    assert "runtime.readiness.code_present.state" in html
    assert "runtime.readiness.ci_verified.state" in html
    assert "runtime.readiness.production_verified.state" in html
    assert 'id="company-readiness-evidence"' in html
    assert "runtime.software_green" not in html
    assert "Software core: {{ '100%'" not in html
    assert "No independent agent votes" in html
    assert "Founder Final required" in html

def test_readiness_requires_a_fresh_durable_worker_heartbeat(monkeypatch):
    monkeypatch.setattr(
        company_intelligence_runtime.organism_runtime,
        "runtime_status",
        lambda: {"schema_ready": True, "worker_fresh": False, "ready": False},
    )
    missing = company_intelligence_runtime.readiness_signals()
    assert missing["worker_connected"]["state"] == "UNKNOWN"
    assert missing["worker_connected"]["evidence_reference"] == ""
    assert missing["guardian_hrm_verified"]["state"] == "UNKNOWN"

    monkeypatch.setattr(
        company_intelligence_runtime.organism_runtime,
        "runtime_status",
        lambda: {"schema_ready": True, "worker_fresh": "true", "ready": True},
    )
    invalid = company_intelligence_runtime.readiness_signals()
    assert invalid["worker_connected"]["state"] == "UNKNOWN"

    monkeypatch.setattr(
        company_intelligence_runtime.organism_runtime,
        "runtime_status",
        lambda: {"schema_ready": True, "worker_fresh": True, "ready": True},
    )
    fresh = company_intelligence_runtime.readiness_signals()
    assert fresh["worker_connected"]["state"] == "PROVEN"
    assert fresh["worker_connected"]["evidence_reference"]
    assert fresh["ci_verified"]["state"] == "UNKNOWN"
    assert fresh["production_verified"]["state"] == "UNKNOWN"


def test_readiness_fails_closed_when_worker_readback_breaks(monkeypatch):
    def unavailable():
        raise RuntimeError("worker store unavailable")

    monkeypatch.setattr(
        company_intelligence_runtime.organism_runtime,
        "runtime_status",
        unavailable,
    )
    result = company_intelligence_runtime.readiness_signals()
    assert result["worker_connected"]["state"] == "UNKNOWN"
    assert result["worker_connected"]["evidence_reference"] == ""
    assert result["guardian_hrm_verified"]["state"] == "UNKNOWN"
