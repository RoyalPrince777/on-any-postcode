"""Offline structural checks for exact-character geometry and motion evidence.

Even a geometrically consistent timeline is NOT evidence of authentic
segmentation, true character movement, audio playback, or Founder approval.
This module cannot render, animate, fetch, record, activate or share layers.
"""
from __future__ import annotations

import math
import re
from collections.abc import Mapping
from typing import Any, Final

from .character_rig_assets import APPROVED_SOURCE_SHA256, LAYERS

ANCHORS: Final[dict[str, tuple[str, ...]]] = {
    "eyes": ("left_eye_center", "right_eye_center"),
    "head": ("head_pivot", "chin"),
    "breathing": ("sternum", "abdomen"),
    "mouth_visemes": ("upper_lip", "lower_lip", "left_corner", "right_corner"),
    "face": ("left_brow", "right_brow", "nose_tip"),
    "hands": ("left_wrist", "right_wrist", "left_palm", "right_palm"),
    "upper_body": ("left_shoulder", "right_shoulder", "spine"),
}
VISEMES: Final = frozenset(
    {"silence", "AA", "EE", "IH", "OH", "OU", "FV", "MBP", "L", "WQ"}
)
LABEL = re.compile(r"^[a-z][a-z0-9_]{0,47}$")
MIN_FRAMES: Final = 2
MAX_FRAMES: Final = 240
MAX_DURATION_MS: Final = 30_000
MAX_DELTA: Final = 0.25


def _finite_number(value: object, minimum: float, maximum: float) -> bool:
    return (
        type(value) in (int, float)
        and minimum <= value <= maximum
        and math.isfinite(value)
    )


def _point(value: object, minimum: float, maximum: float) -> bool:
    return (
        isinstance(value, (list, tuple))
        and len(value) == 2
        and all(_finite_number(x, minimum, maximum) for x in value)
    )


def _layer(record: object, name: str) -> str:
    if not isinstance(record, Mapping):
        return "missing_geometry_or_motion"
    landmarks = record.get("landmarks")
    anchors = ANCHORS[name]
    if (
        not isinstance(landmarks, Mapping)
        or not set(anchors).issubset(landmarks)
        or len(landmarks) > 64
        or any(
            not isinstance(label, str)
            or not LABEL.fullmatch(label)
            or not _point(point, 0.0, 1.0)
            for label, point in landmarks.items()
        )
    ):
        return "invalid_landmarks"
    # Duplicate anchor positions make pivots and bilateral anatomy ambiguous.
    if len({tuple(landmarks[label]) for label in anchors}) != len(anchors):
        return "coincident_required_anchors"

    frames = record.get("frames")
    if (
        not isinstance(frames, list)
        or not MIN_FRAMES <= len(frames) <= MAX_FRAMES
    ):
        return "invalid_motion_sequence"
    previous = -1
    for frame in frames:
        if not isinstance(frame, Mapping):
            return "invalid_motion_sequence"
        ms = frame.get("t_ms")
        deltas = frame.get("delta")
        if (
            type(ms) is not int
            or not previous < ms <= MAX_DURATION_MS
            or not isinstance(deltas, Mapping)
            or set(deltas) != set(anchors)
            or not all(
                _point(deltas[label], -MAX_DELTA, MAX_DELTA)
                for label in anchors
            )
        ):
            return "invalid_motion_sequence"
        previous = ms
        if name == "mouth_visemes" and (
            not isinstance(frame.get("viseme"), str)
            or frame["viseme"] not in VISEMES
            or type(frame.get("audio_ms")) is not int
            or abs(frame["audio_ms"] - ms) > 80
            or frame["audio_ms"] < 0
        ):
            return "invalid_viseme_timing_metadata"
    return "schema_consistent_not_motion_proof"


def inspect_geometry(
    bundle: object,
    asset_report: object,
) -> dict[str, Any]:
    """Bounded structural verdict; always fail-closed for rig activation."""
    verdict: dict[str, Any] = {
        "version": "0.1",
        "active": False,
        "emits_frames": False,
        "identity_proven": False,
        "geometry_proven": False,
        "speech_sync_proven": False,
        "motion_proven": False,
        "human_authority_approved": False,
        "layers": {name: "not_inspected" for name in LAYERS},
    }
    if not isinstance(bundle, Mapping) or bundle.get("version") != "0.1":
        return {**verdict, "reason": "missing_or_invalid_evidence"}
    if bundle.get("approved_source_sha256") != APPROVED_SOURCE_SHA256:
        return {**verdict, "reason": "source_identity_unproven"}
    if (
        not isinstance(asset_report, Mapping)
        or not isinstance(asset_report.get("layers"), Mapping)
        or asset_report.get("reason")
        != "bytes_verified_only_requires_independent_rig_proofs"
        or set(asset_report.get("layers", {})) != set(LAYERS)
        or any(
            value != "bytes_valid_not_rig_proof"
            for value in asset_report["layers"].values()
        )
    ):
        return {**verdict, "reason": "private_asset_bytes_unproven"}
    layers = bundle.get("layers")
    if not isinstance(layers, Mapping) or set(layers) != set(LAYERS):
        return {**verdict, "reason": "seven_layer_geometry_incomplete"}
    results = {name: _layer(layers[name], name) for name in LAYERS}
    verdict["layers"] = results
    verdict["reason"] = (
        "schema_only_requires_independent_visual_motion_and_audio_proof"
        if all(x == "schema_consistent_not_motion_proof" for x in results.values())
        else "geometry_or_timing_schema_incomplete"
    )
    return verdict
