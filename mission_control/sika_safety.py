"""SIKA safety and fraud intelligence.

First-party, non-executing risk assessment for software acceptance. It never
authorises regulated money movement and it never consumes protected traits.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any


class FraudInputError(ValueError):
    pass


def _bounded(value: object, name: str) -> Decimal:
    try:
        number = Decimal(str(value))
    except Exception as exc:
        raise FraudInputError(f"invalid_{name}") from exc
    if number < 0:
        raise FraudInputError(f"{name}_must_not_be_negative")
    return number


def assess(payload: dict[str, Any] | None) -> dict[str, Any]:
    body = payload or {}
    amount = _bounded(body.get("amount_sika", "0"), "amount_sika")
    attempts = int(_bounded(body.get("recent_attempts", "0"), "recent_attempts"))
    new_device = bool(body.get("new_device"))
    unusual_location = bool(body.get("unusual_location"))
    recipient_new = bool(body.get("new_recipient"))
    velocity = int(_bounded(body.get("transactions_10m", "0"), "transactions_10m"))

    score = 0
    reasons: list[str] = []
    if amount >= Decimal(1000):
        score += 30
        reasons.append("high_amount")
    if attempts >= 5:
        score += 25
        reasons.append("repeated_attempts")
    if velocity >= 6:
        score += 25
        reasons.append("high_velocity")
    if new_device:
        score += 10
        reasons.append("new_device")
    if unusual_location:
        score += 10
        reasons.append("unusual_location")
    if recipient_new:
        score += 5
        reasons.append("new_recipient")

    score = min(score, 100)
    if score >= 60:
        decision = "review"
    elif score >= 30:
        decision = "step_up"
    else:
        decision = "allow_software_only"

    return {
        "risk_score": score,
        "decision": decision,
        "reasons": reasons,
        "protected_traits_used": False,
        "money_moved": False,
        "regulated_execution_authorised": False,
        "human_review_available": True,
        "executable": False,
    }


def install_readiness() -> dict[str, Any]:
    return {
        "web_identity": True,
        "csrf": True,
        "rate_limits": True,
        "no_store_private_responses": True,
        "csp_hsts_permissions_policy": True,
        "owner_scope": True,
        "tamper_detection": True,
        "hash_chained_audit": True,
        "fraud_preflight": True,
        "regulated_execution_fail_closed": True,
        "pwa_manifest_on_oap_os": True,
        "pwa_manifest_ready": True,
        "pwa_service_worker_ready": True,
        "pwa_sika_shortcut_ready": True,
        "pwa_private_cache_isolation": True,
        "public_pwa_software_ready": True,
        "real_android_pwa_acceptance": False,
        "sika_specific_signed_android_package": False,
        "real_native_android_install_acceptance": False,
        "native_device_recovery_acceptance": False,
        "safe_public_install_ready": False,
        "native_android_package_ready": False,
        "private_software_acceptance_ready": True,
    }
