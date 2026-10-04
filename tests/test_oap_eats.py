from mission_control import oap_eats


def test_eats_truth_status_reuses_shared_oap_systems():
    state = oap_eats.status()
    assert state["product"] == "OAP Eats"
    assert state["front_door"] == "/eats"
    assert state["courier_engine"] == "oap_rides_movement"
    assert state["duplicate_map_stack"] is False
    assert state["duplicate_payment_stack"] is False
    assert state["software_contract_ready"] is True
    assert state["live_food_operations_authorised"] is False
    assert state["live_payment_execution_authorised"] is False
    assert state["live_courier_execution_authorised"] is False
    assert state["human_authority_final"] is True


def test_eats_order_state_machine_blocks_skips_and_allows_real_flow():
    assert oap_eats.can_transition("created", "authorised")
    assert oap_eats.can_transition("authorised", "confirmed")
    assert oap_eats.can_transition("confirmed", "preparing")
    assert oap_eats.can_transition("preparing", "ready")
    assert oap_eats.can_transition("ready", "courier_assigned")
    assert oap_eats.can_transition("courier_assigned", "collected")
    assert oap_eats.can_transition("collected", "delivered")
    assert oap_eats.can_transition("delivered", "settlement_pending")
    assert oap_eats.can_transition("settlement_pending", "settled")
    assert not oap_eats.can_transition("created", "settled")
    assert not oap_eats.can_transition("ready", "settled")
