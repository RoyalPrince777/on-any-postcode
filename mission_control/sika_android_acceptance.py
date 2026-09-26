"""SIKA Android acceptance evidence contract.

Collects real physical-device evidence for PWA install/update/recovery and
private-cache isolation. It does not self-certify a device or fabricate an APK.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AndroidAcceptanceEvidence:
    device_label: str | None = None
    install_completed: bool = False
    launched_from_home_screen: bool = False
    update_observed: bool = False
    recovery_after_offline_or_restart: bool = False
    private_routes_not_cached: bool = False
    service_worker_active: bool = False
    manifest_identity_matches: bool = False
    user_confirmed: bool = False
    evidence_ref: str | None = None


def evaluate(evidence: AndroidAcceptanceEvidence | None = None) -> dict[str, Any]:
    item = evidence or AndroidAcceptanceEvidence()
    checks = {
        "install_completed": item.install_completed,
        "launched_from_home_screen": item.launched_from_home_screen,
        "update_observed": item.update_observed,
        "recovery_after_offline_or_restart": item.recovery_after_offline_or_restart,
        "private_routes_not_cached": item.private_routes_not_cached,
        "service_worker_active": item.service_worker_active,
        "manifest_identity_matches": item.manifest_identity_matches,
        "user_confirmed": item.user_confirmed,
        "evidence_ref_present": bool(item.evidence_ref),
    }
    accepted = all(checks.values())
    return {
        "device_label": item.device_label,
        "checks": checks,
        "real_android_pwa_acceptance": accepted,
        "native_android_package_ready": False,
        "signed_native_sika_apk": False,
        "native_update_recovery_acceptance": False,
        "public_install_release_gate": accepted,
        "reason": "physical_android_pwa_acceptance_complete" if accepted else "physical_android_evidence_required",
    }
