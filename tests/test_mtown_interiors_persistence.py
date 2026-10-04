"""Regression coverage for M Town interiors and vehicle persistence."""
from mission_control import earth_is_our_turf, mtown_interiors_persistence


def test_interiors_status_truth_boundaries():
    status=mtown_interiors_persistence.status()
    assert status["usable_interiors"] is True
    assert status["door_states"] is True
    assert status["vehicle_condition"] is True
    assert status["fuel_charge_state"] is True
    assert status["real_building_interior_claimed"] is False
    assert status["real_vehicle_telemetry_claimed"] is False


def test_shop_entrance_enters_and_exits_game_interior():
    state=earth_is_our_turf.new_world()
    state=earth_is_our_turf.action(
        state,command="use-entrance",target="entrance-town-local",
    )
    view=earth_is_our_turf.public_state(state)
    assert view["interiors"]["current_interior_id"]=="interior-oap-local"
    state=earth_is_our_turf.action(state,command="exit-interior")
    view=earth_is_our_turf.public_state(state)
    assert view["interiors"]["current_interior_id"] is None


def test_closed_door_blocks_entry():
    state=mtown_interiors_persistence.new_state()
    state=mtown_interiors_persistence.set_door(
        state,interior_id="interior-oap-local",door="closed",
    )
    try:
        mtown_interiors_persistence.enter(
            state,entrance_id="entrance-town-local",node_id="town-centre",
        )
    except ValueError as exc:
        assert str(exc)=="mtown_interior_door_closed"
    else:
        raise AssertionError("closed door must block entry")


def test_driving_consumes_game_energy_and_condition():
    state=earth_is_our_turf.new_world()
    state=earth_is_our_turf.action(state,command="claim-vehicle",target="vehicle-oap-001")
    state=earth_is_our_turf.action(state,command="enter-vehicle",target="vehicle-oap-001")
    state=earth_is_our_turf.action(
        state,command="navigate",target="western-road",mode="car",
    )
    state=earth_is_our_turf.action(state,command="advance-route",distance=500)
    view=earth_is_our_turf.public_state(state)
    vehicle=view["interiors"]["vehicle_state"]["vehicle-oap-001"]
    assert vehicle["odometer_m"]==500
    assert vehicle["energy"] < 100
    assert vehicle["condition"] < 100


def test_service_and_energy_restore_persist_in_state():
    state=earth_is_our_turf.new_world()
    state=earth_is_our_turf.action(state,command="claim-vehicle",target="vehicle-oap-001")
    state=earth_is_our_turf.action(state,command="enter-vehicle",target="vehicle-oap-001")
    state=earth_is_our_turf.action(
        state,command="navigate",target="western-road",mode="car",
    )
    state=earth_is_our_turf.action(state,command="advance-route",distance=500)
    state=earth_is_our_turf.action(
        state,command="service-vehicle",target="vehicle-oap-001",
    )
    state=earth_is_our_turf.action(
        state,command="restore-vehicle-energy",target="vehicle-oap-001",
    )
    view=earth_is_our_turf.public_state(state)
    vehicle=view["interiors"]["vehicle_state"]["vehicle-oap-001"]
    assert vehicle["condition"]==100
    assert vehicle["energy"]==100
    kinds=[row["type"] for row in view["interiors"]["receipts"]]
    assert "vehicle_serviced" in kinds
    assert "vehicle_energy_restored" in kinds
