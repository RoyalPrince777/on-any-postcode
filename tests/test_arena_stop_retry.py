"""Regression: a retried STOP returns its original sealed terminal checkpoint.

A new request after STOP must still be rejected; retries must not append receipts.
"""
import pytest

from mission_control import chess, dot, ludo


@pytest.mark.parametrize(
    "engine,initial",
    [
        (ludo, lambda: ludo.new_game(["Alpha", "Bravo"])),
        (chess, chess.new_game),
        (dot, dot.new_game),
    ],
    ids=["ludo", "chess", "dot"],
)
def test_stop_retry_is_idempotent_but_new_stop_is_denied(engine, initial):
    game = initial()
    request_id = "stop-once-0001"
    stopped = engine.stop(game, request_id=request_id)
    assert stopped["status"] == "stopped"
    assert engine.validate(stopped)["passed"]
    assert stopped["request_receipts"][-1]["request_id"] == request_id
    assert stopped["request_receipts"][-1]["action"] == "stop"

    retried = engine.stop(stopped, request_id=request_id)
    assert retried == stopped
    assert len(retried["request_receipts"]) == 1

    with pytest.raises(ValueError, match="stop_denied"):
        engine.stop(stopped, request_id="different-stop-0002")
