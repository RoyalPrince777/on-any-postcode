from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

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
    assert linkup.LINK_UP_PUBLIC_VOCABULARY["notifications"] == "Incoming"
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


def test_public_link_ui_shows_app_shell_without_private_data(anonymous_client, tmp_path, monkeypatch):
    database_path = tmp_path / "the-link.db"
    monkeypatch.setattr(config, "OAP_DATABASE_PATH", str(database_path))
    response = anonymous_client.get("/linkup")
    page = response.get_data(as_text=True)
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert 'aria-label="Link Up app"' in page
    assert "PUBLIC · CONNECT · CREATE" in page
    assert "Create My Card" in page
    assert "Free and optional. Browse without signing in." in page
    assert 'data-network="unknown"' in page
    assert 'class="linkup-create-card"' not in page
    assert page.count('class="linkup-card-summary"') == 1
    assert 'aria-label="Link Up master tools"' not in page
    assert 'aria-label="Link Up public bottom navigation"' in page
    assert 'href="/the-link"' in page
    assert page.count('<nav class="linkup-royal-bottom"') == 1
    # Both public People actions lead to the protected accepted-Links view
    # via the existing member sign-in gate, not back around a public UI loop.
    assert page.count("next=/linkup") + page.count("next=%2Flinkup") == 1
    assert 'href="/linkup?intent=message"' in page
    assert page.count('href="/linkup?intent=message"') == 1
    assert page.count('aria-label="Link Up public bottom navigation"') == 1
    assert "Nearby People" not in page
    assert "Spotlight" not in page
    assert "Community Signals" not in page
    assert 'aria-label="Private Link Up messenger"' not in page
    assert 'data-linkup-search' not in page
    assert "Enter My World" not in page
    assert 'href="/my-card/create"' in page
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
    assert 'aria-label="My Emojis"' in page
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


def test_linkup_public_shell_uses_free_my_card_actions():
    template = Path("mission_control/templates/linkup.html").read_text(encoding="utf-8")

    assert "Enter My World" not in template
    assert "url_for('my_card_create_page')" in template
    assert "Create My Card" in template
    assert "PUBLIC · CONNECT · CREATE" in template
    assert "linkup-royal-home" in template
    assert "linkup-royal-tools" not in template
    assert "linkup-royal-bottom" in template



def test_linkup_master_menu_is_only_linkups_ring_now_incoming_and_more():
    template = Path("mission_control/templates/linkup.html").read_text(encoding="utf-8")

    assert 'aria-label="Link Up private menu"' in template
    assert '>💬 Link Ups</a>' in template
    assert '>📞 Ring</a>' in template
    assert '>🟢 Now</a>' in template
    assert '>🔔 Incoming</a>' in template
    assert '>⋯ More</a>' in template
    assert 'id="linkup-ring"' in template
    assert 'id="linkup-incoming"' in template
    assert 'id="linkup-requests"' in template
    assert "url_for('auth_sign_out')" in template
    assert 'method="post"' in template
    assert 'name="csrf_token" value="{{ oap_csrf_token }}"' in template
    assert '>Leave My World</button>' in template
    assert 'id="linkup-more"' in template
    assert '>My Card</a>' in template
    assert '>Link Requests</a>' in template
    assert '>My Controls</a>' in template
    for removed in (
        "<strong>Discovery</strong>",
        "<strong>Spotlight</strong>",
        "Nearby People",
        "Community Signals",
    ):
        assert removed not in template


def test_empty_linkup_chat_has_real_next_actions():
    template = Path("mission_control/templates/linkup.html").read_text(encoding="utf-8")

    assert "No Link Ups yet." in template
    assert "Discover people in OAP World" not in template
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
    assert 'data-oap-emoji-picker' in template
    # A working private composer control is evidence; explanatory copy is not.


def test_private_linkup_intents_take_guests_to_existing_member_sign_in(anonymous_client):
    # Public browsing must not require sign-in or expose private member records.
    assert anonymous_client.get("/linkup").status_code == 200
    for intent in ("message", "link-call"):
        response = anonymous_client.get("/linkup", query_string={"intent": intent})
        assert response.status_code == 302
        destination = urlsplit(response.headers["Location"])
        assert destination.path in {"/auth", "/enter-my-world"}
        assert parse_qs(destination.query)["next"] == [f"/linkup?intent={intent}"]
        assert response.headers["Location"].startswith("/")


