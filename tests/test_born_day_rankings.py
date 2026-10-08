"""Born Day rankings reject fabricated results and keep games separate."""
import unittest

from mission_control.born_day_rankings import calculate_leaderboard


def result(ident, player, game="oware", outcome="win"):
    return {"result_id": ident, "player_id": player, "game": game,
            "verification": "server_verified", "outcome": outcome}


class BornDayRankingTests(unittest.TestCase):
    def test_win_draw_loss_order(self):
        rows = calculate_leaderboard([
            result("a", "one"), result("b", "one", outcome="loss"),
            result("c", "two", outcome="draw"), result("d", "two", outcome="loss"),
        ], "oware")
        self.assertEqual([row["player_id"] for row in rows], ["one", "two"])
        self.assertEqual(rows[0]["losses"], 1)

    def test_other_games_do_not_mix(self):
        rows = calculate_leaderboard([result("a", "one"), result("b", "two", "ludo")], "oware")
        self.assertEqual(len(rows), 1)

    def test_unverified_and_duplicates_blocked(self):
        bad = result("a", "one")
        bad["verification"] = "client_claimed"
        with self.assertRaises(ValueError):
            calculate_leaderboard([bad], "oware")
        good = result("a", "one")
        with self.assertRaises(ValueError):
            calculate_leaderboard([good, good], "oware")

    def test_reaction_rush_requires_verified_time(self):
        fast = {"result_id": "r1", "player_id": "fast", "game": "reaction-rush",
                "verification": "server_verified", "reaction_ms": 190, "false_start": False}
        slow = {**fast, "result_id": "r2", "player_id": "slow", "reaction_ms": 260}
        rows = calculate_leaderboard([slow, fast], "reaction-rush")
        self.assertEqual(rows[0]["player_id"], "fast")
        invalid = {**fast, "false_start": True}
        with self.assertRaises(ValueError):
            calculate_leaderboard([invalid], "reaction-rush")


if __name__ == "__main__":
    unittest.main()
