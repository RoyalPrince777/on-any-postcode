from mission_control import (
    atlas_live_sources,
    coherent_automation,
    distribution_intelligence,
    live_signals,
    movement_proof,
    telemetry,
    travel_supply_core,
)


def test_coherent_automation_uses_exact_21_live_signals(monkeypatch):
    monkeypatch.setattr(travel_supply_core, "status", dict)
    status = coherent_automation.status()
    assert status["ready"] is True
    assert status["signal_count"] == 21
    assert status["signals_valid"] is True
    assert len(status["signals"]) == 21
    assert status["external_execution_enabled"] is False
    assert status["human_authority_final"] is True


def test_signal_intelligence_monitor_uses_source_timestamped_runtime_evidence(monkeypatch):
    monkeypatch.setattr(
        telemetry,
        "status",
        lambda: {
            "observability_ready": True,
            "local_request_count": 12,
            "local_health_success_count": 4,
            "local_error_count": 1,
            "local_last_request_epoch": 1789616000,
            "local_last_health_success_epoch": 1789615990,
            "last_success_epoch": None,
            "local_fresh_seconds": 300,
            "delivery_verified": False,
        },
    )
    monkeypatch.setattr(travel_supply_core, "status", dict)

    monitor = coherent_automation.operational_monitor()
    observation = monitor["observations"][0]

    assert monitor["name"] == "Signal Intelligence Monitor"
    assert monitor["source_backed"] is True
    assert monitor["registry_is_not_live_evidence"] is True
    assert observation["source"] == "mission_control.telemetry.status"
    assert observation["source_timestamp"].endswith("Z")
    assert observation["freshness"] == "fresh"
    assert observation["signal"]["id"] == "connected"
    assert observation["proof_state"] == "proven"
    assert monitor["execution_allowed"] is False
    assert monitor["human_authority_final"] is True


def test_signal_intelligence_monitor_fails_closed_without_runtime_evidence(monkeypatch):
    monkeypatch.setattr(telemetry, "status", dict)
    monkeypatch.setattr(atlas_live_sources, "last_fetch_status", dict)
    monkeypatch.setattr(movement_proof, "last_route_status", dict)
    monkeypatch.setattr(travel_supply_core, "status", dict)

    monitor = coherent_automation.operational_monitor()
    observation = monitor["observations"][0]

    assert monitor["source_backed"] is False
    assert observation["source_timestamp"] is None
    assert observation["freshness"] == "unseen"
    assert observation["signal"]["id"] == "offline"
    assert observation["proof_state"] == "proof_required"


def test_signal_intelligence_monitor_reads_passive_map_source_evidence(monkeypatch):
    monkeypatch.setattr(telemetry, "status", dict)
    monkeypatch.setattr(movement_proof, "last_route_status", dict)
    monkeypatch.setattr(travel_supply_core, "status", dict)
    monkeypatch.setattr(
        atlas_live_sources,
        "last_fetch_status",
        lambda: {
            "source": "OpenStreetMap / Nominatim",
            "fetched_at": "2026-09-17T03:55:00Z",
            "fetch_status": "success",
            "result_count": 6,
            "source_backed": True,
            "freshness": "fresh",
            "freshness_window_seconds": 300,
            "passive_only": True,
            "hidden_tracking": False,
            "stores_user_location": False,
        },
    )

    monitor = coherent_automation.operational_monitor()
    observation = monitor["observations"][1]

    assert monitor["observation_count"] == 5
    assert monitor["source_backed"] is True
    assert observation["id"] == "map_intelligence_source"
    assert observation["source"] == "OpenStreetMap / Nominatim"
    assert observation["source_timestamp"] == "2026-09-17T03:55:00Z"
    assert observation["freshness"] == "fresh"
    assert observation["signal"]["id"] == "connected"
    assert observation["proof_state"] == "proven"
    assert observation["evidence"]["result_count"] == 6
    assert observation["evidence"]["hidden_tracking"] is False
    assert observation["evidence"]["stores_user_location"] is False


