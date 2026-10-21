"""Founder-only Earth observation intake; no external sources, network or execution."""
from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from hashlib import sha256
import json
import math
import re
from typing import Any

from mission_control import world_observation

POLICY = {
    "observation_sources": "oap_owned_sensors_only",
    "external_observations_allowed": False,
    "hardware": "oap_designed_commercial_components",
    "infrastructure": "oap_owned_physical_servers_first",
    "third_party_hosted_storage_allowed": False,
    "network_collection_enabled": False,
    "execution_granted": False,
}
UNITS = {"temperature": "celsius", "humidity": "percent", "pressure": "hpa", "air_quality_pm25": "ug_m3"}
BOUNDS = {"temperature": (-90.0, 65.0), "humidity": (0.0, 100.0),
          "pressure": (300.0, 1100.0), "air_quality_pm25": (0.0, 10000.0)}
NODE_ID = re.compile(r"^oap-[a-z0-9-]{3,60}$")
DIGEST = re.compile(r"^[0-9a-f]{64}$")


def intake(reading: Mapping[str, Any], *, now: datetime | None = None) -> dict[str, Any]:
    """Validate an OAP-owned sensor reading without claiming authenticity.

    Enrollment, signatures, calibration, physical server storage and sensor
    transport must be independently proven before observations become trusted.
    """
    if not isinstance(reading, Mapping):
        raise ValueError("reading_must_be_object")
    if reading.get("source_ownership") != "oap_owned":
        raise ValueError("external_observations_forbidden")
    node = reading.get("node_id")
    if not isinstance(node, str) or not NODE_ID.fullmatch(node):
        raise ValueError("invalid_oap_node_id")
    metric = reading.get("measurement")
    if metric not in UNITS or reading.get("unit") != UNITS[metric]:
        raise ValueError("unsupported_measurement_or_unit")
    value = reading.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("invalid_value")
    lower, upper = BOUNDS[metric]
    if not lower <= value <= upper:
        raise ValueError("out_of_range")
    observed = reading.get("observed_at")
    received = reading.get("received_at")
    if not isinstance(observed, str) or not isinstance(received, str):
        raise ValueError("timestamps_required")
    for timestamp in (observed, received):
        try:
            parsed = datetime.fromisoformat(timestamp)
        except ValueError as exc:
            raise ValueError("invalid_timestamp") from exc
        if parsed.tzinfo is None:
            raise ValueError("timezone_required")
    receipt = world_observation.normalise({
        "object_id": node,
        "object_type": "oap_earth_sensor_reading",
        "source": node,
        "source_ownership": "oap_owned",
        "evidence_class": "unverified",
        "observed_at": observed,
        "received_at": received,
        "first_party": {"software": True, "processing": True, "observation": False, "storage": False},
    }, now=now)
    payload = {key: reading[key] for key in
               ("node_id", "measurement", "unit", "value", "observed_at", "received_at")}
    fingerprint = sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"),
                                   allow_nan=False).encode()).hexdigest()
    return {
        **receipt,
        "measurement": metric,
        "value": float(value),
        "unit": UNITS[metric],
        "reading_fingerprint_sha256": fingerprint,
        "node_enrollment_verified": False,
        "signature_verified": False,
        "calibration_verified": False,
        "physical_server_storage_verified": False,
        "ready_for_trusted_analysis": False,
        "live_claim_allowed": False,
    }


def status() -> dict[str, Any]:
    return {**POLICY, "sensor_nodes_verified": 0, "physical_servers_verified": 0,
            "first_party_observation_runtime_ready": False}
