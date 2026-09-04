def _text(path: str) -> str:
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def test_mission_control_prioritises_real_booking_and_private_controls():
    page = _text("mission_control/templates/mission.html")
    booking = page.index("travel_supply.founder_dashboard")
    chat = page.index("mission_control.ollama_chat_dashboard")
    war_room = page.index("mission_control.war_room_dashboard")
    assert booking < chat < war_room
    assert "isac_spatial.dashboard" in page
    assert "provider_fabric.alignment_dashboard" in page
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
    assert "isac_spatial.dashboard" in page
    assert "provider_fabric.alignment_dashboard" in page
    assert "mission_control.judgement_dashboard" in page
    assert "the_link_dashboard" not in page
    assert "https://on-any-postcode.onrender.com/" in page


def test_isac_is_part_of_the_private_command_surface():
    page = _text("mission_control/templates/isac_spatial.html")
    assert "_command_nav.html" in page
    assert "Matrix RF spatial dashboard" in page
    assert "Software live · physical radio evidence fail-closed" in page
    assert "No biometric identity" in page
    assert "Human Authority remains final" in page


def test_alignment_dashboard_keeps_single_brain_and_seven_world_truth():
    page = _text("mission_control/templates/alignment_sovereignty.html")
    assert "SMI brain" in page
    assert "1 · SINGLE" in page
    assert "No 8th World" in page
    assert "Provider authority" in page
    assert "0 · NONE" in page
    assert "A4 / A5" in page
    assert "LOCKED" in page
    assert "No fake sovereignty claim" in page
    assert "Human Authority final" in page


def test_alignment_route_is_founder_only_and_renders(client):
    response = client.get("/mission/alignment")
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "Alignment &amp; Sovereignty" in page or "Alignment & Sovereignty" in page
    assert "26" in page
    assert "78" in page
    assert "7" in page


def test_sovereignty_deck_does_not_fake_execution_controls():
    page = _text("mission_control/templates/mission.html")
    assert "Default deny" in page
    assert "Human Authority" in page
    assert "this UI does not fake a toggle" in page
    assert "dashboard click never silently deploys" in page
