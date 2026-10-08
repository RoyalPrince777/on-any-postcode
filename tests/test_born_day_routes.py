"""Born Day route integration smoke checks; no game engine duplication."""
import unittest

from app import app


class BornDayRouteTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_public_routes_render(self):
        for route in ("/born-day", "/world/born-day"):
            with self.subTest(route=route):
                response = self.client.get(route)
                self.assertEqual(response.status_code, 200)
                self.assertIn(b"Oware Abapa", response.data)
                self.assertIn(b"/born-day/play/oware", response.data)
                self.assertIn(b"/born-day/play/ludo", response.data)
                self.assertIn(b"/born-day/play/connect4", response.data)
                self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_shared_arena_games_have_return_navigation(self):
        for game in ("oware", "ludo", "connect4"):
            with self.subTest(game=game):
                response = self.client.get("/born-day/play/" + game)
                self.assertEqual(response.status_code, 200)
                self.assertIn(b'aria-label="Born Day navigation"', response.data)
                self.assertIn(b'href="/born-day"', response.data)
                self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_unknown_shared_game_is_not_found(self):
        self.assertEqual(self.client.get("/born-day/play/unknown").status_code, 404)

    def test_reaction_rush_is_linked_and_renders(self):
        hub = self.client.get("/born-day")
        self.assertIn(b'href="/born-day/reaction-rush"', hub.data)
        game = self.client.get("/born-day/reaction-rush")
        self.assertEqual(game.status_code, 200)
        self.assertIn(b"Reaction Rush", game.data)
        self.assertIn(b"born_day_reaction_rush.js", game.data)
        self.assertIn(b"false starts", game.data)
        self.assertIn(b'href="/born-day"', game.data)
        self.assertEqual(game.headers["Cache-Control"], "no-store")

    def test_optional_weekday_celebration(self):
        thursday = self.client.get("/born-day?weekday=Thursday")
        self.assertEqual(thursday.status_code, 200)
        self.assertIn(b"Yawoada", thursday.data)
        self.assertIn(b"Happy Thursday", thursday.data)
        invalid = self.client.get("/born-day?weekday=Invalid")
        self.assertEqual(invalid.status_code, 200)
        self.assertNotIn(b"Happy Invalid", invalid.data)

    def test_reaction_rush_javascript_is_first_party(self):
        response = self.client.get("/static/born_day_reaction_rush.js")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"performance.now()", response.data)
        self.assertIn(b"False start", response.data)

    def test_leaderboards_are_visible_but_not_fabricated(self):
        hub = self.client.get("/born-day")
        self.assertIn(b'href="/born-day/leaderboards"', hub.data)
        board = self.client.get("/born-day/leaderboards")
        self.assertEqual(board.status_code, 200)
        self.assertIn(b"Official rankings are not available yet", board.data)
        self.assertIn(b"No verified Arena results ledger", board.data)
        self.assertEqual(board.headers["Cache-Control"], "no-store")

    def test_world_exposes_born_day(self):
        response = self.client.get("/world")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'href="/born-day"', response.data)


if __name__ == "__main__":
    unittest.main()
