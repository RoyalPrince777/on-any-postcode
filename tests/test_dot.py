from mission_control import dot


def test_dot_claims_completed_box():
    state=dot.new_game()
    for i,(a,b) in enumerate([("0,0","1,0"),("0,0","0,1"),("1,0","1,1"),("0,1","1,1")],1):
        state=dot.draw(state,a=a,b=b,request_id=f"dot-{i:04d}")
    assert len(state["boxes"])==1
    assert sum(p["score"] for p in state["players"])==1
