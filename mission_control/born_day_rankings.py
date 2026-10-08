"""Born Day ranking truth: accept only server-verified Arena outcomes.

No client-supplied score or reaction time becomes an official result.
Pure calculation functions; persistence and signed result ingestion remain gated.
"""
from collections import defaultdict

SUPPORTED_GAMES = frozenset({"oware", "ludo", "connect4", "reaction-rush"})
COMPETITIVE_GAMES = frozenset({"oware", "ludo", "connect4"})


def validated_result(record):
    """Validate a trusted, server-created result before it enters rankings."""
    if not isinstance(record, dict):
        raise ValueError("Invalid result")
    if record.get("game") not in SUPPORTED_GAMES:
        raise ValueError("Unsupported game")
    if record.get("verification") != "server_verified":
        raise ValueError("Unverified result")
    if not isinstance(record.get("result_id"), str) or not record["result_id"]:
        raise ValueError("Missing result ID")
    if not isinstance(record.get("player_id"), str) or not record["player_id"]:
        raise ValueError("Missing player ID")
    if record["game"] in COMPETITIVE_GAMES:
        if record.get("outcome") not in {"win", "loss", "draw"}:
            raise ValueError("Invalid outcome")
    else:
        duration = record.get("reaction_ms")
        if isinstance(duration, bool) or not isinstance(duration, int) or not 80 <= duration <= 2000:
            raise ValueError("Invalid reaction time")
        if record.get("false_start") is not False:
            raise ValueError("False starts are ineligible")
    return record


def calculate_leaderboard(records, game):
    """Deterministic per-game leaderboard from trusted results, never mixed games."""
    if game not in SUPPORTED_GAMES:
        raise ValueError("Unsupported game")
    seen = set()
    scores = defaultdict(lambda: {"wins": 0, "draws": 0, "losses": 0, "games": 0, "best_ms": None})
    for candidate in records:
        record = validated_result(candidate)
        if record["result_id"] in seen:
            raise ValueError("Duplicate result ID")
        seen.add(record["result_id"])
        if record["game"] != game:
            continue
        row = scores[record["player_id"]]
        row["games"] += 1
        if game == "reaction-rush":
            ms = record["reaction_ms"]
            row["best_ms"] = ms if row["best_ms"] is None else min(row["best_ms"], ms)
        else:
            row[{"win": "wins", "loss": "losses", "draw": "draws"}[record["outcome"]]] += 1
    result = [{"player_id": player_id, **row} for player_id, row in scores.items()]
    if game == "reaction-rush":
        result.sort(key=lambda row: (row["best_ms"], row["player_id"]))
    else:
        result.sort(key=lambda row: (-row["wins"], -row["draws"], row["losses"], row["player_id"]))
    return [{"rank": index, **row} for index, row in enumerate(result, 1)]
