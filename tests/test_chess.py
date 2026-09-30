from mission_control import chess


def test_chess_basic_legal_move_and_turn():
    state=chess.new_game()
    state=chess.move(state,source="e2",target="e4",request_id="chess-0001")
    view=chess.public_state(state)
    assert view["board"]["e4"]=="wP"
    assert view["turn"]=="Black"
