from mission_control import connect4


def test_connect4_horizontal_win_and_idempotency():
    state=connect4.new_game("Alpha","Bravo")
    moves=[0,0,1,1,2,2,3]
    for i,col in enumerate(moves,1):
        state=connect4.drop(state,column=col,request_id=f"move-{i:04d}")
    view=connect4.public_state(state)
    assert view["status"]=="completed"
    assert view["winner_id"]=="p1"
    again=connect4.drop(state,column=6,request_id="move-0007")
    assert again==state


def test_connect4_fail_closed_on_tamper():
    state=connect4.new_game()
    state["board"][5][0]=1
    try:
        connect4.drop(state,column=0,request_id="move-0001")
        assert False
    except ValueError as exc:
        assert str(exc)=="connect4_checkpoint_invalid"
