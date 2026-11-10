from mission_control import market_sika_pod_runtime


def test_market_sika_payment_gate_requires_all_governed_controls():
    intent = {
        "payment_id": "pay-1",
        "status": "AUTHORISED",
    }
    ready = market_sika_pod_runtime.payment_market_gate(
        payment_intent=intent,
        customer_authority_verified=True,
        rights_gate_allowed=True,
        execution_gate_authorised=True,
    )
    assert ready["ready"] is True
    assert ready["provider_submission_eligible"] is True
    assert ready["provider_calling"] is False
    assert ready["money_movement"] is False

    blocked = market_sika_pod_runtime.payment_market_gate(
        payment_intent=intent,
        customer_authority_verified=True,
        rights_gate_allowed=False,
        execution_gate_authorised=True,
    )
    assert blocked["ready"] is False
    assert "rights_gate_closed" in blocked["block_reasons"]


def test_pod_market_gate_turns_internal_candidate_into_execution_ready_only_with_all_external_evidence():
    checks = {
        "order_exists": True,
        "order_item_exists": True,
        "fulfilment_intent_exists": True,
        "supplier_binding_exists": True,
        "supplier_ready": True,
        "design_exists": True,
        "design_ready": True,
        "made_to_order": True,
        "supplier_product_ref_present": True,
        "supplier_variant_ref_bounded": True,
        "artwork_reference_present": True,
        "placements_present": True,
        "colors_present": True,
        "sizes_present": True,
        "delivery_destination_present": False,
        "payment_capture_proven": False,
        "provider_connector_authorized": False,
        "provider_credentials_configured": False,
        "human_stop_clear": True,
        "recovery_clear": True,
        "external_submission_allowed": False,
    }
    candidate = {
        "order_id": "order-1",
        "provider_slug": "pod-provider",
        "checks": checks,
    }
    result = market_sika_pod_runtime.pod_market_gate(
        handoff_candidate=candidate,
        delivery_destination_present=True,
        payment_capture_proven=True,
        provider_connector_authorized=True,
        provider_credentials_configured=True,
    )
    assert result["ready"] is True
    assert result["external_submission_allowed"] is True
    assert result["external_submission_performed"] is False
    assert result["block_reasons"] == []


def test_pod_market_gate_fails_closed_on_missing_provider_authority():
    candidate = {
        "checks": {
            "order_exists": True,
            "human_stop_clear": True,
            "recovery_clear": True,
            "external_submission_allowed": False,
        }
    }
    result = market_sika_pod_runtime.pod_market_gate(
        handoff_candidate=candidate,
        delivery_destination_present=True,
        payment_capture_proven=True,
        provider_connector_authorized=False,
        provider_credentials_configured=True,
    )
    assert result["ready"] is False
    assert "provider_connector_authorized" in result["block_reasons"]


def test_payment_submission_receipt_gate_requires_accepted_matching_receipt():
    intent = {"payment_id": "pay-7", "status": "SUBMITTED"}
    evidence = {
        "payment_id": "pay-7",
        "outcome": "ACCEPTED",
        "provider_reference": "provider-pay-7",
    }
    result = market_sika_pod_runtime.payment_submission_receipt_gate(
        payment_intent=intent,
        submission_evidence=evidence,
    )
    assert result["proven"] is True
    assert result["settlement_proven"] is False
    assert result["money_movement_claim_allowed"] is False


def test_supplier_receipt_maps_into_distribution_runtime_states():
    accepted = market_sika_pod_runtime.supplier_receipt_gate({
        "state": "ACCEPTED",
        "provider_reference": "pod-123",
    })
    assert accepted["proven"] is True
    assert market_sika_pod_runtime.distribution_transition_for_supplier_state(
        "ACCEPTED"
    ) == "HANDED_OFF"

    delivered = market_sika_pod_runtime.supplier_receipt_gate({
        "state": "DELIVERED",
        "provider_reference": "pod-123",
    })
    assert delivered["delivery_proven"] is True
    assert market_sika_pod_runtime.distribution_transition_for_supplier_state(
        "DELIVERED"
    ) == "DELIVERED"
    assert market_sika_pod_runtime.distribution_transition_for_supplier_state(
        "FAILED"
    ) == "RECOVERY_REQUIRED"


def test_combined_runtime_status_connects_existing_canonical_systems():
    status = market_sika_pod_runtime.status()
    assert status["oap_market_connected"] is True
    assert status["sika_payment_orchestrator_connected"] is True
    assert status["sika_submission_evidence_connected"] is True
    assert status["pod_supplier_bridge_connected"] is True
    assert status["distribution_runtime_connected"] is True
    assert status["internal_orchestration_ready"] is True
    assert status["external_payment_execution_proven"] is False
    assert status["external_manufacturer_execution_proven"] is False
    assert status["money_movement_proven"] is False


def test_market_projection_exposes_sika_pod_runtime(client, monkeypatch):
    import mission_control.product_core_views as views

    monkeypatch.setattr(
        views.product_core_services,
        "commerce_dashboard",
        lambda identity_id: {
            "organ": "OAP Commerce Core",
            "storefront": None,
            "products": [],
            "orders": [],
        },
    )
    projected = views._market_projection("00000000-0000-0000-0000-000000000001")
    assert projected["organ"] == "OAP Market"
    assert projected["sika_pod_runtime"]["internal_orchestration_ready"] is True
