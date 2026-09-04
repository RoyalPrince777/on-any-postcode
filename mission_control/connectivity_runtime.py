"""Production connectivity runtime evidence for Technology Intelligence.

This module never simulates connectivity success. It observes the local host runtime
and optionally verifies a fresh, locally signed radio attestation. It does not
control radios, provision eSIMs, change network configuration, or claim a 6G
production network without standards and runtime proof.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import socket
import time
from pathlib import Path
from typing import Any

EVIDENCE_PATH_ENV = "OAP_6G_EVIDENCE_PATH"
EVIDENCE_KEY_ENV = "OAP_6G_EVIDENCE_HMAC_KEY"
MAX_EVIDENCE_AGE_SECONDS = 300
MAX_FUTURE_CLOCK_SKEW_SECONDS = 30

# Verified against the ITU IMT-2030 programme on 2026-09-04. Candidate radio
# interface technologies are still in the standardisation/evaluation process;
# final IMT-2030 technology standards are targeted for the end of the decade.
IMT_2030_STANDARD_FINALIZED = False
IMT_2030_STATUS_VERIFIED_DATE = "2026-09-04"
IMT_2030_TARGET_STANDARD_YEAR = 2030


def _host_interfaces() -> tuple[str, ...]:
    try:
        return tuple(name for _, name in socket.if_nameindex())
    except OSError:
        return ()


def _linux_default_route_present() -> bool:
    route_file = Path("/proc/net/route")
    try:
        lines = route_file.read_text(encoding="utf-8").splitlines()
    except OSError:
        return False
    for line in lines[1:]:
        fields = line.split()
        if len(fields) < 4 or fields[1] != "00000000":
            continue
        try:
            flags = int(fields[3], 16)
        except ValueError:
            continue
        if flags & 0x2:
            return True
    return False


def probe_host_connectivity() -> dict[str, Any]:
    """Observe real local runtime connectivity without external network calls."""

    interfaces = _host_interfaces()
    non_loopback = tuple(name for name in interfaces if name.casefold() not in {"lo", "lo0"})
    default_route_present = _linux_default_route_present()
    return {
        "observed_at_unix": int(time.time()),
        "interface_count": len(interfaces),
        "non_loopback_interface_count": len(non_loopback),
        "default_route_present": default_route_present,
        "live_runtime_probe": True,
        "runtime_connectivity_present": bool(non_loopback) and default_route_present,
        "external_probe_used": False,
    }


def _canonical_payload(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _radio_attestation_status(
    *,
    evidence_path: str | None = None,
    evidence_key: str | None = None,
    now: float | None = None,
) -> dict[str, Any]:
    path_value = evidence_path if evidence_path is not None else os.getenv(EVIDENCE_PATH_ENV, "")
    key_value = evidence_key if evidence_key is not None else os.getenv(EVIDENCE_KEY_ENV, "")
    base: dict[str, Any] = {
        "configured": bool(path_value and key_value),
        "signature_valid": False,
        "fresh": False,
        "radio_connected": False,
        "radio_class": None,
        "authorized_radio_environment": False,
        "testbed_ready": False,
        "production_network_attested": False,
        "valid": False,
        "reason": "radio evidence not configured",
    }
    if not path_value or not key_value:
        return base

    try:
        document = json.loads(Path(path_value).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {**base, "reason": "radio evidence unreadable"}

    payload = document.get("payload")
    signature = document.get("signature")
    if not isinstance(payload, dict) or not isinstance(signature, str):
        return {**base, "reason": "radio evidence malformed"}

    expected_signature = hmac.new(
        key_value.encode("utf-8"),
        _canonical_payload(payload),
        hashlib.sha256,
    ).hexdigest()
    signature_valid = hmac.compare_digest(expected_signature, signature)

    observed_at = payload.get("observed_at_unix")
    try:
        observed_at_float = float(observed_at)
    except (TypeError, ValueError):
        observed_at_float = 0.0
    current = float(time.time() if now is None else now)
    age_seconds = current - observed_at_float
    fresh = -MAX_FUTURE_CLOCK_SKEW_SECONDS <= age_seconds <= MAX_EVIDENCE_AGE_SECONDS

    radio_class = str(payload.get("radio_class") or "").strip().casefold()
    allowed_classes = {
        "imt-2030-experimental",
        "6g-prestandard-testbed",
        "6g-standard",
    }
    radio_connected = all(
        payload.get(field) is True
        for field in ("ran_connected", "core_connected", "device_connected")
    )
    authorized_radio_environment = payload.get("authorized_radio_environment") is True
    production_network_attested = payload.get("production_network") is True
    collector_present = bool(str(payload.get("collector_id") or "").strip())

    evidence_valid = (
        signature_valid
        and fresh
        and radio_class in allowed_classes
        and radio_connected
        and authorized_radio_environment
        and collector_present
    )
    testbed_ready = evidence_valid and radio_class in {
        "imt-2030-experimental",
        "6g-prestandard-testbed",
    }
    reason = "radio evidence verified" if evidence_valid else "radio evidence failed verification"
    return {
        **base,
        "configured": True,
        "signature_valid": signature_valid,
        "fresh": fresh,
        "radio_connected": radio_connected,
        "radio_class": radio_class or None,
        "authorized_radio_environment": authorized_radio_environment,
        "testbed_ready": testbed_ready,
        "production_network_attested": production_network_attested,
        "valid": evidence_valid,
        "reason": reason,
    }


def connectivity_runtime_status() -> dict[str, Any]:
    """Return production runtime readiness with fail-closed 6G truth boundaries."""

    host = probe_host_connectivity()
    radio = _radio_attestation_status()
    production_software_ready = bool(host["runtime_connectivity_present"])
    production_6g_ready = bool(
        radio["valid"]
        and radio["radio_class"] == "6g-standard"
        and radio["production_network_attested"]
        and IMT_2030_STANDARD_FINALIZED
    )
    return {
        "mode": "production",
        "demo_mode": False,
        "simulation_success_allowed": False,
        "production_software_ready": production_software_ready,
        "host": host,
        "radio_evidence": radio,
        "6g_intelligence_runtime_ready": production_software_ready,
        "6g_testbed_ready": bool(radio["testbed_ready"]),
        "6g_production_network_ready": production_6g_ready,
        "imt_2030_standard_finalized": IMT_2030_STANDARD_FINALIZED,
        "imt_2030_status_verified_date": IMT_2030_STATUS_VERIFIED_DATE,
        "imt_2030_target_standard_year": IMT_2030_TARGET_STANDARD_YEAR,
        "network_execution_authority": False,
        "human_authority_final": True,
    }
