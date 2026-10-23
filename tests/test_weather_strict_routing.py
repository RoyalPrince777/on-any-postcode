"""Verify strict weather mode never performs an external weather request."""
import os
import unittest
from unittest.mock import patch
from mission_control import location_intelligence


class StrictWeatherRoutingTests(unittest.TestCase):
    @patch.dict(os.environ, {"OAP_WEATHER_SOURCE_MODE": "strict_oap_owned"})
    @patch.object(location_intelligence, "_json", side_effect=AssertionError("external request attempted"))
    def test_strict_weather_fails_closed_before_network(self, request):
        with self.assertRaisesRegex(location_intelligence.LocationUnavailable, "oap_owned_observation_not_connected"):
            location_intelligence.weather(51.4, -0.2)
        request.assert_not_called()

    @patch.dict(os.environ, {}, clear=True)
    @patch.object(location_intelligence, "_json", side_effect=AssertionError("external request attempted"))
    def test_default_weather_fails_closed_before_network(self, request):
        with self.assertRaises(location_intelligence.LocationUnavailable):
            location_intelligence.weather(51.4, -0.2)
        request.assert_not_called()

    @patch.dict(os.environ, {"OAP_WEATHER_SOURCE_MODE": "strict_oap_owned"})
    def test_status_reports_strict_mode_not_ready(self):
        status = location_intelligence.status()
        self.assertEqual(status["weather_source_mode"], "strict_oap_owned")
        self.assertFalse(status["weather_provider_verified"])
        self.assertFalse(status["strict_oap_owned_observation_ready"])
        self.assertFalse(status["ready"])
        self.assertEqual(status["weather_intelligence"]["source_mode"], "strict_oap_owned")
        self.assertFalse(status["weather_intelligence"]["ready"])
        self.assertFalse(status["weather_intelligence"]["live_observation_verified"])
        self.assertFalse(status["weather_intelligence"]["external_dependency_present"])


if __name__ == "__main__":
    unittest.main()
