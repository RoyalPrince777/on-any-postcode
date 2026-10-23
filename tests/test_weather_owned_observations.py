"""Negative tests for the strict owned-weather admission boundary."""
import unittest
from datetime import datetime, timezone, timedelta
from mission_control.weather_owned_observations import admit_owned_observation

NOW = datetime(2026, 10, 23, 12, tzinfo=timezone.utc)
REGISTRY = {"oap-station-1": {"owner": "OAP", "enabled": True}}
PAYLOAD = {"station_id": "oap-station-1", "source": "oap_owned_sensor",
           "observed_at": NOW.isoformat(),
           "readings": {"temperature_c": 15, "humidity_pct": 70, "pressure_hpa": 1013}}


class OwnedObservationTests(unittest.TestCase):
    def admit(self, payload=None, **kwargs):
        return admit_owned_observation(
            PAYLOAD if payload is None else payload,
            station_registry=kwargs.get("registry", REGISTRY),
            authenticated_station_id=kwargs.get("identity", "oap-station-1"),
            now=NOW)

    def test_valid_registered_owned_reading(self):
        self.assertTrue(self.admit()["admitted"])
        self.assertFalse(self.admit()["forecast_ready"])

    def test_external_source_rejected(self):
        with self.assertRaises(ValueError):
            self.admit({**PAYLOAD, "source": "api.open-meteo.com"})

    def test_missing_authenticated_identity_rejected(self):
        with self.assertRaises(ValueError):
            self.admit(identity="")

    def test_unregistered_station_rejected(self):
        with self.assertRaises(ValueError):
            self.admit(registry={})

    def test_station_spoof_rejected(self):
        with self.assertRaises(ValueError):
            self.admit({**PAYLOAD, "station_id": "another"})

    def test_stale_reading_rejected(self):
        with self.assertRaises(ValueError):
            self.admit({**PAYLOAD, "observed_at": (NOW-timedelta(minutes=10)).isoformat()})

    def test_future_reading_rejected(self):
        with self.assertRaises(ValueError):
            self.admit({**PAYLOAD, "observed_at": (NOW+timedelta(seconds=1)).isoformat()})

    def test_impossible_measurement_rejected(self):
        with self.assertRaises(ValueError):
            self.admit({**PAYLOAD, "readings": {**PAYLOAD["readings"], "humidity_pct": 150}})

    def test_missing_measurement_rejected(self):
        with self.assertRaises(ValueError):
            self.admit({**PAYLOAD, "readings": {"temperature_c": 15}})


if __name__ == "__main__":
    unittest.main()
