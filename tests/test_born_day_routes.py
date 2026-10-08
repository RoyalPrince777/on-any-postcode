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

    def test_world_exposes_born_day(self):
        response = self.client.get("/world")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'href="/born-day"', response.data)


if __name__ == "__main__":
    unittest.main()
