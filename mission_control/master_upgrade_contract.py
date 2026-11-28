"""Master upgrade contract for real-green platform readiness.

This contract prevents static extras from being counted as completion. A feature
is only real green when it works end-to-end, is install-ready, is proof-backed,
and keeps all safety locks intact.
"""
from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


PRIVATE_ORIGIN_PORT = "5000"
PRIVATE_ORIGIN_PATH = "/mission/smi"
RELEASE_EVIDENCE_REQUIREMENTS = (
    "exact_candidate_digest",
    "actual_target_runtime_proof",
    "independent_guardian_review",
    "durable_hrm_readback",
    "exact_version_green_gate",
    "rollback_verified",
    "founder_final",
)


def private_origin_allowed(server_port: object) -> bool:
    """Use the WSGI listener port, never a client Host or forwarded-port header."""
    return server_port == PRIVATE_ORIGIN_PORT


def release_hrm_review(product: str, digest: str) -> dict[str, object]:
    """Read an exact-build HRM receipt; this is diagnostic, never approval."""
    from . import hrm_durable_receipt

    result = {"receipt_found": False, "readback_verified": False,
              "fresh": False, "publication_authorized": False,
              "reason": "exact_release_receipt_required"}
    if not isinstance(product, str) or not re.fullmatch(r"[a-z0-9-]{1,64}", product):
        return {**result, "reason": "invalid_product"}
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        return {**result, "reason": "invalid_candidate_digest"}
    signal = f"release:{product}:{digest}"
    try:
        receipt = hrm_durable_receipt.latest_receipt_status(signal)
    except Exception:  # noqa: BLE001 - evidence unavailable must fail closed.
        return {**result, "reason": "receipt_store_unavailable"}
    if not isinstance(receipt, dict) or receipt.get("found") is not True:
        return result
    result["receipt_found"] = True
    if receipt.get("read_back_verified") is not True:
        return {**result, "reason": "receipt_readback_failed"}
    result["readback_verified"] = True
    if receipt.get("authority_transferred") is not False:
        return {**result, "reason": "receipt_authority_invalid"}
    try:
        stamp = datetime.fromisoformat(receipt.get("recorded_at", ""))
        if stamp.tzinfo is None or stamp.utcoffset() is None:
            raise ValueError("timezone_required")
        age = datetime.now(UTC) - stamp
    except (TypeError, ValueError, OverflowError):
        return {**result, "reason": "receipt_timestamp_invalid"}
    if not timedelta(0) <= age <= timedelta(hours=24):
        return {**result, "reason": "receipt_stale_or_future"}
    return {**result, "fresh": True,
            "reason": "readback_only_independent_release_proofs_required"}


MASTER_UPGRADE_RULES = {
    "mode": "master_upgrades_only",
    "private_origin_required": True,
    "private_origin_path": PRIVATE_ORIGIN_PATH,
    "private_origin_port": PRIVATE_ORIGIN_PORT,
    "automatic_publication": False,
    "simulation_counts_as_runtime_proof": False,
    "code_or_ci_counts_as_runtime_proof": False,
    "release_evidence_requirements": RELEASE_EVIDENCE_REQUIREMENTS,
    "ecosystem_wide_runtime_enforcement_verified": False,
    "static_extra_counts_as_green": False,
    "real_green_definition": (
        "Fully functioning, working end-to-end, proof-passed, install-ready on supported platforms, "
        "public/private clean, monitored, reversible and HRM-recorded."
    ),
    "public_world_rule": "OAP World stays clean: one front door, no internal SMI noise, no debug language, no fake live labels.",
    "install_rule": "Install is not real green until manifest, icons, service worker/app shell, Android, iOS, desktop and offline-safe fallback checks pass.",
}


REAL_GREEN_GATES = (
    "end_to_end_function_works",
    "public_route_returns_200_or_expected_redirect",
    "api_returns_clean_json",
    "private_routes_fail_closed_anonymously",
    "no_public_private_debug_leak",
    "source_name_present",
    "source_timestamp_present",
    "stale_data_warning_present",
    "hrm_receipt_recorded",
    "rollback_or_recovery_path_exists",
    "fresh_error_logs_clean",
    "install_manifest_valid",
    "icons_available",
    "service_worker_or_install_controller_ready",
    "android_install_path_tested",
    "ios_add_to_home_screen_path_documented_or_tested",
    "desktop_install_path_tested",
    "payment_capture_locked_until_compliance",
    "dispatch_locked_until_operator_proof",
    "hidden_tracking_blocked",
    "fake_green_blocked",
)


OAP_WORLD_NOISE_TO_STRIP = (
    "static extra presented as complete",
    "live surface labels without full proof",
    "public SMI/War Room/internal debug wording",
    "duplicate map/travel/movement cards",
    "fake live traffic/open-now/event claims",
    "too many competing product names on first screen",
    "private status blocks on public pages",
)


MASTER_UPGRADE_LANES = {
    "map_intelligence": {
        "parent": "On Any Place",
        "children": ("Base Map", "Place Data", "Travel", "Movement", "Live Pattern", "Proof", "Consent", "Green Gate"),
        "not_green_until": (
            "real map tiles",
            "route geometry",
            "turn-by-turn guidance",
            "source-backed UK places",
            "events/open-now proof",
            "live traffic/disruption proof",
            "proof-runner pass",
        ),
    },
    "oap_world": {
        "parent": "ON ANY POSTCODE",
        "children": ("On Any Place", "OAP Direct", "The Link", "My World"),
        "not_green_until": (
            "clean public front door",
            "install checks pass",
            "no private debug language",
            "main functions work end-to-end",
        ),
    },
    "smi": {
        "parent": "Private War Room",
        "children": ("simulation", "thinking signals", "green gate", "guardian", "hrm memory"),
        "not_green_until": (
            "private fail-closed proof",
            "HRM receipt writes",
            "live proof runner reads real checks",
            "Founder approval path remains final",
        ),
    },
}


def status() -> dict[str, object]:
    """Return the master upgrade truth contract."""

    return {
        "component": "OAP Master Upgrade Contract",
        "generated_at": _now(),
        "rules": MASTER_UPGRADE_RULES,
        "real_green_gate_count": len(REAL_GREEN_GATES),
        "real_green_gates": REAL_GREEN_GATES,
        "noise_to_strip": OAP_WORLD_NOISE_TO_STRIP,
        "lanes": MASTER_UPGRADE_LANES,
        "status": {
            "master_upgrade_contract": "🟣 source contract; runtime enforcement incomplete",
            "static_extra_green": "🔴 blocked",
            "oap_world_noise": "🟡 stripping",
            "install_ready_any_platform": "🟠 not proven",
            "whole_product_green": "🟠 not green",
        },
        "locks": {
            "payment_capture_enabled": False,
            "dispatch_enabled": False,
            "hidden_tracking_enabled": False,
            "fake_green_enabled": False,
            "self_approval_enabled": False,
        },
        "human_authority_final": True,
        "overall_green": False,
    }
