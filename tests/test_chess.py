import pytest

from mission_control import chess


def _move(state, source, target, n):
    return chess.move(
        state,
        source=source,
        target=target,
        request_id=f"chess-{n:04d}",
    )


def test_chess_basic_legal_move_and_turn():
    state=chess.new_game()
    state=_move(state,"e2","e4",1)
    view=chess.public_state(state)
    assert view["board"]["e4"]=="wP"
    assert view["turn"]=="Black"
    assert view["check"] is False
    assert view["result"] is None


def test_chess_rejects_move_that_ignores_check():
    state=chess.new_game()
    state=_move(state,"e2","e3",1)
    state=_move(state,"d7","d5",2)
    state=_move(state,"f1","b5",3)
    view=chess.public_state(state)
    assert view["turn"]=="Black"
    assert view["check"] is True

    with pytest.raises(ValueError, match="chess_self_check_invalid"):
        _move(state,"a7","a6",4)


def test_chess_fools_mate_ends_by_checkmate_not_king_capture():
    state=chess.new_game()
    state=_move(state,"f2","f3",1)
    state=_move(state,"e7","e5",2)
    state=_move(state,"g2","g4",3)
    state=_move(state,"d8","h4",4)

    view=chess.public_state(state)
    assert view["status"]=="completed"
    assert view["result"]=="checkmate"
    assert view["check"] is True
    assert view["winner"]=="Black"
    assert view["board"]["e1"]=="wK"


def test_chess_stop_retry_remains_idempotent_after_check_upgrade():
    state=chess.new_game()
    stopped=chess.stop(state,request_id="chess-stop-0001")
    assert chess.stop(stopped,request_id="chess-stop-0001")==stopped


def test_chess_stalemate_is_completed_without_winner():
    state=chess.new_game()
    state["board"]={
        "a8":"bK",
        "c6":"wK",
        "b6":"wQ",
    }
    state["turn"]="w"
    state["winner"]=None
    state["result"]=None
    state["check"]=False
    state=chess._seal(state)

    state=chess.move(
        state,
        source="b6",
        target="c7",
        request_id="chess-stalemate-0001",
    )
    view=chess.public_state(state)
    assert view["status"]=="completed"
    assert view["result"]=="stalemate"
    assert view["winner"] is None
    assert view["check"] is False


def test_chess_rejects_king_capture():
    state=chess.new_game()
    state["board"]={
        "e1":"wK",
        "e7":"wQ",
        "e8":"bK",
    }
    state["turn"]="w"
    state["winner"]=None
    state["result"]=None
    state["check"]=False
    state=chess._seal(state)

    with pytest.raises(ValueError, match="chess_king_capture_invalid"):
        chess.move(
            state,
            source="e7",
            target="e8",
            request_id="chess-king-capture-0001",
        )
