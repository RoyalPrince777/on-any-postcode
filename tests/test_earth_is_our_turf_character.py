"""Regression coverage for EARTH IS OUR TURF playable character."""
from mission_control import earth_is_our_turf, earth_is_our_turf_character


def test_character_status_contract():
    state=earth_is_our_turf_character.status()
    assert state["name"]=="EARTH IS OUR TURF Character"
    assert state["movement_modes"]==["foot","bike","car"]
    assert "top" in state["appearance_slots"]
    assert "m_town" in state["reputation_dimensions"]


def test_character_new_state_has_my_card_and_truth_guard():
    character=earth_is_our_turf_character.new_character(display_name="M Town Player")
    view=earth_is_our_turf_character.public_character(character)
    assert view["my_card"]["display_name"]=="M Town Player"
    assert view["my_card"]["home"]=="M Town · CR4"
    assert view["movement"]["node"]=="town-centre"
    assert view["truth"]["biometric_identity_claimed"] is False


def test_character_equipment_and_relationship_memory():
    character=earth_is_our_turf_character.new_character()
    character=earth_is_our_turf_character.equip(character,slot="headwear",item="25-8 cap")
    character=earth_is_our_turf_character.relationship(
        character,
        person_id="ally-001",
        trust=25,
        respect=40,
        loyalty=10,
    )
    view=earth_is_our_turf_character.public_character(character)
    assert view["appearance"]["slots"]["headwear"]=="25-8 cap"
    assert view["relationships"]["ally-001"]["respect"]==40
    assert "ally-001" in view["memory"]["people_met"]


def test_world_travel_updates_character_position_and_memory():
    state=earth_is_our_turf.new_world()
    state=earth_is_our_turf.action(state,command="navigate",target="lavender-avenue",mode="foot")
    state=earth_is_our_turf.action(state,command="travel-route")
    world=earth_is_our_turf.public_state(state)
    assert world["character"]["movement"]["node"]=="lavender-avenue"
    assert world["character"]["movement"]["mode"]=="foot"
    assert "lavender-avenue" in world["character"]["memory"]["places_visited"]


def test_help_local_increases_character_mtown_reputation():
    state=earth_is_our_turf.new_world()
    before=earth_is_our_turf.public_state(state)["character"]["reputation"]["m_town"]
    state=earth_is_our_turf.action(state,command="help-local")
    after=earth_is_our_turf.public_state(state)["character"]["reputation"]["m_town"]
    assert after==before+1
