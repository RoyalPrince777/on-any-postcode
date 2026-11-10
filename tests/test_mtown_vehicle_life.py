"""Regression coverage for M Town Vehicle Life."""
from mission_control import (
    earth_is_our_turf,
    mtown_vehicle_life,
)


def test_vehicle_life_status_contract():
    status=mtown_vehicle_life.status()
    assert status["ownership"] is True
    assert status["enter_exit"] is True
    assert status["route_vehicle_sync"] is True
    assert status["parking"] is True
    assert status["npc_routines"] is True
    assert status["usable_entrances"] is True
    assert status["real_vehicle_claimed"] is False
    assert status["real_person_schedule_claimed"] is False


def test_claim_enter_drive_exit_cycle():
    state=earth_is_our_turf.new_world()
    state=earth_is_our_turf.action(state,command="claim-vehicle",target="vehicle-oap-001")
    state=earth_is_our_turf.action(state,command="enter-vehicle",target="vehicle-oap-001")
    entered=earth_is_our_turf.public_state(state)
    assert entered["vehicle_life"]["inside_vehicle"] is True
    assert entered["vehicle_life"]["active_vehicle_id"]=="vehicle-oap-001"
    assert "vehicle-oap-001" in entered["character"]["owned"]["vehicles"]
    assert entered["character"]["movement"]["mode"]=="car"

    state=earth_is_our_turf.action(
        state,command="navigate",target="western-road",mode="car",
    )
    state=earth_is_our_turf.action(state,command="advance-route",distance=2000)
    driven=earth_is_our_turf.public_state(state)
    vehicle=next(v for v in driven["living_streets"]["vehicles"] if v["id"]=="vehicle-oap-001")
    assert vehicle["node"]=="western-road"

    state=earth_is_our_turf.action(state,command="exit-vehicle")
    exited=earth_is_our_turf.public_state(state)
    assert exited["vehicle_life"]["inside_vehicle"] is False
    assert exited["character"]["movement"]["mode"]=="foot"


def test_enter_vehicle_requires_same_node_and_ownership():
    state=earth_is_our_turf.new_world()
    try:
        earth_is_our_turf.action(state,command="enter-vehicle",target="vehicle-oap-002")
    except ValueError as exc:
        assert str(exc) in {"mtown_vehicle_not_here","mtown_vehicle_not_owned"}
    else:
        raise AssertionError("entering unavailable vehicle must fail")


def test_park_vehicle_requires_local_game_parking():
    state=earth_is_our_turf.new_world()
    state=earth_is_our_turf.action(state,command="claim-vehicle",target="vehicle-oap-001")
    state=earth_is_our_turf.action(state,command="enter-vehicle",target="vehicle-oap-001")
    state=earth_is_our_turf.action(state,command="park-vehicle",target="park-town-01")
    view=earth_is_our_turf.public_state(state)
    vehicle=next(v for v in view["living_streets"]["vehicles"] if v["id"]=="vehicle-oap-001")
    assert vehicle["status"]=="parked"
    assert vehicle["parking_id"]=="park-town-01"
    assert view["vehicle_life"]["inside_vehicle"] is False


def test_npc_routines_are_game_only_and_deterministic():
    state=mtown_vehicle_life.new_state()
    morning=mtown_vehicle_life.npc_positions(state,minute=480)
    repeat=mtown_vehicle_life.npc_positions(state,minute=480)
    assert morning==repeat
    assert all(row["source"]=="game_routine" for row in morning)
    assert all(row["persistent"] is True for row in morning)


def test_use_entrance_records_receipt_without_claiming_real_access():
    state=earth_is_our_turf.new_world()
    state=earth_is_our_turf.action(
        state,command="use-entrance",target="entrance-town-local",
    )
    view=earth_is_our_turf.public_state(state)
    assert view["vehicle_life"]["last_entrance_id"]=="entrance-town-local"
    assert view["vehicle_life"]["truth"]["exact_private_entrance_claimed"] is False
