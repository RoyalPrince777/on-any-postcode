from pathlib import Path

MOTION = Path("mission_control/static/smi_source_pixel_motion.js")


def test_source_pixel_motion_uses_lightweight_live_rendering_path():
    text = MOTION.read_text(encoding="utf-8")
    assert "function drawRegion(region,params)" in text
    assert "context.ellipse(" in text
    assert "context.scale(" in text
    assert "frameBudgetMs=lowPower?50:34" in text
    assert 'doc.hidden||(!live&&phase!=="ready")' in text
    assert 'ambientFrameBudgetMs=lowPower?170:120' in text
    assert 'ambientVisualMotion:phase==="ready"&&!live&&played>0' in text
    assert "droppedFrames" in text


def test_source_pixel_motion_keeps_lip_sync_truth_boundary():
    text = MOTION.read_text(encoding="utf-8")
    assert 'cue?.source!=="oap-first-party-pcm"' in text
    assert "cue?.synthesisPhonemeTiming!==true" in text
    assert "audioCues>=3" in text
    assert "accurateHumanLipSyncProven:false" in text
    assert "source:'browser-speech-synthesis',decodedAudio:false,phonemeAligned:false" in Path(
        "mission_control/static/smi_canonical_controller.js"
    ).read_text(encoding="utf-8")
