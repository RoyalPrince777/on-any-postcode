#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mission_control import location_intelligence

LOCATION = os.getenv("OAP_WEATHER_GREEN_GATE_LOCATION", "CR4 1AB").strip() or "CR4 1AB"
MAX_RECEIPT_AGE_SECONDS = location_intelligence.CACHE_SECONDS


def build_receipt(resolved: dict[str, Any], status: dict[str, Any], *, now: int | None = None) -> dict[str, Any]:
    weather = dict(resolved.get("weather") or {})
    intelligence = dict(weather.get("intelligence") or {})
    earth = dict(weather.get("earth_intelligence") or {})
    received = int(weather.get("source_received_epoch") or 0)
    ttl = int(weather.get("source_ttl_seconds") or 0)
    current = int(time.time()) if now is None else int(now)
    receipt_age = current - received if received else -1
    advisory = str(intelligence.get("advisory_level") or "unavailable").strip().lower()
    observation_time = str(intelligence.get("observation_time") or "").strip()
    provider_id = str(weather.get("provider_id") or "").strip()

    fresh_receipt = (
        received > 0
        and ttl > 0
        and 0 <= receipt_age <= min(ttl, MAX_RECEIPT_AGE_SECONDS)
    )
    advisory_valid = advisory in {"green", "yellow", "amber", "red"}
    live_ready = bool(
        status.get("weather_provider_verified")
        and status.get("postcode_provider_verified")
        and status.get("weather_intelligence_ready")
        and earth.get("live_environment_ready")
        and provider_id == "api.open-meteo.com"
        and observation_time
        and fresh_receipt
        and advisory_valid
    )
    return {
        "event": "oap_weather_bounded_external_probe",
        "location_scope": "explicit_test_postcode",
        "weather_provider_id": provider_id,
        "postcode_provider_verified": bool(status.get("postcode_provider_verified")),
        "weather_provider_verified": bool(status.get("weather_provider_verified")),
        "weather_intelligence_ready": bool(status.get("weather_intelligence_ready")),
        "earth_live_environment_ready": bool(earth.get("live_environment_ready")),
        "observation_time_present": bool(observation_time),
        "advisory_level": advisory,
        "source_receipt_age_seconds": receipt_age,
        "source_ttl_seconds": ttl,
        "fresh_receipt": fresh_receipt,
        "live_path_proven": live_ready,
        "first_party_intelligence": True,
        "first_party_observation_network": bool(
            status.get("weather_intelligence_first_party_ready")
        ),
        "external_observation_bootstrap": True,
        "precise_location_persisted": False,
        "silent_location_tracking": False,
        "execution_granted": False,
    }


def main() -> None:
    try:
        resolved = location_intelligence.lookup_with_weather(LOCATION)
        status = location_intelligence.status()
        receipt = build_receipt(resolved, status)
    except (ValueError, location_intelligence.LocationUnavailable) as exc:
        receipt = {
            "event": "oap_weather_bounded_external_probe",
            "location_scope": "explicit_test_postcode",
            "live_path_proven": False,
            "failure_type": type(exc).__name__,
            "first_party_intelligence": True,
            "first_party_observation_network": False,
            "external_observation_bootstrap": True,
            "precise_location_persisted": False,
            "silent_location_tracking": False,
            "execution_granted": False,
        }
        print(json.dumps(receipt, sort_keys=True))
        raise SystemExit("live weather probe failed closed") from exc

    print(json.dumps(receipt, sort_keys=True))
    if not receipt["live_path_proven"]:
        raise SystemExit("live weather probe did not satisfy Truth Mode gates")


if __name__ == "__main__":
    main()
