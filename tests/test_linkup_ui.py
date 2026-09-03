from __future__ import annotations

import json

from mission_control import config, linkup


def test_link_dashboard_preserves_three_approved_views():
    assert linkup.LOCKED_LINK_VIEW_NAMES == (
        "Directory",
        "Inbox",
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
    assert linkup.LINK_UP_PUBLIC_VOCABULARY["video_call"] == "Face Up"
    assert linkup.LINK_UP_PUBLIC_VOCABULARY["share_location"] == "Share My Spot"
    assert linkup.LINK_UP_PUBLIC_VOCABULARY["delivered"] == "Landed"
    assert linkup.LINK_UP_PUBLIC_VOCABULARY["read"] == "Seen"


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


def test_public_link_ui_is_simple_and_read_only(client, tmp_path, monkeypatch):
    database_path = tmp_path / "the-link.db"
    monkeypatch.setattr(config, "OAP_DATABASE_PATH", str(database_path))
    response = client.get("/linkup")
    page = response.get_data(as_text=True)
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "Simple private chat." in page
    assert "Message your Links. Voice, Call and Face Up stay inside each chat." in page
    assert "Circle" not in page
    assert 'method="post"' not in page.lower()
    assert client.post("/linkup").status_code == 405
    assert not database_path.exists()


def test_public_link_projection_is_presentation_only():
    projection = linkup.get_public_link_dashboard()
    assert set(projection) == {"product_name", "tagline", "law", "features"}
    assert projection["product_name"] == "Link Up"
    assert projection["tagline"] == "Simple private chat."
    assert projection["law"] == "The Link → Link Up"
    assert [feature["name"] for feature in projection["features"]] == ["Chats", "Calls"]
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
