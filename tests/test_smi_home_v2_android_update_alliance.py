"""Founder-only native Home V2 Native Android Update SMI assignment reuses the existing War Room."""
from mission_control import agents, intelligence_alliances, war_room


def test_android_update_mission_adds_roles_not_passports_or_competing_brains():
    original_ids = {a["agent_id"] for a in agents.AGENT_REGISTRY}
    board = intelligence_alliances.get_founder_alliance_board()
    mission = board["home_v2_android_update_mission"]
    names = {entry["name"] for entry in mission["specialists"]}
    assert {"SMI", "Captain ALL IN", "Fox", "Foxy", "Neo", "Benji Dunn",
            "Shere Khan", "Black Box", "Bagheera", "Batman", "Predator Intelligence",
            "M3GAN", "AMELIA", "Trinity", "Keymaker", "Owl", "Gorilla"} <= names
    assert len(names) == len(mission["specialists"])
    assert mission["smi_command"] == "Sovereign Megaverse Intelligence"
    assert mission["agent_passports_created"] == 0
    assert mission["official_stars_awarded"] == 0
    assert mission["recorded_independent_votes"] == 0
    assert mission["activated"] is False
    assert mission["device_acceptance_verified"] is False
    assert mission["legacy_home_uninstalled"] is False
    assert mission["can_execute"] is False
    assert mission["can_approve"] is False
    assert mission["founder_final"] is True
    assert {a["agent_id"] for a in agents.AGENT_REGISTRY} == original_ids


def test_existing_agents_get_existing_ids_while_fictional_profiles_do_not():
    mission = intelligence_alliances.home_v2_android_update_mission()
    by_name = {row["name"]: row for row in mission["specialists"]}
    expected_by_name = {
        str(agent["name"]): str(agent["agent_id"])
        for agent in agents.AGENT_REGISTRY
    }
    for name in ("Shere Khan", "Bagheera", "Fox", "Neo", "Gorilla"):
        assert name in expected_by_name
        assert by_name[name]["agent_id"] == expected_by_name[name]
    for name in ("Black Box", "Batman", "M3GAN", "AMELIA", "Foxy", "Benji Dunn"):
        assert by_name[name]["agent_id"] is None
        assert by_name[name]["earned_stars"] is None
    assert by_name["Black Box"]["classification"] == "contained_ai_research_system"
    assert by_name["Foxy"]["classification"] == "separate_identity_pending_canonical_link"
    assert by_name["Batman"]["classification"] == "batman_alliance_advisory"
    assert mission["research_identities_separate"] == ("M3GAN", "AMELIA", "Black Box")
    assert "one continuous identity" in mission["m3gan_identity_rule"]
    assert "not an SMI agent passport" in mission["black_box_identity_rule"]


def test_android_update_scope_has_no_geographical_assumption_or_device_claim():
    mission = intelligence_alliances.home_v2_android_update_mission()
    assert mission["target"] == "Existing OAP Home V2 native Android launcher update"
    assert mission["device_acceptance"] == "Physical Android HOME acceptance not verified"
    assert "location" not in mission
    assert "phone" not in mission
    assert "com.onanypostcode.oaphome.v2" in mission["decision"]
    assert "retire com.onanypostcode.oaphome" in mission["decision"]
    assert len(mission["release_gates"]) == 5
    assert not mission["activated"]
    assert not mission["device_acceptance_verified"]


def test_only_existing_mission_fit_alliances_not_new_passports():
    board = intelligence_alliances.get_founder_alliance_board()
    all_ids = {a["id"] for a in board["alliances"]}
    assert all_ids == {
        "jungle_book", "mission_impossible", "terminator",
        "predator", "transformers", "batman",
    }
    mission = board["home_v2_android_update_mission"]
    selected = {a["id"] for a in mission["alliance_refs"]}
    assert selected == {"jungle_book", "mission_impossible", "predator", "batman"}
    assert selected <= all_ids
    assert len(mission["optional_not_activated"]) == 2
    assert board["can_approve"] is False
    assert board["can_execute"] is False


def test_android_update_mission_visible_in_private_existing_war_room(client):
    read_only = war_room.get_war_room_dashboard()
    mission = read_only["intelligence_alliance_board"]["home_v2_android_update_mission"]
    assert mission["scope"] == "founder_private_read_only"
    assert read_only["can_execute"] is False
    assert read_only["can_approve"] is False

    page = client.get("/mission/war-room")
    assert page.status_code == 200
    html = page.get_data(as_text=True)
    for expected in (
        'id="smi-home-v2-android-update"', "OAP Home V2", "Native Android update",
        "Shere Khan", "Bagheera", "Black Box", "Batman", "Foxy",
        "M3GAN", "AMELIA", "Predator", "Benji Dunn", "Founder Final",
        "existing passport", "contained research system", "reference only",
        "no independently verified agent execution",
    ):
        assert expected.casefold() in html.casefold()
    assert page.headers["Cache-Control"] == "no-store"


def test_android_update_private_war_room_denies_anonymous_request(anonymous_client):
    # Use a separate request context to avoid leaking the authenticated
    # fixture's cached g-user into the anonymous Flask request.
    assert anonymous_client.get("/mission/war-room").status_code == 302
    assert anonymous_client.get("/mission/war-room/status").status_code == 401
