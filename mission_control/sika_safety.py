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

    scam_signals = {
        "remote_access_or_screen_share": bool(body.get("remote_access_or_screen_share")),
        "urgent_or_secret_payment": bool(body.get("urgent_or_secret_payment")),
        "impersonation_claim": bool(body.get("impersonation_claim")),
        "safe_account_claim": bool(body.get("safe_account_claim")),
        "investment_or_crypto_pitch": bool(body.get("investment_or_crypto_pitch")),
        "payment_instructions_changed": bool(body.get("payment_instructions_changed")),
        "suspicious_link_or_qr": bool(body.get("suspicious_link_or_qr")),
    }

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

    scam_weights = {
        "remote_access_or_screen_share": 35,
        "urgent_or_secret_payment": 25,
        "impersonation_claim": 35,
        "safe_account_claim": 45,
        "investment_or_crypto_pitch": 30,
        "payment_instructions_changed": 25,
        "suspicious_link_or_qr": 25,
    }
    for signal, active in scam_signals.items():
        if active:
            score += scam_weights[signal]
            reasons.append(signal)

    score = min(score, 100)
    scam_detected = any(scam_signals.values())
    if scam_signals["safe_account_claim"] or (scam_detected and score >= 75):
        decision = "block_software_only"
    elif score >= 60 or scam_detected:
        decision = "review"
    elif score >= 30:
        decision = "step_up"
    else:
        decision = "allow_software_only"

    return {
        "risk_score": score,
        "decision": decision,
        "reasons": reasons,
        "scam_signals": scam_signals,
        "scam_detected": scam_detected,
        "protected_traits_used": False,
        "money_moved": False,
        "regulated_execution_authorised": False,
        "human_review_available": True,
        "recipient_confirmation_required": recipient_new,
        "cool_off_recommended": decision in {"review", "block_software_only"},
        "executable": False,
    }


def security_posture() -> dict[str, Any]:
    return {
        "screen_capture": {
            "web_os_level_block_enforceable": False,
            "browser_capture_claim_allowed": False,
            "visibility_blur_enabled": True,
            "print_block_enabled": True,
            "copy_context_menu_block_enabled": True,
            "display_capture_permission_disabled": True,
            "native_secure_surface_required_for_hard_block": True,
        },
        "session": {
            "authenticated_owner_required": True,
            "idle_timeout_seconds": 300,
            "sensitive_action_reauth_seconds": 120,
            "reauth_required_after_timeout": True,
            "csrf_required_for_mutations": True,
            "private_cache_disabled": True,
            "sensitive_autocomplete_disabled": True,
            "hide_on_background": True,
        },
        "fraud_and_scam": {
            "amount_velocity_checks": True,
            "new_device_location_recipient_checks": True,
            "remote_access_screen_share_signal": True,
            "urgency_secret_payment_signal": True,
            "impersonation_signal": True,
            "safe_account_signal": True,
            "investment_crypto_signal": True,
            "changed_payment_instruction_signal": True,
            "suspicious_link_qr_signal": True,
            "human_review_available": True,
            "beneficiary_cooling_off": True,
            "software_transfer_limits": True,
            "suspicious_device_recovery": True,
            "regulated_execution_authorised": False,
        },
        "founder_auth_touched": False,
        "money_execution_enabled": False,
    }



def payment_controls(payload: dict[str, Any] | None) -> dict[str, Any]:
    body = payload or {}
    amount = _bounded(body.get("amount_sika", "0"), "amount_sika")
    daily_used = _bounded(body.get("daily_used_sika", "0"), "daily_used_sika")
    daily_limit = _bounded(body.get("daily_limit_sika", "1000"), "daily_limit_sika")
    recipient_age_minutes = int(
        _bounded(body.get("recipient_age_minutes", "0"), "recipient_age_minutes")
    )
    suspicious_device = bool(body.get("suspicious_device"))

    remaining = max(daily_limit - daily_used, Decimal(0))
    over_limit = amount > remaining
    new_recipient_cooling_off = recipient_age_minutes < 30
    step_up_required = (
        over_limit or new_recipient_cooling_off or suspicious_device or amount >= Decimal(500)
    )
    return {
        "daily_limit_sika": f"{daily_limit:.2f}",
        "daily_used_sika": f"{daily_used:.2f}",
        "remaining_sika": f"{remaining:.2f}",
        "over_limit": over_limit,
        "new_recipient_cooling_off": new_recipient_cooling_off,
        "cooling_off_minutes": 30,
        "suspicious_device": suspicious_device,
        "step_up_required": step_up_required,
        "payment_may_progress_to_review": not over_limit and not suspicious_device,
        "money_moved": False,
        "executable": False,
    }


def session_policy() -> dict[str, Any]:
    return {
        "idle_timeout_seconds": 300,
        "sensitive_action_reauth_seconds": 120,
        "background_immediate_privacy_shield": True,
        "reauth_required_after_timeout": True,
        "founder_auth_touched": False,
        "money_execution_enabled": False,
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
