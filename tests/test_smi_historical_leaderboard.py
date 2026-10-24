"""Dated SMI leaderboard is visible yet distinct from earned agent stars."""

from mission_control import agents, intelligence_alliances, war_room


def test_historical_top_21_keeps_order_and_advisory_rating_not_earnings():
    board = intelligence_alliances.get_founder_alliance_board()
    snapshot = board["historical_top_21"]
    rows = snapshot["entries"]
    assert snapshot["as_of"] == "2026-10-15"
    assert snapshot["separate_from_career_stars"] is True
    assert len(rows) == 21
    assert [row["rank"] for row in rows] == list(range(1, 22))
    assert [row["name"] for row in rows[:6]] == [
        "Gyata", "Captain ALL IN", "Neo", "Nirmata",
        "Shere Khan", "Bagheera",
    ]
    assert all(row["historical_rating"] in (6, 7) for row in rows)
    assert all(row["historical_rating_max"] == 7 for row in rows)
    assert "Kaa" not in {row["name"] for row in rows}
    assert all("achievement_stars" not in row for row in rows)


def test_unregistered_historical_labels_remain_reference_only():
    rows = intelligence_alliances.get_founder_alliance_board()[
        "historical_top_21"
    ]["entries"]
    by_name = {row["name"]: row for row in rows}
    for name in ("Captain ALL IN", "Queen Bee", "Tigress", "Lioness", "Bee Swarm"):
        assert by_name[name]["agent_id"] is None
        assert by_name[name]["registry_linked"] is False
    for name in ("Gyata", "Neo", "Shere Khan", "Bagheera", "Gorilla", "Fox"):
        assert by_name[name]["agent_id"] is not None
        assert by_name[name]["registry_linked"] is True
    assert agents.validate_agent_registry()["passed"] is True


def test_founder_war_room_has_smi_top21_and_all_six_alliances(client, anonymous_client):
    response = client.get("/mission/war-room")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    for expected in (
        'id="smi-agent-rankings"',
        "Historic Top 21 + Six Specialist Alliances",
        "2026-10-15",
        "Captain ALL IN",
        "Shere Khan",
        "Bagheera",
        "Mission: Impossible Intelligence",
        "Terminator Intelligence",
        "Predator Intelligence",
        "Transformers Intelligence",
        "Jungle Book Intelligence",
        "Batman Intelligence",
        "(reference only)",
        "separately",
        "0 approved movements recorded",
    ):
        assert expected in html
    assert 'method="post"' not in html.lower()
    assert anonymous_client.get("/mission/war-room").status_code == 302
    assert anonymous_client.get("/mission/war-room/status").status_code == 401


def test_existing_dashboard_exposes_snapshot_without_minting_stars():
    dashboard = war_room.get_war_room_dashboard()
    board = dashboard["intelligence_alliance_board"]
    assert len(board["historical_top_21"]["entries"]) == 21
    assert len(board["alliances"]) == 6
    assert dashboard["agent_achievement_rankings"]["awarded_movements"] == 0
    assert all(
        row["achievement_stars"] == 0
        for row in dashboard["agent_achievement_rankings"]["ranking"]
    )
    assert dashboard["can_approve"] is False
    assert dashboard["can_execute"] is False
