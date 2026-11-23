"""First-party SMI anti-biometric privacy boundary.

This pure policy module does not access device sensors, alter Android permissions,
block public cameras or certify a deployed shield. No raw biometric templates
are ever accepted by the Founder-private recognition path.
"""
from __future__ import annotations

import re
from collections.abc import Mapping

# Do not classify ordinary consensual voice calls as voiceprints.
_BIOMETRIC_TERMS = frozenset({
    "biometric", "biometrics", "face", "facial", "faceprint", "face_template",
    "face_embedding", "facial_recognition", "facial_template", "fingerprint",
    "fingerprints", "fingerprint_template", "palmprint", "iris", "retina",
    "voiceprint", "voice_print", "speaker_id", "speaker_identification",
    "speaker_recognition", "gait", "gait_recognition", "walking_pattern",
    "keystroke", "keystroke_dynamics", "typing_pattern",
    "behavioural_biometric", "behavioral_biometric",
    "behavioural_biometrics", "behavioral_biometrics",
})
_SENSITIVE_LOCATION = frozenset({"location", "precise_location", "gps", "movement_history"})
_ALLOWED_OPERATIONS = frozenset({"observe", "store", "profile", "identify", "share", "export", "train"})
_REQUIRED_EVIDENCE = (
    "code_dataflow_review", "device_permission_review",
    "local_storage_audit", "network_egress_test",
    "android_device_test", "guardian_independent_review",
    "hrm_receipt_readback", "founder_final",
)


def _normalise(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return re.sub(r"[^a-z0-9]+", "_", value.casefold()).strip("_")


def is_raw_biometric_category(category: object) -> bool:
    """Conservatively identify known identity/behavioural biometric categories."""
    key = _normalise(category)
    return bool(
        key in _BIOMETRIC_TERMS
        or key.startswith(("biometric_", "biometrics_", "faceprint_", "voiceprint_"))
        or any(
            f"_{term}_" in f"_{key}_"
            for term in ("fingerprint", "face_template", "face_embedding", "voiceprint",
                         "gait_recognition", "keystroke_dynamics", "facial_recognition")
        )
    )


def permission_decision(
    *,
    category: str,
    operation: str,
    consent: bool,
    destination: str = "local",
) -> dict[str, object]:
    """Fail closed for raw biometrics, nonconsensual location or external export.

    Must be called at each actual ingestion/egress boundary; this function alone
    does not provide OS-level protection or monitor network traffic.
    """
    kind, action, target = map(_normalise, (category, operation, destination))
    if not kind or action not in _ALLOWED_OPERATIONS or target not in {"local", "first_party", "external"}:
        return {"allowed": False, "reason": "UNKNOWN_FLOW"}
    if is_raw_biometric_category(kind):
        return {"allowed": False, "reason": "RAW_BIOMETRICS_BLOCKED"}
    if target == "external":
        return {"allowed": False, "reason": "EXTERNAL_DESTINATION_BLOCKED"}
    if kind in _SENSITIVE_LOCATION and (not consent or target != "local" or action in {"profile", "identify", "train"}):
        return {"allowed": False, "reason": "LOCATION_MINIMISATION"}
    if not consent:
        return {"allowed": False, "reason": "NO_CONSENT"}
    return {"allowed": True, "reason": "CONSENTED_FIRST_PARTY_FLOW"}



# Scope of already-existing camera, mic, picture, Bluetooth and motion systems.
# Permission is for a specific action, not a standing right to scan in background.
_DEVICE_MEDIA_KINDS = frozenset({
    "camera", "camera_frame", "photo", "picture", "gallery_photo",
    "image_capture", "photo_attachment", "picture_attachment",
    "microphone", "mic", "mic_capture", "audio_capture", "voice_note",
    "voice_message", "screen_capture", "bluetooth", "bluetooth_scan",
    "bluetooth_transfer", "nearby_device", "nearby_devices",
    "device_discovery", "motion", "accelerometer", "gyroscope",
})
_BLUETOOTH_KINDS = frozenset({
    "bluetooth", "bluetooth_scan", "bluetooth_transfer",
    "nearby_device", "nearby_devices", "device_discovery",
})
_DEVICE_OPERATIONS = frozenset({
    "capture", "record", "read", "store", "scan", "discover",
    "transfer", "share", "stream",
})


def sensor_flow_decision(
    *,
    kind: str,
    operation: str,
    consent: bool,
    foreground: bool,
    destination: str = "local",
    peer_authorised: bool = False,
) -> dict[str, object]:
    """Policy for existing OAP sensor/media pathways, not OS enforcement.

    Capture and discovery must be visible, explicit and first-party. Sharing
    to a different first-party recipient requires separately authorised peer.
    Device permissions, live flows and paired hardware still require proof.
    """
    category, action, target = map(_normalise, (kind, operation, destination))
    if is_raw_biometric_category(category):
        return {"allowed": False, "reason": "RAW_BIOMETRICS_BLOCKED"}
    if (
        category not in _DEVICE_MEDIA_KINDS
        or action not in _DEVICE_OPERATIONS
        or target not in {"local", "first_party", "external"}
    ):
        return {"allowed": False, "reason": "UNKNOWN_FLOW"}
    if target == "external":
        return {"allowed": False, "reason": "EXTERNAL_DESTINATION_BLOCKED"}
    if not consent:
        return {"allowed": False, "reason": "NO_CONSENT"}
    if action in {"scan", "discover"} and category not in _BLUETOOTH_KINDS:
        return {"allowed": False, "reason": "INCOMPATIBLE_SENSOR_OPERATION"}
    if not foreground and action in {
        "capture", "record", "scan", "discover", "stream", "read",
    }:
        return {"allowed": False, "reason": "BACKGROUND_SENSOR_ACCESS_BLOCKED"}
    if action in {"transfer", "share"} and target == "first_party" and not peer_authorised:
        return {"allowed": False, "reason": "PEER_AUTHORISATION_REQUIRED"}
    return {"allowed": True, "reason": "CONSENTED_FIRST_PARTY_FLOW"}

def evidence_gate(checks: Mapping[str, object] | None = None) -> dict[str, object]:
    """Report missing proof; caller-supplied flags never self-certify production."""
    supplied = checks if isinstance(checks, Mapping) else {}
    missing = tuple(key for key in _REQUIRED_EVIDENCE if supplied.get(key) is not True)
    return {
        "scope": "SMI application biometric privacy only",
        "status": "UNKNOWN" if missing else "REVIEW_REQUIRED",
        "missing_proof": missing,
        "code_policy_present": True,
        "android_protection_verified": False,
        "external_cctv_blockable": False,
        "universal_tracking_blocked": False,
        "guaranteed": False,
        "human_authority_final": True,
    }
