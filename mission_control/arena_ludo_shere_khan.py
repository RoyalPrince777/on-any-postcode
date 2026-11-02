"""Bounded Shere Khan Ludo move selection on the existing server-authoritative game.

Only chooses a legal piece. The game engine performs rolls, captures and turn changes.
"""
from __future__ import annotations

from mission_control import ludo

LEVEL_NAMES = {
    "cub": "Tiger Cub",
    "roar": "Royal Roar",
    "tyrant": "Jungle Tyrant",
}


def choose_shere_khan_piece(state: dict, level: str = "cub") -> str:
    """Return an existing legal piece id; never mutate the authoritative state."""
    if level not in LEVEL_NAMES:
        raise ValueError("ludo_agent_level_invalid")
    if not ludo.validate(state)["passed"] or state["status"] != "active":
        raise ValueError("ludo_agent_state_invalid")
    rolled = state.get("pending_roll")
    if rolled is None:
        raise ValueError("ludo_agent_roll_required")
    allowed = ludo._movable_piece_ids(state, rolled)
    if not allowed:
        raise ValueError("ludo_agent_no_legal_piece")
    player = state["players"][state["turn_index"]]
    choices = []
    for piece in player["pieces"]:
        if piece["id"] not in allowed:
            continue
        before = piece["progress"]
        after = 0 if before < 0 else before + rolled
        capture = 0
        safe = 0
        if 0 <= after < ludo.TRACK_LENGTH:
            target_square = (player["start_offset"] + after) % ludo.TRACK_LENGTH
            safe = int(target_square in ludo.SAFE_TRACK_SQUARES)
            if not safe:
                for opponent in state["players"]:
                    if opponent["id"] == player["id"]:
                        continue
                    for target in opponent["pieces"]:
                        p = target["progress"]
                        if 0 <= p < ludo.TRACK_LENGTH and (
                            opponent["start_offset"] + p
                        ) % ludo.TRACK_LENGTH == target_square:
                            capture += 1
        finish = int(after == ludo.FINISH_PROGRESS)
        # The three tiers differ only in move priorities, not game rules.
        if level == "cub":
            score = (int(before < 0) * 5) + after * 0.02 + capture * 2
        elif level == "roar":
            score = capture * 25 + finish * 16 + safe * 5 + after * 0.2
        else:
            score = capture * 50 + finish * 60 + safe * 12 + after * 0.4
        choices.append((score, piece["id"]))
    # Stable tie-breaking, no invented randomness or access to hidden information.
    return sorted(choices, key=lambda item: (-item[0], item[1]))[0][1]
