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



def test_chess_castles_kingside_and_moves_rook():
    state = chess.new_game()
    state["board"] = {"e1": "wK", "h1": "wR", "e8": "bK", "a8": "bR"}
    state["turn"] = "w"
    state["castling"] = {"wK": True, "wQ": False, "bK": False, "bQ": True}
    state["en_passant"] = None
    state["position_counts"] = {}
    state = chess._seal(state)

    state = chess.move(
        state,
        source="e1",
        target="g1",
        request_id="chess-castle-0001",
    )
    assert state["board"]["g1"] == "wK"
    assert state["board"]["f1"] == "wR"
    assert "e1" not in state["board"] and "h1" not in state["board"]
    assert state["castling"]["wK"] is False


def test_chess_en_passant_real_sequence():
    state = chess.new_game()
    state = _move(state, "e2", "e4", 11)
    state = _move(state, "a7", "a6", 12)
    state = _move(state, "e4", "e5", 13)
    state = _move(state, "d7", "d5", 14)
    assert state["en_passant"] == "d6"

    state = _move(state, "e5", "d6", 15)
    assert state["board"]["d6"] == "wP"
    assert "d5" not in state["board"]
    assert state["request_receipts"][-1]["special"] == "en_passant"


def test_chess_promotion_requires_and_applies_choice():
    state = chess.new_game()
    state["board"] = {"h1": "wK", "h8": "bK", "a7": "wP"}
    state["turn"] = "w"
    state["castling"] = {"wK": False, "wQ": False, "bK": False, "bQ": False}
    state["en_passant"] = None
    state["position_counts"] = {}
    state = chess._seal(state)

    with pytest.raises(ValueError, match="chess_promotion_required"):
        chess.move(
            state,
            source="a7",
            target="a8",
            request_id="chess-promote-0001",
        )

    promoted = chess.move(
        state,
        source="a7",
        target="a8",
        promotion="N",
        request_id="chess-promote-0002",
    )
    assert promoted["board"]["a8"] == "wN"
    assert promoted["request_receipts"][-1]["special"] == "promotion"


def test_chess_threefold_repetition_draw():
    state = chess.new_game()
    moves = [
        ("g1", "f3"), ("g8", "f6"), ("f3", "g1"), ("f6", "g8"),
        ("g1", "f3"), ("g8", "f6"), ("f3", "g1"), ("f6", "g8"),
    ]
    for n, (source, target) in enumerate(moves, start=30):
        state = _move(state, source, target, n)
    view = chess.public_state(state)
    assert view["status"] == "completed"
    assert view["result"] == "draw_threefold"
    assert view["winner"] is None


def test_chess_fifty_move_draw():
    state = chess.new_game()
    state["board"] = {"e1": "wK", "e8": "bK", "a1": "wR"}
    state["turn"] = "w"
    state["castling"] = {"wK": False, "wQ": False, "bK": False, "bQ": False}
    state["en_passant"] = None
    state["halfmove_clock"] = 99
    state["position_counts"] = {}
    state = chess._seal(state)

    state = chess.move(
        state,
        source="a1",
        target="a2",
        request_id="chess-fifty-0001",
    )
    assert state["status"] == "completed"
    assert state["result"] == "draw_fifty_move"


def test_chess_insufficient_material_draw():
    state = chess.new_game()
    state["board"] = {"e1": "wK", "e8": "bK", "c1": "wB"}
    state["turn"] = "w"
    state["castling"] = {"wK": False, "wQ": False, "bK": False, "bQ": False}
    state["en_passant"] = None
    state["position_counts"] = {}
    state = chess._seal(state)

    state = chess.move(
        state,
        source="c1",
        target="d2",
        request_id="chess-material-0001",
    )
    assert state["status"] == "completed"
    assert state["result"] == "draw_insufficient_material"
