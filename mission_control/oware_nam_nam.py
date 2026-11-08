"""Nam-Nam relay sowing and territory rules for OAP Arena."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Position:
    pits: tuple[int, ...]
    scores: tuple[int, int]
    turn: int = 0
    territory: int = 6
    round_number: int = 1
    result: str | None = None
    last_round: tuple[int, int] | None = None


def owners(territory):
    return tuple(
        [0] * min(territory, 6) + [1] * max(6 - territory, 0)
        + [1] * min(12 - territory, 6) + [0] * max(territory - 6, 0)
    )


def _relay(position, start, ownership):
    pits = list(position.pits)
    scores = list(position.scores)
    cursor = start
    seen = set()

    # A digital turn must finish even if a relay repeats or runs unusually long.
    for _ in range(256):
        checkpoint = (tuple(pits), cursor)
        if checkpoint in seen:
            return None
        seen.add(checkpoint)
        hand, pits[cursor] = pits[cursor], 0
        for remaining in range(hand - 1, -1, -1):
            cursor = (cursor + 1) % 12
            pits[cursor] += 1
            if pits[cursor] != 4:
                continue
            captor = ownership[cursor] if remaining else position.turn
            scores[captor] += 4
            pits[cursor] = 0
            if sum(scores) == 44:
                scores[captor] += 4
                return (0,) * 12, tuple(scores)
        if pits[cursor] <= 1:
            return tuple(pits), tuple(scores)
    return None


def options(position):
    if position.result:
        return {}
    ownership = owners(position.territory)
    opponent = 1 - position.turn
    must_feed = not any(seeds for seeds, owner in zip(position.pits, ownership) if owner == opponent)
    moves = {}
    for pit, (seeds, owner) in enumerate(zip(position.pits, ownership)):
        if not seeds or owner != position.turn:
            continue
        outcome = _relay(position, pit, ownership)
        if must_feed and (
            outcome is None or (
                sum(outcome[1]) < 48
                and not any(count for count, seat in zip(outcome[0], ownership) if seat == opponent)
            )
        ):
            continue
        moves[pit] = outcome
    return moves


def _next_round(position, territory, last_round=None):
    return Position(
        pits=(4,) * 12,
        scores=(0, 0),
        territory=territory,
        turn=position.round_number % 2,
        round_number=position.round_number + 1,
        last_round=last_round,
    )


def replay_round(position):
    return _next_round(position, position.territory)


def play(position, outcome):
    if outcome is None:
        return replay_round(position)
    pits, scores = outcome
    following = Position(pits, scores, 1 - position.turn, position.territory, position.round_number)
    if sum(scores) < 48:
        if options(following):
            return following
        ownership = owners(position.territory)
        # A player whose territory is empty passes to the player who can feed it.
        if not any(count for count, owner in zip(pits, ownership) if owner == following.turn):
            feeding = Position(pits, scores, position.turn, position.territory, position.round_number)
            if options(feeding):
                return feeding
        scores = tuple(
            scores[seat] + sum(count for count, owner in zip(pits, ownership) if owner == seat)
            for seat in (0, 1)
        )

    territory = scores[0] // 4
    if territory in (0, 12):
        return Position((0,) * 12, scores, position.turn, territory, position.round_number, "territory", scores)
    return _next_round(position, territory, scores)


def agent_value(position, depth):
    if position.result:
        return 1000 if position.territory == 0 else -1000
    value = 8 * (6 - position.territory) + position.scores[1] - position.scores[0]
    if not depth:
        return value
    values = [agent_value(play(position, outcome), depth - 1) for outcome in options(position).values()]
    if not values:
        return value
    return max(values) if position.turn == 1 else min(values)
