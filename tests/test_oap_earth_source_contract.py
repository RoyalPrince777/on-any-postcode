"""Static regression checks for the opt-in OAP Earth slice.

These tests verify source contracts only, not a live Flask server, WebGL GPU,
mobile device, or production runtime.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ROUTES = ROOT / "mission_control" / "on_any_place_routes.py"
EARTH = ROOT / "mission_control" / "templates" / "oap_earth.html"
MAP = ROOT / "mission_control" / "templates" / "local_map.html"


class OAPEarthSourceContract(unittest.TestCase):
    def test_opt_in_route(self):
        source = ROUTES.read_text(encoding="utf-8")
        self.assertIn("@bp.get('/oap-earth')", source)
        self.assertIn("render_template('oap_earth.html')", source)

    def test_existing_navigation_remains(self):
        source = MAP.read_text(encoding="utf-8")
        self.assertIn('id="roads-svg"', source)
        self.assertIn('id="route-svg"', source)
        self.assertIn("oap_map_navigation.css", source)

    def test_webgl_fallback_and_motion_controls(self):
        source = EARTH.read_text(encoding="utf-8")
        for required in (
            "getContext('webgl'",
            "prefers-reduced-motion: reduce",
            "webglcontextlost",
            'id="fallback"',
            'href="/oap-map"',
            'id="toggle"',
        ):
            with self.subTest(required=required):
                self.assertIn(required, source)

    def test_no_external_feed_or_geolocation_dependency(self):
        source = EARTH.read_text(encoding="utf-8")
        for prohibited in (
            "navigator.geolocation",
            "getCurrentPosition(",
            "watchPosition(",
            "fetch(",
            "XMLHttpRequest",
            "<script src=",
            "<iframe",
        ):
            with self.subTest(prohibited=prohibited):
                self.assertNotIn(prohibited, source)


if __name__ == "__main__":
    unittest.main()