def test_public_spot_link_linkup_chain_is_navigable(anonymous_client):
    spot = anonymous_client.get("/the-spot")
    link = anonymous_client.get("/the-link")
    public_linkup = anonymous_client.get("/linkup")
    assert spot.status_code == link.status_code == public_linkup.status_code == 200
    assert 'href="/the-link"' in spot.get_data(as_text=True)
    assert 'href="/linkup?intent=message"' in link.get_data(as_text=True)
    assert 'href="/linkup?intent=message"' in public_linkup.get_data(as_text=True)



def test_combined_world_spot_linkup_secure_handoff(anonymous_client):
    """Exercise the combined public journey and the actual private sign-in gate.

    Source/HTTP acceptance only: this does not claim a device, call, or
    provider-backed two-member message was completed.
    """
    world = anonymous_client.get("/world", query_string={"source": "oap-os"})
    assert world.status_code == 200
    assert 'href="/the-spot"' in world.get_data(as_text=True)

    spot = anonymous_client.get("/the-spot")
    assert spot.status_code == 200
    assert spot.headers["Cache-Control"] == "no-store"
    spot_html = spot.get_data(as_text=True)
    assert 'href="/pulse"' in spot_html
    assert 'href="/the-link"' in spot_html
    assert spot_html.count('href="/the-link"') == 1
    assert spot_html.count("<summary>More</summary>") == 1
    assert 'href="/studio"' in spot_html
    assert 'href="/arena"' in spot_html
    assert 'href="/my-card/create"' in spot_html

    link = anonymous_client.get("/the-link")
    assert link.status_code == 200
    assert link.headers["Cache-Control"] == "no-store"
    link_html = link.get_data(as_text=True)
    assert 'href="/linkup?intent=message"' in link_html
    assert 'href="/the-spot/postcode-rooms"' in link_html
    assert link_html.count("<summary>More</summary>") == 1

    public_linkup = anonymous_client.get("/linkup")
    assert public_linkup.status_code == 200
    assert 'aria-label="Link Up public bottom navigation"' in public_linkup.get_data(as_text=True)
    assert 'aria-label="Private Link Up messenger"' not in public_linkup.get_data(as_text=True)

    for private_intent in ("message", "link-call"):
        response = anonymous_client.get(
            "/linkup", query_string={"intent": private_intent}
        )
        assert response.status_code == 302
        auth_target = urlsplit(response.headers["Location"])
        assert auth_target.path in {"/auth", "/enter-my-world"}
        assert parse_qs(auth_target.query)["next"] == [
            f"/linkup?intent={private_intent}"
        ]


def test_private_linkup_mobile_menu_reveals_ring_incoming_and_more():
    """A mobile sidebar hash must reveal the chat before scrolling to it."""
    template = Path("mission_control/templates/linkup.html").read_text(encoding="utf-8")
    script = Path("static/linkup_messenger.js").read_text(encoding="utf-8")
    style = Path("static/linkup_messenger.css").read_text(encoding="utf-8")

    for target in ("linkup-chats", "linkup-now", "linkup-ring", "linkup-incoming", "linkup-more"):
        assert f'href="#{target}"' in template
        assert f'id="{target}"' in template
    assert script.count('["#linkup-ring", "#linkup-incoming", "#linkup-more"]') == 1
    assert 'openPanel(active.dataset.linkupPanel, { focusComposer: false })' in script
    assert 'if (targetId === "#linkup-more") target.open = true' in script
    assert 'app.dataset.chatOpen = "true"' in script
    assert '.linkup-master-nav{display:grid;grid-template-columns:repeat(5,minmax(0,1fr))' in style
    assert '.linkup-royal-bottom{padding-bottom:max(10px,env(safe-area-inset-bottom,0px))}' in style


def test_combined_guest_menu_keeps_one_route_per_core_destination(anonymous_client):
    spot = anonymous_client.get("/the-spot")
    link = anonymous_client.get("/the-link")
    public_linkup = anonymous_client.get("/linkup")
    assert spot.status_code == link.status_code == public_linkup.status_code == 200

    spot_html = spot.get_data(as_text=True)
    link_html = link.get_data(as_text=True)
    public_html = public_linkup.get_data(as_text=True)

    assert spot_html.count('href="/the-link"') == 1
    assert spot_html.count('href="/store"') == 1
    assert link_html.count('href="/linkup?intent=message"') == 1
    assert link_html.count('href="/the-spot"') == 1
    assert public_html.count('href="/linkup?intent=message"') == 1
    assert public_html.count('aria-label="Link Up public bottom navigation"') == 1
    assert 'class="linkup-topbar linkup-guest-topbar"' in public_html
    for path in ("/store", "/oap-map", "/movement"):
        assert anonymous_client.get(path).status_code in (200, 302)
