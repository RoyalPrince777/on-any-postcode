"""Regression coverage for continuous M Town world position."""
from mission_control import earth_is_our_turf, mtown_world_position


def test_position_starts_on_first_route_segment():
    plan=earth_is_our_turf.route("town-centre","lavender-avenue","car")
    pos=mtown_world_position.start(plan)
    assert pos["current_node"]=="town-centre"
    assert pos["segment"]["from"]=="town-centre"
    assert pos["remaining_m"]==plan["distance_m"]
    assert pos["completed"] is False
    assert pos["exact_geometry_claimed"] is False


def test_position_advances_without_teleporting():
    plan=earth_is_our_turf.route("town-centre","lavender-avenue","car")
    pos=mtown_world_position.start(plan)
    moved=mtown_world_position.advance(pos,plan,distance_m=100)
    assert moved["travelled_m"]==100
    assert 0 < moved["route_progress"] < 1
    assert moved["completed"] is False


def test_position_crosses_segments_and_completes():
    plan=earth_is_our_turf.route("town-centre","lavender-avenue","car")
    pos=mtown_world_position.start(plan)
    moved=mtown_world_position.advance(pos,plan,distance_m=plan["distance_m"]+500)
    assert moved["completed"] is True
    assert moved["current_node"]=="lavender-avenue"
    assert moved["remaining_m"]==0
    assert moved["route_progress"]==1.0


def test_lookahead_nodes_follow_current_route():
    plan=earth_is_our_turf.route("town-centre","phipps-bridge","car")
    pos=mtown_world_position.start(plan)
    nodes=mtown_world_position.lookahead_nodes(pos,plan,distance_m=1200)
    assert nodes[0]=="town-centre"
    assert len(nodes)>=2
    assert all(node in plan["nodes"] for node in nodes)


def test_world_advance_route_updates_character_without_destination_jump():
    state=earth_is_our_turf.new_world()
    state=earth_is_our_turf.action(
        state,command="navigate",target="lavender-avenue",mode="foot",
    )
    planned=earth_is_our_turf.public_state(state)
    assert planned["world_position"]["route_progress"]==0
    state=earth_is_our_turf.action(state,command="advance-route",distance=100)
    moved=earth_is_our_turf.public_state(state)
    assert moved["world_position"]["route_progress"]>0
    assert moved["active_route"] is not None
    assert moved["character"]["movement"]["segment"] is not None
    assert moved["character"]["movement"]["offset"]>0


def test_world_advance_route_finishes_and_preserves_position_receipt():
    state=earth_is_our_turf.new_world()
    state=earth_is_our_turf.action(
        state,command="navigate",target="lavender-avenue",mode="foot",
    )
    total=earth_is_our_turf.public_state(state)["active_route"]["distance_m"]
    state=earth_is_our_turf.action(state,command="advance-route",distance=total+1)
    world=earth_is_our_turf.public_state(state)
    assert world["active_route"] is None
    assert world["world_position"]["completed"] is True
    assert world["player"]["node"]=="lavender-avenue"
    assert world["character"]["movement"]["node"]=="lavender-avenue"