def test_signal_intelligence_monitor_reads_passive_movement_evidence(monkeypatch):
    monkeypatch.setattr(telemetry, "status", dict)
    monkeypatch.setattr(atlas_live_sources, "last_fetch_status", dict)
    monkeypatch.setattr(travel_supply_core, "status", dict)
    monkeypatch.setattr(
        movement_proof,
        "last_route_status",
        lambda: {
            "source": "OAP first-party seed coordinate estimate",
            "source_timestamp": "2026-09-17T05:50:00Z",
            "proof_status": "seed_route_proof",
            "source_backed": True,
            "verified_area_pair": True,
            "distance_estimate_present": True,
            "eta_estimate_present": True,
            "freshness": "fresh",
            "freshness_window_seconds": 300,
            "route_geometry_proven": False,
            "live_traffic_proven": False,
            "dispatch_enabled": False,
            "hidden_tracking": False,
            "stores_origin_destination": False,
            "stores_coordinates": False,
            "passive_only": True,
        },
    )

    monitor = coherent_automation.operational_monitor()
    observation = monitor["observations"][2]

    assert monitor["observation_count"] == 5
    assert observation["id"] == "movement_intelligence_route"
    assert observation["signal"]["id"] == "connected"
    assert observation["proof_state"] == "bounded_proof"
    assert observation["evidence"]["distance_estimate_present"] is True
    assert observation["evidence"]["eta_estimate_present"] is True
    assert observation["evidence"]["route_geometry_proven"] is False
    assert observation["evidence"]["live_traffic_proven"] is False
    assert observation["evidence"]["dispatch_enabled"] is False
    assert observation["evidence"]["stores_origin_destination"] is False
    assert observation["evidence"]["stores_coordinates"] is False


def test_signal_intelligence_monitor_reads_bounded_direct_supply_evidence(monkeypatch):
    monkeypatch.setattr(telemetry, "status", dict)
    monkeypatch.setattr(atlas_live_sources, "last_fetch_status", dict)
    monkeypatch.setattr(movement_proof, "last_route_status", dict)
    monkeypatch.setattr(
        travel_supply_core,
        "status",
        lambda: {
            "schema_ready": True,
            "certified_supplier_count": 2,
            "active_listing_count": 5,
            "live_inventory_slot_count": 8,
            "live_direct_supply": True,
            "direct_booking_runtime_ready": True,
            "payment_capture_live": False,
            "external_provider_authority": False,
        },
    )

    monitor = coherent_automation.operational_monitor()
    observation = monitor["observations"][3]

    assert monitor["observation_count"] == 5
    assert observation["id"] == "oap_direct_supply"
    assert observation["signal"]["id"] == "warning"
    assert observation["proof_state"] == "partial_proof"
    assert observation["source_timestamp"].endswith("Z")
    assert observation["evidence"]["certified_supplier_count"] == 2
    assert observation["evidence"]["active_listing_count"] == 5
    assert observation["evidence"]["live_inventory_slot_count"] == 8
    assert observation["evidence"]["certified_terms_proven"] is False
    assert observation["evidence"]["inventory_observation_timestamp_proven"] is False
    assert observation["evidence"]["payment_capture_live"] is False
    assert observation["external_authority"] is False


def test_movement_status_sample_does_not_create_live_monitor_evidence():
    movement_proof._LAST_ROUTE_PROOF.update(
        generated_at=None,
        proof_status="unseen",
        source="OAP Movement",
        source_backed=False,
        verified_area_pair=False,
        distance_estimate_present=False,
        eta_estimate_present=False,
    )

    movement_proof.status()
    evidence = movement_proof.last_route_status()

    assert evidence["source_timestamp"] is None
    assert evidence["freshness"] == "unseen"
    assert evidence["source_backed"] is False


def test_coherent_automation_plan_never_self_executes():
    empty = coherent_automation.plan("")
    assert empty["accepted"] is False
    assert empty["execution_allowed"] is False

    plan = coherent_automation.plan("prepare OAP distribution release", target="OAP Distribution")
    assert plan["accepted"] is True
    assert plan["execution_allowed"] is False
    assert plan["human_authority_final"] is True


def test_distribution_requires_proof_before_external_ready():
    status = distribution_intelligence.status()
    assert status["ready"] is True
    assert status["core_signal_count"] == 21
    assert status["external_execution_enabled"] is False

    blocked = distribution_intelligence.review_release({"title": "Release One"})
    assert blocked["owned_oap_distribution_ready"] is False
    assert blocked["external_distribution_ready"] is False
    assert blocked["execution_performed"] is False

    owned = distribution_intelligence.review_release(
        {
            "title": "Release One",
            "rights_proof": True,
            "campaign_ready": True,
            "human_approval": True,
            "receipt_destination": True,
        }
    )
    assert owned["owned_oap_distribution_ready"] is True
    assert owned["external_distribution_ready"] is False

    external = distribution_intelligence.review_release(
        {
            "title": "Release One",
            "rights_proof": True,
            "campaign_ready": True,
            "human_approval": True,
            "receipt_destination": True,
            "external_adapter_proven": True,
        }
    )
    assert external["external_distribution_ready"] is True
    assert external["execution_performed"] is False


def test_live_signal_contract_still_validates():
    validation = live_signals.validate_signal_language()
    assert validation["passed"] is True
    assert validation["signal_count"] == 21
