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


def test_community_power_is_linked_without_ownership_transfer():
    community_power = next(
        view
        for view in linkup.LINK_DASHBOARD_VIEWS
        if view["id"] == "community_power"
    )

    assert community_power["owner"] == "Community Power"
    assert community_power["ownership"] == "linked_view"
    assert "contribution and reputation records" in community_power["boundary"]


def test_community_power_ownership_transfer_is_rejected():
    changed_views = tuple(
        {
            **view,
            "owner": "Communications",
            "ownership": "owned_view",
        }
        if view["id"] == "community_power"
        else view
        for view in linkup.LINK_DASHBOARD_VIEWS
    )

    validation = linkup.validate_link_scope(changed_views)

    assert validation["passed"] is False
    assert validation["checks"]["ownership_conflicts"] == 1
    assert any("ownership conflict" in error for error in validation["errors"])


def test_duplicate_link_view_is_rejected():
    validation = linkup.validate_link_scope(
        (*linkup.LINK_DASHBOARD_VIEWS, linkup.LINK_DASHBOARD_VIEWS[0])
    )

    assert validation["passed"] is False
    assert validation["checks"]["duplicate_ids"] == 1
    assert validation["checks"]["naming_conflicts"] == 1


def test_link_ui_is_read_only_and_does_not_create_database(
    client, tmp_path, monkeypatch
):
    database_path = tmp_path / "the-link.db"
    monkeypatch.setattr(config, "OAP_DATABASE_PATH", str(database_path))

    response = client.get("/mission/linkup")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "LinkUp boundaries verified" in page
    assert "Simple chat. Talk local. Build global." in page
    assert "The Spot / The Link / LinkUp" in page
    assert "Directory, Inbox and Community Power" in page
    assert "No member identities exposed" in page
    assert "No private messages exposed" in page
    assert "No message composer is registered" in page
    assert 'method="post"' not in page.lower()
    assert client.post("/mission/linkup").status_code == 405
    assert client.get("/mission/chat").status_code == 405
    assert not database_path.exists()


def test_link_ui_keeps_related_systems_separate(client):
    page = client.get("/mission/linkup").get_data(as_text=True)

    assert "Related systems stay separate" in page
    assert "Public announcements remain Signals" in page
    assert "Pulse remains the community heartbeat" in page
    assert "OAP TV Team Rooms" in page
    assert "this dashboard does not copy them" in page
    assert "Mail, Notifications and Broadcasts" in page
    assert "HRM receives approved audit metadata only" in page


def test_every_link_enablement_proposal_requires_human_approval():
    projection = linkup.get_public_link_dashboard()

    assert projection["proposed_enablement"]
    assert all(
        proposal["status"] == "Requires human approval"
        for proposal in projection["proposed_enablement"]
    )
    assert (
        projection["human_authority"]["status"]
        == "Final architecture approval required"
    )


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
        "correlation_id",
        "password",
        "token",
        "totp",
    ):
        assert private_key not in serialized
    assert '"mutation_enabled": true' not in serialized
    assert '"execute"' not in serialized


def test_link_route_does_not_reflect_query_input(client):
    attack = '<script>alert("inbox")</script>'

    page = client.get(
        "/mission/linkup", query_string={"conversation": attack}
    ).get_data(as_text=True)

    assert attack not in page
    assert "&lt;script&gt;" not in page
