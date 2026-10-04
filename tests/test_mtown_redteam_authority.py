"""Red Team regression coverage for M Town authority boundaries."""
import pytest

from mission_control import earth_is_our_turf


def test_redteam_car_travel_requires_entered_vehicle():
    state=earth_is_our_turf.new_world()
    with pytest.raises(ValueError,match="mtown_vehicle_required_for_car_travel"):
        earth_is_our_turf.action(
            state,command="navigate",target="western-road",mode="car",
        )


def test_redteam_claim_rejects_unknown_vehicle():
    state=earth_is_our_turf.new_world()
    with pytest.raises(ValueError,match="mtown_vehicle_invalid"):
        earth_is_our_turf.action(
            state,command="claim-vehicle",target="vehicle-does-not-exist",
        )


def test_redteam_claim_rejects_remote_vehicle():
    state=earth_is_our_turf.new_world()
    with pytest.raises(ValueError,match="mtown_vehicle_not_here"):
        earth_is_our_turf.action(
            state,command="claim-vehicle",target="vehicle-oap-002",
        )


def test_redteam_claim_rejects_nonworld_owned_vehicle():
    state=earth_is_our_turf.new_world()
    with pytest.raises(ValueError,match="mtown_vehicle_claim_forbidden"):
        earth_is_our_turf.action(
            state,command="claim-vehicle",target="vehicle-oap-003",
        )


def test_redteam_owned_local_vehicle_can_enter_and_drive():
    state=earth_is_our_turf.new_world()
    state=earth_is_our_turf.action(
        state,command="claim-vehicle",target="vehicle-oap-001",
    )
    state=earth_is_our_turf.action(
        state,command="enter-vehicle",target="vehicle-oap-001",
    )
    state=earth_is_our_turf.action(
        state,command="navigate",target="western-road",mode="car",
    )
    state=earth_is_our_turf.action(state,command="advance-route",distance=100)
    view=earth_is_our_turf.public_state(state)
    assert view["world_position"]["travelled_m"]==100
    assert view["interiors"]["vehicle_state"]["vehicle-oap-001"]["energy"]<100


def test_redteam_drive_rejects_distance_beyond_energy_capacity():
    state=earth_is_our_turf.new_world()
    state=earth_is_our_turf.action(
        state,command="claim-vehicle",target="vehicle-oap-001",
    )
    state=earth_is_our_turf.action(
        state,command="enter-vehicle",target="vehicle-oap-001",
    )
    state=earth_is_our_turf.action(
        state,command="navigate",target="western-road",mode="car",
    )
    with pytest.raises(ValueError,match="mtown_vehicle_energy_insufficient"):
        earth_is_our_turf.action(state,command="advance-route",distance=120001)


def test_redteam_service_requires_correct_location():
    state=earth_is_our_turf.new_world()
    state=earth_is_our_turf.action(
        state,command="claim-vehicle",target="vehicle-oap-001",
    )
    state=earth_is_our_turf.action(
        state,command="enter-vehicle",target="vehicle-oap-001",
    )
    state=earth_is_our_turf.action(
        state,command="navigate",target="western-road",mode="car",
    )
    state=earth_is_our_turf.action(state,command="advance-route",distance=100)
    with pytest.raises(ValueError,match="mtown_vehicle_service_location_required"):
        earth_is_our_turf.action(
            state,command="service-vehicle",target="vehicle-oap-001",
        )


def test_redteam_exit_vehicle_before_foot_route():
    state=earth_is_our_turf.new_world()
    state=earth_is_our_turf.action(
        state,command="claim-vehicle",target="vehicle-oap-001",
    )
    state=earth_is_our_turf.action(
        state,command="enter-vehicle",target="vehicle-oap-001",
    )
    with pytest.raises(ValueError,match="mtown_exit_vehicle_before_noncar_travel"):
        earth_is_our_turf.action(
            state,command="navigate",target="figges-marsh",mode="foot",
        )
