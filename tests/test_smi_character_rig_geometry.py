"""Adversarial geometry schema gate; mock landmarks are never authentic rig proof."""

from __future__ import annotations

from copy import deepcopy

import pytest

from oap.smi.character_rig_assets import APPROVED_SOURCE_SHA256, LAYERS
from oap.smi.character_rig_geometry import ANCHORS, inspect_geometry


def _assets():
    return {
        "reason": "bytes_verified_only_requires_independent_rig_proofs",
        "layers": {name: "bytes_valid_not_rig_proof" for name in LAYERS},
        "active": False,
        "motion_proven": False,
    }


def _sample():
    layers = {}
    for name in LAYERS:
        anchors = ANCHORS[name]
        landmarks = {
            label: [0.10 + i * 0.10, 0.15 + i * 0.10]
            for i, label in enumerate(anchors)
        }
        frames = []
        for timecode in (0, 120):
            frame = {
                "t_ms": timecode,
                "delta": {label: [0.01, -0.01] for label in anchors},
            }
            if name == "mouth_visemes":
                frame["viseme"] = "silence" if timecode == 0 else "AA"
                frame["audio_ms"] = timecode
            frames.append(frame)
        layers[name] = {"landmarks": landmarks, "frames": frames}
    return {
        "version": "0.1",
        "approved_source_sha256": APPROVED_SOURCE_SHA256,
        "layers": layers,
        "founder_approved": True,
        "motion_proven": True,
        "enable_rig": True,
    }


def test_no_evidence_and_no_asset_report_fail_closed():
    assert inspect_geometry(None, None)["reason"] == "missing_or_invalid_evidence"
    assert inspect_geometry(_sample(), None)["reason"] == "private_asset_bytes_unproven"
    assert inspect_geometry(_sample(), {"layers": None})["active"] is False


def test_complete_schema_never_proves_identity_motion_or_live_visemes():
    result = inspect_geometry(_sample(), _assets())
    assert result["reason"] == "schema_only_requires_independent_visual_motion_and_audio_proof"
    assert list(result["layers"]) == list(LAYERS)
    assert set(result["layers"].values()) == {"schema_consistent_not_motion_proof"}
    assert all(
        result[key] is False
        for key in (
            "active", "emits_frames", "identity_proven", "geometry_proven",
            "speech_sync_proven", "motion_proven", "human_authority_approved",
        )
    )


def test_forged_source_incomplete_layer_and_forged_asset_report_rejected():
    bundle = _sample()
    bundle["approved_source_sha256"] = "0" * 64
    assert inspect_geometry(bundle, _assets())["reason"] == "source_identity_unproven"
    bundle["approved_source_sha256"] = APPROVED_SOURCE_SHA256
    bundle["layers"].pop("hands")
    assert inspect_geometry(bundle, _assets())["reason"] == "seven_layer_geometry_incomplete"
    bundle = _sample()
    assets = _assets()
    assets["layers"]["eyes"] = "claimed_true"
    assert inspect_geometry(bundle, assets)["reason"] == "private_asset_bytes_unproven"


@pytest.mark.parametrize(
    ("name", "change", "verdict"),
    [
        ("eyes", lambda x: x["landmarks"].pop("left_eye_center"), "invalid_landmarks"),
        ("head", lambda x: x["landmarks"].update({"chin": [2.0, 0.3]}), "invalid_landmarks"),
        ("breathing", lambda x: x["landmarks"].update({"sternum": [float("nan"), 0.2]}), "invalid_landmarks"),
        ("face", lambda x: x["landmarks"].update({"nose_tip": [True, 0.2]}), "invalid_landmarks"),
        ("hands", lambda x: x["landmarks"].update({"left_palm": x["landmarks"]["right_palm"]}), "coincident_required_anchors"),
        ("upper_body", lambda x: x["frames"][1].update({"t_ms": 0}), "invalid_motion_sequence"),
        ("upper_body", lambda x: x["frames"][1]["delta"].update({"spine": [float("inf"), 0]}), "invalid_motion_sequence"),
        ("eyes", lambda x: x["frames"][0]["delta"].update({"left_eye_center": [0.5, 0]}), "invalid_motion_sequence"),
        ("eyes", lambda x: x["frames"][1].update({"t_ms": 30001}), "invalid_motion_sequence"),
        ("mouth_visemes", lambda x: x["frames"][0].pop("audio_ms"), "invalid_viseme_timing_metadata"),
        ("mouth_visemes", lambda x: x["frames"][1].update({"audio_ms": 500}), "invalid_viseme_timing_metadata"),
        ("mouth_visemes", lambda x: x["frames"][0].update({"viseme": []}), "invalid_viseme_timing_metadata"),
    ],
)
def test_bad_landmarks_motion_and_mouth_timing_fail_closed(name, change, verdict):
    bundle = deepcopy(_sample())
    change(bundle["layers"][name])
    result = inspect_geometry(bundle, _assets())
    assert result["layers"][name] == verdict
    assert result["motion_proven"] is False
    assert result["active"] is False
    assert result["reason"] == "geometry_or_timing_schema_incomplete"


def test_malformed_untrusted_records_never_raise_or_prove_motion():
    bundle = _sample()
    report = _assets()
    report["layers"] = ["eyes"]
    assert inspect_geometry(bundle, report)["reason"] == "private_asset_bytes_unproven"

    bundle["layers"]["eyes"]["landmarks"]["left_eye_center"] = [10**1000, 0.2]
    assert inspect_geometry(bundle, _assets())["layers"]["eyes"] == "invalid_landmarks"

    bundle = _sample()
    bundle["layers"]["mouth_visemes"]["frames"][0]["audio_ms"] = True
    assert (
        inspect_geometry(bundle, _assets())["layers"]["mouth_visemes"]
        == "invalid_viseme_timing_metadata"
    )
