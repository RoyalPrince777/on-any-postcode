from mission_control import ludo


def test_ludo_turns_and_win():
    state=ludo.new_game(["Alpha","Bravo"])
    state=ludo.move(state,steps=6,request_id="ludo-0001")
    assert state["turn_index"]==1
    state["players"][1]["piece"]=23;state=ludo._seal(state)
    state=ludo.move(state,steps=1,request_id="ludo-0002")
    assert state["status"]=="completed" and state["winner_id"]=="p2"
