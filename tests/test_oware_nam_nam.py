"""Nam-Nam rules, match lifecycle, and local Arena integration."""
import pytest

from mission_control import oware
from mission_control import oware_nam_nam as nam_nam


def test_relay_continues_from_an_occupied_landing_house():
    position = nam_nam.Position((1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2), (20, 24))
    result = nam_nam.play(position, nam_nam.options(position)[0])
    assert result.pits == (0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 2)
    assert result.turn == 1


def test_intermediate_four_goes_to_house_owner_and_last_four_goes_to_sower():
    position = nam_nam.Position((4, 0, 0, 0, 0, 2, 3, 3, 4, 0, 0, 0), (16, 16))
    result = nam_nam.play(position, nam_nam.options(position)[5])
    assert result.scores == (20, 20)
    assert result.pits[6:8] == (0, 0)
    assert result.turn == 1


def test_player_must_feed_empty_territory_if_possible():
    position = nam_nam.Position((1, 0, 3, 0, 4, 1, 3, 0, 0, 0, 0, 0), (16, 20))
    result = nam_nam.play(position, nam_nam.options(position)[5])
    assert result.turn == 0
    assert 0 not in nam_nam.options(result)
    assert 4 in nam_nam.options(result)


def test_impossible_feed_settles_remaining_seeds_and_changes_territory():
    position = nam_nam.Position((4, 2, 2, 0, 0, 1, 3, 0, 0, 0, 0, 0), (16, 20))
    result = nam_nam.play(position, nam_nam.options(position)[5])
    assert result.last_round == (28, 20)
    assert result.territory == 7


@pytest.mark.parametrize("scores,territory,completed", [((20, 20), 7, False), ((40, 0), 12, True)])
def test_last_eight_and_territory_win(scores, territory, completed):
    state = oware.new_game(variant="nam-nam")
    state["pits"] = [0, 0, 0, 0, 0, 1, 3, 0, 4, 0, 0, 0]
    for player, score in zip(state["players"], scores):
        player["captured"] = score
    result = oware.public_state(oware.move(oware._seal(state), pit=5, request_id="nam-nam-round"))
    assert result["owners"].count(0) == territory
    if completed:
        assert result["status"] == "completed"
        assert result["winner_id"] == "p1"
        assert result["players"][0]["captured"] == 48
        assert result["pits"] == [0] * 12
    else:
        assert result["status"] == "active"
        assert result["round"] == 2
        assert result["last_round"] == [28, 20]
        assert result["pits"] == [4] * 12
        assert result["current_player_id"] == "p2"
        assert result["legal_pits"] == [6, 7, 8, 9, 10]


@pytest.mark.parametrize("level", [None, "beginner", "standard", "expert"])
def test_nam_nam_local_modes_resume_and_conserve_seeds(client, csrf, level):
    headers = {"X-OAP-CSRF": csrf["csrf_token"]}
    start = client.post("/arena/oware/start", json={"variant": "nam-nam", "agent_level": level}, headers=headers)
    assert start.status_code == 201
    opening = start.get_json()
    assert opening["variant"] == "nam-nam"
    assert opening["round"] == 1
    assert opening["pits"] == [4] * 12
    move = {"pit": opening["legal_pits"][0], "request_id": "nam-nam-http", "game_id": opening["game_id"]}
    response = client.post("/arena/oware/move", json=move, headers=headers)
    assert response.status_code == 200
    state = response.get_json()
    assert state["current_player_id"] == ("p2" if level is None else "p1")
    assert sum(state["pits"]) + sum(p["captured"] for p in state["players"]) == 48
    assert client.get("/arena/oware/state").get_json() == state
    assert client.post("/arena/oware/move", json=move, headers=headers).get_json() == state


def test_unknown_variant_is_rejected(client, csrf):
    response = client.post(
        "/arena/oware/start", json={"variant": "other"},
        headers={"X-OAP-CSRF": csrf["csrf_token"]},
    )
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "oware_variant_invalid"


def test_agent_plays_first_when_new_round_belongs_to_it():
    state = oware.new_game(variant="nam-nam", agent_level="standard")
    state["pits"] = [0, 0, 0, 0, 0, 1, 3, 0, 4, 0, 0, 0]
    for player in state["players"]:
        player["captured"] = 20
    result = oware.play_local_turn(oware._seal(state), pit=5, request_id="nam-nam-agent-round")
    assert result["round"] == 2
    assert result["turn_index"] == 0
    assert result["last_round"] == [28, 20]
    assert result["request_receipts"][-1]["pit"] in range(6, 11)
    assert oware.play_local_turn(result, pit=5, request_id="nam-nam-agent-round") == result
