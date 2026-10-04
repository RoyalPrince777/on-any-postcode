"""Regression coverage for M Town Living Streets."""
from mission_control import earth_is_our_turf, mtown_living_streets


def test_living_streets_status_truth_boundaries():
    status=mtown_living_streets.status()
    assert status["traffic_simulation"] is True
    assert status["pedestrian_simulation"] is True
    assert status["live_traffic_claimed"] is False
    assert status["precise_private_access_claimed"] is False


def test_living_snapshot_contains_game_traffic_people_parking_and_entrances():
    world=earth_is_our_turf.public_state(earth_is_our_turf.new_world())
    living=world["living"]
    assert living["source"]=="game_living_streets_simulation_v1"
    assert living["live_claim"] is False
    assert living["counts"]["moving_traffic"] >= 0
    assert living["counts"]["pedestrians"] >= 0
    assert isinstance(living["parking"],list)
    assert isinstance(living["entrances"],list)
    assert all(actor["game_actor"] is True for actor in living["traffic"])
    assert all(actor["game_actor"] is True for actor in living["pedestrians"])


def test_living_snapshot_is_bounded_to_streamed_chunks():
    world=earth_is_our_turf.public_state(earth_is_our_turf.new_world())
    loaded=set(world["loaded_chunks"])
    node_chunks={row["id"]:row["chunk"] for row in earth_is_our_turf.NODES}
    assert all(node_chunks[row["node"]] in loaded for row in world["living"]["traffic"])
    assert all(node_chunks[row["node"]] in loaded for row in world["living"]["pedestrians"])
    assert all(node_chunks[row["node"]] in loaded for row in world["living"]["persistent_vehicles"])


def test_persistent_vehicle_can_move_between_game_parking_locations():
    state=mtown_living_streets.new_state()
    moved=mtown_living_streets.park_vehicle(
        state,vehicle_id="vehicle-oap-001",parking_id="park-lower-01",
    )
    vehicle=next(row for row in moved["vehicles"] if row["id"]=="vehicle-oap-001")
    assert vehicle["node"]=="lower-mitcham"
    assert vehicle["parking_id"]=="park-lower-01"
    assert vehicle["status"]=="parked"


def test_entrance_intelligence_respects_travel_mode():
    foot=mtown_living_streets.entrance_for(node_id="figges-marsh",mode="foot")
    car=mtown_living_streets.entrance_for(node_id="figges-marsh",mode="car")
    assert foot
    assert car==[]
    assert foot[0]["fictional_detail"] is True


def test_continuous_route_keeps_living_streets_available():
    state=earth_is_our_turf.new_world()
    state=earth_is_our_turf.action(
        state,command="navigate",target="lavender-avenue",mode="car",
    )
    state=earth_is_our_turf.action(state,command="advance-route",distance=100)
    world=earth_is_our_turf.public_state(state)
    assert world["active_route"] is not None
    assert world["living_status"]["name"]=="M Town Living Streets"
    assert world["living"]["counts"]["persistent_vehicles"] >= 1
