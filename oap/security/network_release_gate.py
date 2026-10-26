"""Fail-closed admission checks for proposed OAP network-security releases.

This is a release decision helper, NOT a VPN, packet firewall or certification.
It deliberately cannot accept simple booleans as evidence of deployment.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

REQUIRED_PROOF: Mapping[str, tuple[str, ...]] = {
    "oap.vpn": (
        "signed_android_build",
        "device_tunnel_test",
        "dns_ipv4_ipv6_leak_test",
        "reconnect_kill_switch_test",
        "independent_security_review",
        "founder_final",
    ),
    "oap.cyber-security": (
        "enforcement_integration_test",
        "allow_deny_regression_test",
        "fail_closed_recovery_test",
        "independent_security_review",
        "founder_final",
    ),
}


@dataclass(frozen=True)
class NetworkReleaseDecision:
    app_id: str
    admitted: bool
    missing: tuple[str, ...]
    reason: str


def evaluate_network_release(
    app_id: str, evidence: Mapping[str, str] | None = None
) -> NetworkReleaseDecision:
    """Review evidence references; never enable/install a service.

    A non-empty reference is only a *submission*, not independent proof.
    Therefore this function always denies operational admission; an
    independent verifier and authoritative Founder Final check are required
    before any future integration may support an allow decision.
    """
    if app_id not in REQUIRED_PROOF:
        return NetworkReleaseDecision(app_id, False, (), "unknown_app_fail_closed")
    submitted = evidence or {}
    missing = tuple(
        key for key in REQUIRED_PROOF[app_id]
        if not isinstance(submitted.get(key), str) or not submitted[key].strip()
    )
    return NetworkReleaseDecision(
        app_id, False, missing,
        "missing_evidence" if missing else "independent_verification_required",
    )
