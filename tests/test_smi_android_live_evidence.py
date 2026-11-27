from datetime import UTC, datetime

from mission_control import smi_android_live_evidence as evidence


def valid_receipt():
    h = "a" * 64
    return {
        "evidenceType": "physical_android_live_smi",
        "platform": "Android",
        "deviceModel": "25028RN03A",
        "androidVersion": "15",
        "approvedSourceSha256": evidence.APPROVED_SOURCE_SHA256,
        "layerSha256": {name: h for name in evidence.EVIDENCE_LAYERS},
        "exactCharacterIntact": True,
        "microphoneStartObserved": True,
        "sendObserved": True,
        "persistedReplyObserved": True,
        "conversationId": "11111111-1111-4111-8111-111111111111",
        "requestId": "22222222-2222-4222-8222-222222222222",
        "playedAudioObserved": True,
        "motionObserved": True,
        "pauseObserved": True,
        "resumeObserved": True,
        "maxAudioClockDeltaMs": 20.0,
        "motionStopped": True,
        "audioStopped": True,
        "stopAcknowledgementMs": 5.0,
        "backgroundStopPassed": True,
        "storesAudio": False,
        "storesTranscript": False,
        "humanVisualApproved": True,
        "productionApproved": False,
        "humanFinalApproved": False,
        "testedAt": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "humanNote": "Exact original character and actual reply audio observed.",
    }


def test_physical_android_live_receipt_accepts_only_complete_real_chain():
    result = evidence.validate_physical_android_receipt(valid_receipt())
    assert result["accepted"] is True
    assert result["reasons"] == []
    assert result["production_approved"] is False
    assert result["human_final_approved"] is False


def test_physical_android_live_receipt_fails_closed_for_missing_real_evidence():
    for field, value in [
        ("platform", "Desktop"),
        ("exactCharacterIntact", False),
        ("microphoneStartObserved", False),
        ("sendObserved", False),
        ("persistedReplyObserved", False),
        ("playedAudioObserved", False),
        ("motionObserved", False),
        ("pauseObserved", False),
        ("resumeObserved", False),
        ("motionStopped", False),
        ("audioStopped", False),
        ("backgroundStopPassed", False),
        ("humanVisualApproved", False),
        ("storesAudio", True),
        ("storesTranscript", True),
        ("productionApproved", True),
        ("humanFinalApproved", True),
        ("maxAudioClockDeltaMs", 80.1),
        ("stopAcknowledgementMs", 50.1),
    ]:
        payload = valid_receipt()
        payload[field] = value
        result = evidence.validate_physical_android_receipt(payload)
        assert result["accepted"] is False
        assert result["reasons"]


def test_record_requires_durable_independent_hrm_readback(monkeypatch):
    calls = []

    def write_receipt(kind, payload, require_durable=False):
        calls.append((kind, payload, require_durable))
        return {
            "ok": True,
            "durable": True,
            "read_back_ok": True,
            "fallback_used": False,
            "receipt_id": "smi-test",
            "status": "written_and_read_back",
        }

    monkeypatch.setattr(evidence.smi_receipt_backend, "write_receipt", write_receipt)
    monkeypatch.setenv("RENDER_GIT_COMMIT", "a" * 40)
    result = evidence.record_physical_android_receipt(
        valid_receipt(), identity_id="founder-owner"
    )
    assert result["accepted"] is True
    assert result["durable"] is True
    assert result["production_approved"] is False
    assert result["human_final_approved"] is False
    assert calls and calls[0][0] == "hrm_neon_evidence_receipt"
    assert calls[0][2] is True
    safe = calls[0][1]["safe_payload"]
    assert "deviceModel" not in safe
    assert "humanNote" not in safe
    assert safe["stores_audio"] is False
    assert safe["stores_transcript"] is False
    assert safe["motion_performance"] is None
    assert safe["motion_performance_measured"] is False
    assert safe["physical_smoothness_approved"] is False
    assert safe["accurate_lip_sync_approved"] is False


def motion_performance():
    return {
        "version": 1, "measurement": "browser_canvas_submission", "status": "completed",
        "captureMode": "live",
        "sampleCount": 60, "durationMs": 2000, "measuredFps": 30,
        "frameP50Ms": 33, "frameP95Ms": 50, "frameMaxMs": 70, "renderP95Ms": 4,
        "overBudgetCount": 2, "physicalDeviceProven": False,
        "thermalStatus": "unknown", "smoothnessApproved": False,
    }


def test_browser_measurements_are_bounded_evidence_not_physical_approval(monkeypatch):
    payload = valid_receipt()
    payload["motionPerformance"] = motion_performance()
    assert evidence.validate_physical_android_receipt(payload)["accepted"] is True
    stored = []

    def write_receipt(kind, data, **kwargs):
        stored.append(data["safe_payload"])
        return {"ok": True, "durable": True, "read_back_ok": True, "fallback_used": False}

    monkeypatch.setattr(evidence.smi_receipt_backend, "write_receipt", write_receipt)
    evidence.record_physical_android_receipt(payload, identity_id="founder")
    assert stored[0]["motion_performance"] == motion_performance()
    assert stored[0]["motion_performance_measured"] is True
    assert stored[0]["physical_smoothness_approved"] is False
    assert stored[0]["anatomical_masks_approved"] is False
    for field, value in [
        ("sampleCount", 601), ("sampleCount", True), ("durationMs", float("nan")),
        ("measuredFps", 60), ("frameP95Ms", 10), ("frameP50Ms", -1),
        ("overBudgetCount", 61), ("renderP95Ms", float("inf")),
        ("physicalDeviceProven", True), ("smoothnessApproved", True),
        ("thermalStatus", "cool"), ("transcript", "must never be retained"),
    ]:
        payload["motionPerformance"] = {**motion_performance(), field: value}
        result = evidence.validate_physical_android_receipt(payload)
        assert result["accepted"] is False, field
        assert "motion_performance_invalid" in result["reasons"]


def test_nonfinite_timing_cannot_pass_android_proof():
    for field in ("maxAudioClockDeltaMs", "stopAcknowledgementMs"):
        for value in (float("nan"), float("inf"), -float("inf"), 10**1000):
            payload = valid_receipt()
            payload[field] = value
            assert evidence.validate_physical_android_receipt(payload)["accepted"] is False


def test_record_does_not_fallback_to_fake_green(monkeypatch):
    monkeypatch.setattr(
        evidence.smi_receipt_backend,
        "write_receipt",
        lambda *args, **kwargs: {
            "ok": True,
            "durable": False,
            "read_back_ok": True,
            "fallback_used": True,
            "receipt_id": "smi-ephemeral",
            "status": "written_and_read_back",
        },
    )
    result = evidence.record_physical_android_receipt(
        valid_receipt(), identity_id="founder-owner"
    )
    assert result["accepted"] is False
    assert result["reasons"] == ["durable_hrm_receipt_unconfirmed"]
