from __future__ import annotations

import json
from pathlib import Path

from mission_control import config, linkup, product_store


def test_link_dashboard_preserves_three_approved_views():
    assert linkup.LOCKED_LINK_VIEW_NAMES == (
        "👥 People",
        "🔗 Link Ups",
        "Community Power",
    )
    assert linkup.LOCKED_LINK_VIEW_IDS == (
        "directory",
        "inbox",
        "community_power",
    )
    validation = linkup.validate_link_scope()
    assert validation["passed"] is True
    assert validation["errors"] == []
    assert validation["checks"] == {
        "dashboard_views": 3,
        "communication_views": 2,
        "linked_views": 1,
        "duplicate_ids": 0,
        "naming_conflicts": 0,
        "ownership_conflicts": 0,
        "mutation_controls": 0,
    }


def test_link_up_language_law_keeps_messenger_terms_simple():
    assert linkup.LINK_UP_LANGUAGE_LAW == (
        "Brand language for identity.",
        "Human language for conversation.",
        "Plain language for safety.",
        "Local character without global confusion.",
    )
    assert linkup.LINK_UP_PUBLIC_VOCABULARY["product"] == "Link Up"
    assert linkup.LINK_UP_PUBLIC_VOCABULARY["new_conversation"] == "New Link"
    assert "group" not in linkup.LINK_UP_PUBLIC_VOCABULARY
    assert linkup.LINK_UP_PUBLIC_VOCABULARY["video_call"] == "Link Call"
    assert linkup.LINK_UP_PUBLIC_VOCABULARY["notifications"] == "Tap In"
    assert linkup.LINK_UP_PUBLIC_VOCABULARY["share_location"] == "Share My Spot"
    assert linkup.LINK_UP_PUBLIC_VOCABULARY["in_transit"] == "Landing…"
    assert linkup.LINK_UP_PUBLIC_VOCABULARY["delivered"] == "Landed"
    assert linkup.LINK_UP_PUBLIC_VOCABULARY["read"] == "Lit"


def test_protected_link_runtime_matches_existing_communications_store():
    assert linkup.PROTECTED_LINK_RUNTIME == {
        "authenticated_identity_required": True,
        "csrf_required_for_mutations": True,
        "sender_recipient_scope": True,
        "message_persistence": "Postgres Communications store",
        "rate_limit_enabled": True,
        "guardian_message_screening": True,
        "read_receipts": True,
        "public_message_projection": False,
        "human_authority_final": True,
    }


def test_world_rooms_are_linked_without_messenger_ownership():
    community_power = next(
        view for view in linkup.LINK_DASHBOARD_VIEWS if view["id"] == "community_power"
    )
    assert community_power["owner"] == "Community Power"
    assert community_power["ownership"] == "linked_view"
    assert "World Rooms" in community_power["purpose"]
    assert "never by the private messenger" in community_power["boundary"]


def test_community_power_ownership_transfer_is_rejected():
    changed_views = tuple(
        {**view, "owner": "Communications", "ownership": "owned_view"}
        if view["id"] == "community_power"
        else view
        for view in linkup.LINK_DASHBOARD_VIEWS
    )
    validation = linkup.validate_link_scope(changed_views)
    assert validation["passed"] is False
    assert validation["checks"]["ownership_conflicts"] == 1


def test_duplicate_link_view_is_rejected():
    validation = linkup.validate_link_scope(
        (*linkup.LINK_DASHBOARD_VIEWS, linkup.LINK_DASHBOARD_VIEWS[0])
    )
    assert validation["passed"] is False
    assert validation["checks"]["duplicate_ids"] == 1
    assert validation["checks"]["naming_conflicts"] == 1



