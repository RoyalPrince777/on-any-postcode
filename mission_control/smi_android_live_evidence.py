"""Physical Android live SMI evidence: validate real browser observations and
write one owner-scoped durable HRM receipt.

This module never fabricates device observations, stores transcript/audio, or
grants production approval. Human visual approval is mandatory and the durable
receipt remains evidence only; Human Authority stays final.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
from datetime import UTC, datetime
from typing import Any

from . import smi_receipt_backend

APPROVED_SOURCE_SHA256 = "f9503174f6f18b815f1c73e24faff3b4966c2e1fbae8d20a8d2bcc22e4a84a4b"
EVIDENCE_LAYERS = (
    "eyes",
    "head",
    "breathing",
    "mouth_visemes",
    "face",
    "hands",
    "upper_body",
)
MAX_AUDIO_CLOCK_DELTA_MS = 80.0
MAX_STOP_ACKNOWLEDGEMENT_MS = 50.0
_HASH = re.compile(r"^[a-f0-9]{64}$")
_UUIDISH = re.compile(r"^[a-f0-9-]{16,64}$", re.IGNORECASE)


def _now() -> datetime:
    return datetime.now(UTC)


def _fresh_iso(value: object) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return False
    if parsed.tzinfo is None:
        return False
    delta = (_now() - parsed.astimezone(UTC)).total_seconds()
    return -300 <= delta <= 86400


def _is_number(value: object) -> bool:
    return (
        type(value) in (int, float)
        and -1e308 <= value <= 1e308
        and math.isfinite(value)
    )


def _valid_motion_performance(value: object) -> bool:
    """Check bounded browser aggregates, never infer physical smoothness."""
    if not isinstance(value, dict) or set(value) != {
        "version", "measurement", "status", "captureMode", "sampleCount", "durationMs",
        "measuredFps", "frameP50Ms", "frameP95Ms", "frameMaxMs", "renderP95Ms",
        "overBudgetCount", "physicalDeviceProven", "thermalStatus", "smoothnessApproved",
    }:
        return False
    if (
        type(value["version"]) is not int or value["version"] != 1
        or value["measurement"] != "browser_canvas_submission"
        or value["status"] not in ("unknown", "capturing", "completed")
        or value["captureMode"] not in ("unknown", "ambient", "live")
        or value["physicalDeviceProven"] is not False
        or value["smoothnessApproved"] is not False
        or value["thermalStatus"] != "unknown"
    ):
        return False
    count, over = value["sampleCount"], value["overBudgetCount"]
    if type(count) is not int or not 0 <= count <= 600:
        return False
    if type(over) is not int or not 0 <= over <= count:
        return False
    duration = value["durationMs"]
    if not _is_number(duration) or not 0 <= duration <= 3_600_000:
        return False
    metrics = ("measuredFps", "frameP50Ms", "frameP95Ms", "frameMaxMs", "renderP95Ms")
    if count == 0:
        return (
            value["status"] == "unknown" and duration == 0
            and all(value[key] is None for key in metrics)
        )
    if value["status"] == "unknown" or duration <= 0:
        return False
    if any(not _is_number(value[key]) or value[key] < 0 for key in metrics):
        return False
    # Percentiles describe submitted frames, not display scan-out or a target.
    return (
        0 < value["measuredFps"] <= 1000
        and abs(value["measuredFps"] - count * 1000 / duration) <= 0.1
        and 0 < value["frameP50Ms"] <= value["frameP95Ms"] <= value["frameMaxMs"] <= duration + 0.01
        and value["renderP95Ms"] <= 60_000
    )


def validate_physical_android_receipt(payload: object) -> dict[str, Any]:
    reasons: list[str] = []
    if not isinstance(payload, dict):
        return {
            "accepted": False,
            "reasons": ["receipt_missing"],
            "production_approved": False,
            "human_final_approved": False,
        }

    if payload.get("evidenceType") != "physical_android_live_smi":
        reasons.append("physical_android_live_test_missing")
    if payload.get("platform") != "Android":
        reasons.append("platform_not_android")

    device_model = str(payload.get("deviceModel") or "").strip()
    android_version = str(payload.get("androidVersion") or "").strip()
    if len(device_model) < 2:
        reasons.append("device_model_missing")
    if not android_version:
        reasons.append("android_version_missing")

    if payload.get("approvedSourceSha256") != APPROVED_SOURCE_SHA256:
        reasons.append("source_sha_mismatch")

    layers = payload.get("layerSha256")
    if (
        not isinstance(layers, dict)
        or set(layers) != set(EVIDENCE_LAYERS)
        or any(not _HASH.fullmatch(str(layers.get(name) or "")) for name in EVIDENCE_LAYERS)
    ):
        reasons.append("seven_source_region_hashes_invalid")

    required_true = {
        "exactCharacterIntact": "exact_character_not_proven",
        "microphoneStartObserved": "microphone_start_unproven",
        "sendObserved": "send_unproven",
        "persistedReplyObserved": "persisted_reply_unproven",
        "playedAudioObserved": "played_audio_unproven",
        "motionObserved": "character_motion_unproven",
        "pauseObserved": "pause_unproven",
        "resumeObserved": "resume_unproven",
        "motionStopped": "motion_stop_unproven",
        "audioStopped": "audio_stop_unproven",
        "backgroundStopPassed": "background_stop_unproven",
        "humanVisualApproved": "human_visual_approval_missing",
    }
    for field, reason in required_true.items():
        if payload.get(field) is not True:
            reasons.append(reason)

    audio_delta = payload.get("maxAudioClockDeltaMs")
    if (
        not _is_number(audio_delta)
        or float(audio_delta) < 0
        or float(audio_delta) > MAX_AUDIO_CLOCK_DELTA_MS
    ):
        reasons.append("played_audio_timing_unproven")

    stop_ack = payload.get("stopAcknowledgementMs")
    if (
        not _is_number(stop_ack)
        or float(stop_ack) < 0
        or float(stop_ack) > MAX_STOP_ACKNOWLEDGEMENT_MS
    ):
        reasons.append("immediate_stop_unproven")

    if payload.get("storesAudio") is not False or payload.get("storesTranscript") is not False:
        reasons.append("privacy_retention_boundary_invalid")
    if payload.get("productionApproved") is not False or payload.get("humanFinalApproved") is not False:
        reasons.append("forbidden_approval_claim")

    # Legacy receipts stay readable but cannot acquire performance proof.
    performance = payload.get("motionPerformance")
    if performance is not None and not _valid_motion_performance(performance):
        reasons.append("motion_performance_invalid")

    if not _fresh_iso(payload.get("testedAt")):
        reasons.append("test_time_invalid_or_stale")

    human_note = str(payload.get("humanNote") or "").strip()
    if len(human_note) < 3 or len(human_note) > 500:
        reasons.append("human_note_missing_or_invalid")

    conversation_id = str(payload.get("conversationId") or "").strip()
    request_id = str(payload.get("requestId") or "").strip()
    if not _UUIDISH.fullmatch(conversation_id):
        reasons.append("conversation_id_missing")
    if not _UUIDISH.fullmatch(request_id):
        reasons.append("request_id_missing")

    return {
        "accepted": not reasons,
        "reasons": sorted(set(reasons)),
        "production_approved": False,
        "human_final_approved": False,
    }


def record_physical_android_receipt(
    payload: object,
    *,
    identity_id: str,
) -> dict[str, Any]:
    validation = validate_physical_android_receipt(payload)
    if not validation["accepted"]:
        return {
            **validation,
            "durable": False,
            "receipt_id": None,
            "status": "physical_android_evidence_rejected",
        }

    assert isinstance(payload, dict)
    runtime_revision = (os.getenv("RENDER_GIT_COMMIT") or "").strip()
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    receipt_sha256 = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    owner_sha256 = hashlib.sha256(str(identity_id).encode("utf-8")).hexdigest()
    model_sha256 = hashlib.sha256(str(payload["deviceModel"]).encode("utf-8")).hexdigest()
    note_sha256 = hashlib.sha256(str(payload["humanNote"]).encode("utf-8")).hexdigest()

    safe_payload = {
        "proof_version": "physical-android-live-smi-v1",
        "owner_sha256": owner_sha256,
        "runtime_revision": runtime_revision or "unknown",
        "receipt_sha256": receipt_sha256,
        "platform": "Android",
        "android_version": str(payload["androidVersion"]),
        "device_model_sha256": model_sha256,
        "approved_source_sha256": APPROVED_SOURCE_SHA256,
        "layer_sha256": {name: str(payload["layerSha256"][name]) for name in EVIDENCE_LAYERS},
        "exact_character_intact": True,
        "microphone_start_observed": True,
        "send_observed": True,
        "persisted_reply_observed": True,
        "conversation_id": str(payload["conversationId"]),
        "request_id": str(payload["requestId"]),
        "played_audio_observed": True,
        "motion_observed": True,
        "pause_observed": True,
        "resume_observed": True,
        "max_audio_clock_delta_ms": float(payload["maxAudioClockDeltaMs"]),
        "motion_stopped": True,
        "audio_stopped": True,
        "stop_acknowledgement_ms": float(payload["stopAcknowledgementMs"]),
        "background_stop_passed": True,
        "motion_performance": payload.get("motionPerformance"),
        "motion_performance_measured": bool(
            payload.get("motionPerformance")
            and payload["motionPerformance"]["sampleCount"] > 0
        ),
        "physical_smoothness_approved": False,
        "anatomical_masks_approved": False,
        "accurate_lip_sync_approved": False,
        "tested_at": str(payload["testedAt"]),
        "human_visual_approved": True,
        "human_note_sha256": note_sha256,
        "stores_audio": False,
        "stores_transcript": False,
        "production_approved": False,
        "human_final_approved": False,
        "authority_transferred": False,
    }
    receipt = smi_receipt_backend.write_receipt(
        "hrm_neon_evidence_receipt",
        {
            "brain_part": "smi_android_live",
            "gate": 21,
            "command": "physical_android_live_acceptance",
            "signal": "🟣",
            "guardian": "physical_runtime_observed",
            "green_gate": "device_evidence_recorded_founder_final_still_required",
            "founder_final": "required_for_full_green",
            "safe_payload": safe_payload,
        },
        require_durable=True,
    )
    durable = bool(
        receipt.get("ok")
        and receipt.get("durable")
        and receipt.get("read_back_ok")
        and not receipt.get("fallback_used")
    )
    return {
        "accepted": durable,
        "reasons": [] if durable else ["durable_hrm_receipt_unconfirmed"],
        "durable": durable,
        "receipt_id": receipt.get("receipt_id"),
        "receipt_sha256": receipt_sha256,
        "status": (
            "physical_android_evidence_durable"
            if durable
            else str(receipt.get("status") or "durable_hrm_receipt_unconfirmed")
        ),
        "production_approved": False,
        "human_final_approved": False,
        "runtime_revision": runtime_revision or None,
    }
