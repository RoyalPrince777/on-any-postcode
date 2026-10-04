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



def test_eats_home_is_app_first_and_routes_to_shared_oap_surfaces(client):
    response = client.get("/eats")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    for marker in (
        'aria-label="OAP Eats navigation"',
        'id="track-form"',
        'href="/market"',
        'href="/oap-map"',
        'href="/transport"',
        'href="/pay/bank"',
        "Find it. Order it. Bring it.",
        "Physical operations are outside this software build.",
    ):
        assert marker in body


def test_eats_app_config_exposes_real_navigation_without_duplicate_stacks(client):
    response = client.get("/eats/app-config")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["navigation"] == {
        "eats": "/eats",
        "explore": "/market",
        "world": "/oap-map",
        "rides": "/transport",
        "sika": "/pay/bank",
    }
    assert payload["physical_operations_in_scope"] is False
    assert payload["human_authority_final"] is True


def test_eats_order_readback_and_write_guards_are_wired():
    from pathlib import Path

    source = Path("mission_control/oap_eats_routes.py").read_text(encoding="utf-8")
    assert '@bp.get("/eats/orders/<order_id>")' in source
    assert "STORE.read_order(" in source
    payment = source.split('def bind_order_payment(order_id: str):', 1)[1].split(
        '@bp.post("/eats/orders/<order_id>/delivery")', 1
    )[0]
    delivery = source.split('def create_order_delivery(order_id: str):', 1)[1].split(
        '@bp.get("/eats/fulfilment-status")', 1
    )[0]
    assert "PUBLIC_WRITE_LIMITER.allow(identity)" in payment
    assert "PUBLIC_WRITE_LIMITER.allow(identity)" in delivery
