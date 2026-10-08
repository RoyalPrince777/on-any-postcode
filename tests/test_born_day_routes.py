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
                self.assertIn(b"/arena/oware", response.data)
                self.assertIn(b"/arena/ludo", response.data)
                self.assertIn(b"/arena/connect4", response.data)
                self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_reaction_rush_is_linked_and_renders(self):
        hub = self.client.get("/born-day")
        self.assertIn(b'href="/born-day/reaction-rush"', hub.data)
        game = self.client.get("/born-day/reaction-rush")
        self.assertEqual(game.status_code, 200)
        self.assertIn(b"Reaction Rush", game.data)
        self.assertIn(b"performance.now()", game.data)
        self.assertIn(b"False start", game.data)
        self.assertIn(b'href="/born-day"', game.data)
        self.assertEqual(game.headers["Cache-Control"], "no-store")

    def test_world_exposes_born_day(self):
        response = self.client.get("/world")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'href="/born-day"', response.data)


if __name__ == "__main__":
    unittest.main()
