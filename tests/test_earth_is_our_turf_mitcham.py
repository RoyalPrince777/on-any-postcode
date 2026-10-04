"""Regression coverage for EARTH IS OUR TURF Mitcham living-world slice."""
from mission_control import earth_is_our_turf


def test_mitcham_world_action_memory_and_consequence():
    state=earth_is_our_turf.new_world()
    before=earth_is_our_turf.public_state(state)
    assert before["district"]=="Mitcham · CR4"
    assert before["player"]["node"]=="town-centre"
    changed=earth_is_our_turf.action(state,command="help-local")
    after=earth_is_our_turf.public_state(changed)
    assert after["player"]["influence"]==2
    assert after["player"]["reputation"]==1
    node=next(n for n in after["nodes"] if n["id"]=="town-centre")
    assert node["memory"]==2
    assert node["prosperity"]==52
    assert after["events"][-1]["type"]=="postcode_memory"


def test_mitcham_world_only_allows_connected_routes():
    state=earth_is_our_turf.new_world()
    moved=earth_is_our_turf.action(state,command="move",target="eastfields")
    assert earth_is_our_turf.public_state(moved)["player"]["node"]=="eastfields"
    try:
        earth_is_our_turf.action(moved,command="move",target="ravensbury")
    except ValueError as exc:
        assert str(exc)=="eiot_route_not_adjacent"
    else:
        raise AssertionError("non-adjacent route should fail")


def test_mitcham_arena_surface_is_exposed(client):
    response=client.get("/arena/earth-is-our-turf")
    assert response.status_code==200
    html=response.get_data(as_text=True)
    assert "EARTH IS OUR TURF" in html
    assert "Born Local. Built Global." in html
    assert "Mitcham / CR4" in html
    assert "earth_is_our_turf.js" in html
    assert "No precise tracking" in html


def test_arena_front_door_links_mitcham_world(client):
    html=client.get("/arena").get_data(as_text=True)
    assert 'href="/arena/earth-is-our-turf"' in html
    assert "Enter Mitcham" in html
