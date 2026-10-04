"""Regression coverage for EARTH IS OUR TURF Mitcham living-world slice."""
from mission_control import earth_is_our_turf


def test_mitcham_world_action_memory_and_consequence():
    state=earth_is_our_turf.new_world()
    before=earth_is_our_turf.public_state(state)
    assert before["district"]=="Mitcham · CR4"
    assert before["player"]["node"]=="town-centre"
    assert before["player"]["travel_mode"]=="foot"
    changed=earth_is_our_turf.action(state,command="help-local")
    after=earth_is_our_turf.public_state(changed)
    assert after["player"]["influence"]==2
    assert after["player"]["reputation"]==1
    node=next(n for n in after["nodes"] if n["id"]=="town-centre")
    assert node["memory"]==2
    assert node["prosperity"]==52
    assert after["events"][-1]["type"]=="postcode_memory"


def test_mitcham_navigation_separates_car_from_foot_shortcuts():
    foot=earth_is_our_turf.route("town-centre","figges-marsh","foot")
    car=earth_is_our_turf.route("town-centre","figges-marsh","car")
    assert foot["distance_m"] <= car["distance_m"]
    assert foot["mode"]=="foot"
    try:
        earth_is_our_turf.route("town-centre","market-lane","car")
    except ValueError as exc:
        assert str(exc)=="eiot_route_unavailable_for_mode"
    else:
        raise AssertionError("car must not use alley-only destination")


def test_mitcham_planned_route_can_be_travelled_and_remembered():
    state=earth_is_our_turf.new_world()
    state=earth_is_our_turf.action(state,command="navigate",target="pollards-hill",mode="bike")
    planned=earth_is_our_turf.public_state(state)
    assert planned["active_route"]["to"]=="pollards-hill"
    assert planned["active_route"]["mode"]=="bike"
    state=earth_is_our_turf.action(state,command="travel-route")
    after=earth_is_our_turf.public_state(state)
    assert after["player"]["node"]=="pollards-hill"
    assert after["active_route"] is None
    assert after["events"][-1]["type"]=="travel"


def test_mitcham_arena_surface_is_exposed(client):
    response=client.get("/arena/earth-is-our-turf")
    assert response.status_code==200
    html=response.get_data(as_text=True)
    assert "EARTH IS OUR TURF" in html
    assert "Born Local. Built Global." in html
    assert "Mitcham / CR4" in html
    assert "earth_is_our_turf.js" in html
    assert "Mitcham Navigation" in html
    assert "Travel mode" in html
    assert "Foot" in html and "Bike / e-bike" in html and "Car" in html
    assert "No precise tracking" in html


def test_arena_front_door_links_mitcham_world(client):
    html=client.get("/arena").get_data(as_text=True)
    assert 'href="/arena/earth-is-our-turf"' in html
    assert "Enter Mitcham" in html


def test_mitcham_streams_named_neighbourhood_chunks_and_environment():
    state=earth_is_our_turf.new_world()
    view=earth_is_our_turf.public_state(state)
    assert view["active_chunk"]=="central"
    assert "central" in view["loaded_chunks"]
    assert view["environment"]["live_claim"] is False
    assert view["environment"]["source"]=="game_environment_simulation_v1"

    state=earth_is_our_turf.action(state,command="navigate",target="lavender-avenue",mode="foot")
    planned=earth_is_our_turf.public_state(state)
    assert "lavender" in planned["loaded_chunks"]

    state=earth_is_our_turf.action(state,command="travel-route")
    arrived=earth_is_our_turf.public_state(state)
    assert arrived["active_chunk"]=="lavender"
    assert arrived["player"]["node"]=="lavender-avenue"


def test_named_mitcham_anchors_are_in_world_catalogue():
    state=earth_is_our_turf.public_state(earth_is_our_turf.new_world())
    labels={n["label"] for n in state["nodes"]}
    assert {"Lavender Avenue","Lavender Park","Phipps Bridge","Armfield Crescent","Laburnum Road"} <= labels