def test_public_link_ui_shows_private_chat_front_door_without_public_discovery_noise(anonymous_client, tmp_path, monkeypatch):
    database_path = tmp_path / "the-link.db"
    monkeypatch.setattr(config, "OAP_DATABASE_PATH", str(database_path))
    response = anonymous_client.get("/linkup")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert 'aria-label="Link Up private chat"' in page
    assert "Private chat for your Links." in page
    assert "Create My Card" in page
    assert "The Link" in page

    for public_noise in (
        "Search Link Up",
        "Discovery",
        "Nearby People",
        "Community Signals",
        "Spotlight",
        "Open public spaces",
        "Work &amp; collaboration",
        "PUBLIC · CONNECT · CREATE",
    ):
        assert public_noise not in page

    assert "Enter My World" not in page
    assert 'href="/auth"' not in page
    assert "World Rooms" not in page
    assert 'method="post"' not in page.lower()
    assert anonymous_client.post("/linkup").status_code == 405
    assert not database_path.exists()


def test_linkup_template_keeps_policy_copy_off_the_visible_messenger():
    page = Path("mission_control/templates/linkup.html").read_text(encoding="utf-8")
    for copy in (
        "first-party OAP Data",
        "accepted Link",
        "World Rooms",
        "live outside this messenger",
        "Private media runtime required",
    ):
        assert copy not in page


def test_public_link_projection_is_presentation_only():
    projection = linkup.get_public_link_dashboard()
    assert set(projection) == {"product_name", "tagline", "law", "features"}
    assert projection["product_name"] == "Link Up"
    assert projection["tagline"] == "Simple private chat."
    assert projection["law"] == "The Link → Link Up"
    assert [feature["name"] for feature in projection["features"]] == [
        "🔗 Link Ups",
        "📞 Call & Link Call",
    ]
    assert "Circle" not in json.dumps(projection)


def test_public_link_projection_contains_no_people_or_conversations():
    serialized = json.dumps(linkup.get_public_link_dashboard()).lower()
    for private_key in (
        "message_body",
        "sender_id",
        "recipient_id",
        "member_id",
        "email_address",
        "phone_number",
        "conversation_id",
        "password",
        "token",
    ):
        assert private_key not in serialized


def test_link_route_does_not_reflect_query_input(client):
    attack = '<script>alert("inbox")</script>'
    page = client.get("/linkup", query_string={"conversation": attack}).get_data(as_text=True)
    assert attack not in page
    assert "&lt;script&gt;" not in page


def test_linkup_member_card_id_is_human_readable_without_exposing_raw_uuid():
    identity = "00000000-0000-0000-0000-00000000abcd"
    card_id = product_store.member_card_id(identity)

    assert card_id == "OAP-00000000"
    assert identity not in card_id


def test_linkup_template_exposes_my_card_and_peer_identity_labels():
    page = Path("mission_control/templates/linkup.html").read_text(encoding="utf-8")

    assert "My Card" in page
    assert "my_card.card_id" in page
    assert "thread.card_id" in page
    assert "thread.username" in page
    assert "Choose an OAP member" in page
    assert "Choose a Certified member" not in page


def test_linkup_chat_surfaces_link_request_onboarding():
    page = Path("mission_control/templates/linkup.html").read_text(encoding="utf-8")

    assert "Link Requests" in page
    assert "Send Link Request" in page
    assert "Accept Link" in page
    assert "Messaging unlocks only after it is accepted." in page
    assert "Your My Card is still active above." in page
    assert "Link Requests are not ready, so new private chat remains locked." in page


def test_linkup_seven_star_gate_fails_closed_until_all_runtime_evidence_is_true():
    status = linkup.linkup_seven_star_status(
        {
            "identity": True,
            "relationship": True,
            "messaging": True,
            "safety": True,
            "privacy": False,
            "resilience": False,
            "live_gate": False,
        }
    )

    assert status["star_count"] == 4
    assert status["star_total"] == 7
    assert status["ready"] is False
    assert status["signal"] == "purple"
    assert status["stars_display"] == "★★★★☆☆☆"


def test_linkup_seven_star_gate_reaches_green_only_at_seven_of_seven():
    evidence = {gate["id"]: True for gate in linkup.LINK_UP_SEVEN_STAR_GATE}
    status = linkup.linkup_seven_star_status(evidence)

    assert status["star_count"] == 7
    assert status["percent"] == 100
    assert status["ready"] is True
    assert status["signal"] == "green"
    assert status["human_authority_final"] is True


