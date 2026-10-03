from mission_control import hormozi_offline_intelligence as offline


NOW = "2026-10-03T06:00:00+00:00"


def _offer():
    return {
        "offer_id": "oap-business-50",
        "customer_outcome": "Launch a clearer digital business offer",
        "price": 50,
        "direct_cost": 5,
        "fulfilment_cost": 5,
        "payment_cost": 1,
        "refund_allowance": 2,
        "delivery_hours": 24,
        "onboarding_steps": 2,
        "deliverables": ("promo graphic", "menu", "service list"),
        "evidence": ("completed-scope", "pricing-record"),
        "evidence_observed_at": "2026-10-02T12:00:00+00:00",
        "requires_live_external_data": False,
    }


def test_offline_offer_evaluation_requires_no_network():
    result = offline.evaluate_offer(_offer(), now=NOW)

    assert result["offline_capable"] is True
    assert result["network_required_for_analysis"] is False
    assert result["unit_economics"]["contribution_margin"] == 37.0
    assert result["freshness"] == "FRESH"
    assert result["automatic_publish_allowed"] is False
    assert result["payment_capture_allowed"] is False


def test_stale_external_dependency_blocks_commercial_change():
    offer = _offer()
    offer["requires_live_external_data"] = True
    offer["evidence_observed_at"] = "2026-08-01T00:00:00+00:00"

    result = offline.evaluate_offer(offer, now=NOW)

    assert result["freshness"] == "EXPIRED"
    assert "evidence_freshness" in result["blockers"]
    assert "live_external_verification_required" in result["blockers"]
    assert result["commercial_change_ready"] is False


def test_negative_unit_economics_fail_closed():
    offer = _offer()
    offer["direct_cost"] = 60

    result = offline.evaluate_offer(offer, now=NOW)

    assert result["unit_economics"]["positive_contribution"] is False
    assert "non_positive_contribution_margin" in result["blockers"]
    assert "repair_unit_economics_before_publishing" in result["recommendations"]


def test_scenarios_do_not_mutate_source_offer():
    offer = _offer()
    original_price = offer["price"]

    result = offline.scenario_compare(
        offer,
        (
            {"price": 60},
            {"delivery_hours": 48},
        ),
        now=NOW,
    )

    assert offer["price"] == original_price
    assert len(result["scenarios"]) == 2
    assert result["source_offer_mutated"] is False
    assert result["simulation_is_not_runtime_proof"] is True


def test_local_receipt_is_hash_identified_and_sync_pending():
    evaluation = offline.evaluate_offer(_offer(), now=NOW)
    receipt = offline.local_receipt(evaluation, created_at=NOW)

    assert len(receipt["receipt_sha256"]) == 64
    assert receipt["sync_state"] == "LOCAL_PENDING"
    assert receipt["authorises_external_action"] is False


def test_reconcile_never_silently_overwrites_stale_local_state():
    evaluation = offline.evaluate_offer(_offer(), now=NOW)
    receipt = offline.local_receipt(evaluation, created_at=NOW)
    receipt["freshness"] = "STALE"

    result = offline.reconcile(
        receipt,
        {"offer_id": "oap-business-50", "freshness": "FRESH"},
    )

    assert result["coherent"] is False
    assert "newer_remote_evidence" in result["conflicts"]
    assert result["silent_overwrite_allowed"] is False
    assert result["resolution"] == "human_review_required"


def test_status_preserves_human_authority_boundary():
    result = offline.status()

    assert result["offline_first"] is True
    assert result["scenario_analysis"] is True
    assert result["automatic_publish_allowed"] is False
    assert result["automatic_price_change_allowed"] is False
    assert result["payment_capture_allowed"] is False
    assert result["human_authority_final"] is True
