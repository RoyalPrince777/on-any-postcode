"""Strict OAP-owned weather observation admission gate.

This module does not fetch external data, discover sensors or assert live readiness.
Only locally authenticated, explicitly registered OAP-owned station readings
can pass. The caller must authenticate transport and provide a trusted registry;
untrusted payload fields cannot establish ownership or authentication.
"""
from __future__ import annotations

import math
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

MAX_AGE_SECONDS = 300
RANGES = {"temperature_c": (-80.0, 60.0), "humidity_pct": (0.0, 100.0),
          "pressure_hpa": (800.0, 1100.0), "wind_speed_mps": (0.0, 120.0),
          "rainfall_mm": (0.0, 500.0)}
REQUIRED = ("temperature_c", "humidity_pct", "pressure_hpa")


def admit_owned_observation(
    payload: Mapping[str, Any], *,
    station_registry: Mapping[str, Mapping[str, Any]],
    authenticated_station_id: str | None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Validate a trusted transport identity against an OAP-owned station registry.

    Fail closed. The authenticated_station_id MUST come from a verified local
    transport/session, not the observation payload. A successful return is
    admission of a reading, not calibration or forecast certification.
    """
    if not authenticated_station_id:
        raise ValueError("station_authentication_required")
    station = station_registry.get(authenticated_station_id)
    if not isinstance(station, Mapping) or station.get("owner") != "OAP" or station.get("enabled") is not True:
        raise ValueError("registered_oap_station_required")
    if payload.get("station_id") != authenticated_station_id:
        raise ValueError("station_identity_mismatch")
    if payload.get("source") != "oap_owned_sensor":
        raise ValueError("external_source_rejected")
    timestamp = payload.get("observed_at")
    if not isinstance(timestamp, str):
        raise TypeError("observation_timestamp_required")
    try:
        observed = datetime.fromisoformat(timestamp)
    except ValueError as exc:
        raise ValueError("invalid_observation_timestamp") from exc
    if observed.tzinfo is None:
        raise ValueError("timezone_required")
    current = now or datetime.now(UTC)
    age = (current - observed).total_seconds()
    if not 0 <= age <= MAX_AGE_SECONDS:
        raise ValueError("stale_or_future_observation")
    readings = payload.get("readings")
    if not isinstance(readings, Mapping) or any(k not in readings for k in REQUIRED):
        raise ValueError("required_measurements_missing")
    validated = {}
    for key, value in readings.items():
        if key not in RANGES:
            raise ValueError("unsupported_measurement")
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError("invalid_measurement")
        lower, upper = RANGES[key]
        if not lower <= value <= upper:
            raise ValueError("measurement_out_of_range")
        validated[key] = float(value)
    return {
        "source_mode": "strict_oap_owned",
        "station_id": authenticated_station_id,
        "observed_at": observed.isoformat(),
        "readings": validated,
        "admitted": True,
        "forecast_ready": False,
        "public_warning_authorized": False,
    }