def test_linkup_template_hides_internal_seven_star_gate_from_users():
    page = Path("mission_control/templates/linkup.html").read_text(encoding="utf-8")

    assert "7-Star Gate" not in page
    assert "linkup-stars-grid" not in page


def test_linkup_emoji_and_conversation_settings_reuse_existing_owners():
    page = Path("mission_control/templates/linkup.html").read_text(encoding="utf-8")
    script = Path("static/linkup_realtime.js").read_text(encoding="utf-8")
    assert "data-oap-emoji-picker" in page
    assert "data-oap-emoji=" in page
    assert 'aria-label="Choose emoji"' in page
    assert "data-oap-emoji" in script
    assert "textarea.setRangeText(emoji, start, end," in script
    assert "next.length > textarea.maxLength" in script
    assert 'textarea.dispatchEvent(new Event("input", { bubbles: true }))' in script
    assert "data-oap-conversation-settings" not in page
    assert 'aria-label="Conversation settings"' in page
    assert "linkup_safety.block_member" in page
    assert 'name="csrf_token" value="{{ oap_csrf_token }}"' in page
    assert "My Card sharing enabled" not in page


def test_linkup_empty_mobile_inbox_opens_new_link_workspace():
    script = Path("static/linkup_messenger.js").read_text(encoding="utf-8")

    assert 'panels.some((panel) => panel.dataset.linkupPanel === "new")' in script
    assert 'openPanel("new")' in script



def test_linkup_public_shell_stays_private_and_keeps_my_card_entry():
    template = Path("mission_control/templates/linkup.html").read_text(encoding="utf-8")

    assert "Enter My World" not in template
    assert "url_for('my_card_create_page')" in template
    assert "Create My Card" in template
    assert 'aria-label="Link Up private chat"' in template
    assert "linkup-royal-tools" not in template
    assert "linkup-royal-stream" not in template
    assert "linkup-royal-bottom" not in template
    assert "linkup-public-search" not in template



def test_linkup_private_menu_is_low_noise_and_oap_native():
    template = Path("mission_control/templates/linkup.html").read_text(encoding="utf-8")

    assert 'aria-label="Link Up private menu"' in template
    for label in ("Link Ups", "Ring", "Now", "Tap In", "More"):
        assert f">{label}</a>" in template

    assert 'id="linkup-conversations"' in template
    assert 'id="linkup-ring"' in template
    assert 'id="linkup-now"' in template
    assert 'id="linkup-tap-in"' in template
    assert 'id="linkup-more"' in template

    for public_noise in (
        "<strong>Discovery</strong>",
        "<strong>Nearby People</strong>",
        "<strong>Community Signals</strong>",
        "<strong>Spotlight</strong>",
        "<strong>Opportunities</strong>",
    ):
        assert public_noise not in template


def test_empty_linkup_chat_has_real_next_actions():
    template = Path("mission_control/templates/linkup.html").read_text(encoding="utf-8")

    assert "No Link Ups yet." in template
    assert "Discover people in OAP World" in template
    assert "Open The Link" in template
    assert "Open My Card" in template


def test_linkup_has_no_room_navigation_or_typing_language():
    page = Path("mission_control/templates/linkup.html").read_text(encoding="utf-8")
    script = Path("static/linkup_messages.js").read_text(encoding="utf-8")

    assert "link_circles.circle_page" not in page
    assert ">Room</a>" not in page
    assert "Typing…" not in script
    assert "/linkup/activity/typing" not in script
    assert "Landing → Landed → Lit" in script

def test_my_emojis_are_private_chat_composer_language():
    template = Path("mission_control/templates/linkup.html").read_text(encoding="utf-8")

    assert 'aria-label="My Emojis"' in template
    assert 'title="My Emojis"' in template
    assert "My Emojis stay inside the private chat" in template
