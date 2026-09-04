def _text(path: str) -> str:
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def test_mission_control_prioritises_real_booking_and_private_controls():
    page = _text("mission_control/templates/mission.html")
    booking = page.index("travel_supply.founder_dashboard")
    chat = page.index("mission_control.ollama_chat_dashboard")
    war_room = page.index("mission_control.war_room_dashboard")
    assert booking < chat < war_room
    assert "mission_control.judgement_dashboard" in page
    assert "mission_control.infrastructure_dashboard" in page
    assert "humanitarian_tracker.dashboard" in page
    assert "the_link_dashboard" not in page
    assert "No operational controls are enabled" not in page
    assert "https://on-any-postcode.onrender.com/" in page


def test_my_world_is_profile_not_twelve_workspace_menu():
    page = _text("templates/my_world.html")
    assert "Your 12 private workspaces" not in page
    assert "for workspace in workspaces" not in page
    assert "travel_supply.founder_dashboard" in page
    assert "mission_control.mission_workspace" in page
    assert "auth_sign_out" in page
    assert "method=\"post\"" in page


def test_infrastructure_menu_uses_private_working_routes():
    page = _text("mission_control/templates/mission_control/infrastructure.html")
    assert "travel_supply.founder_dashboard" in page
    assert "mission_control.ollama_chat_dashboard" in page
    assert "mission_control.war_room_dashboard" in page
    assert "mission_control.judgement_dashboard" in page
    assert "the_link_dashboard" not in page
    assert "https://on-any-postcode.onrender.com/" in page


def test_sovereignty_deck_does_not_fake_execution_controls():
    page = _text("mission_control/templates/mission.html")
    assert "Default deny" in page
    assert "Human Authority" in page
    assert "this UI does not fake a toggle" in page
    assert "dashboard click never silently deploys" in page
