from mission_control import dot


def test_dot_claims_completed_box():
    state=dot.new_game()
    for i,(a,b) in enumerate([("0,0","1,0"),("0,0","0,1"),("1,0","1,1"),("0,1","1,1")],1):
        state=dot.draw(state,a=a,b=b,request_id=f"dot-{i:04d}")
    assert len(state["boxes"])==1
    assert sum(p["score"] for p in state["players"])==1


def test_dot_engine_rejects_noncanonical_edge_nodes():
    for a, b in (("00,0", "1,0"), ("x,0", "1,0"), ("0,0", "3,0")):
        try:
            dot.draw(dot.new_game(), a=a, b=b, request_id="dot-canon-0001")
        except ValueError as exc:
            assert str(exc) == "dot_edge_invalid"
        else:
            raise AssertionError("invalid Dot node accepted")
