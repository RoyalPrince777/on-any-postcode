from pathlib import Path

MOTION = Path("mission_control/static/smi_source_pixel_motion.js")


def test_source_pixel_motion_uses_lightweight_live_rendering_path():
    text = MOTION.read_text(encoding="utf-8")
    assert "function drawRegion(region,params)" in text
    assert "context.ellipse(" in text
    assert "context.scale(" in text
    assert "frameBudgetMs=lowPower?33:16" in text
    assert 'function renderActive()' in text
    assert 'return epoch>=0&&!doc.hidden&&!userReducedMotion&&' in text
    assert 'function resetFrameTelemetry()' in text
    assert 'doc.addEventListener?.("visibilitychange",resetFrameTelemetry)' in text
    assert 'ambientFrameBudgetMs=lowPower?50:33' in text
    assert 'context=canvas.getContext("2d",{alpha:false})' in text
    assert 'evidenceContext=evidenceCanvas.getContext("2d",{willReadFrequently:true})' in text
    assert 'context.imageSmoothingQuality="high"' in text
    assert "renderCostMs*1.8" in text
    assert "observedFps:" in text
    assert "adaptiveFrameBudgetMs:" in text
    assert "const featheredPatches=new Map(REGIONS.map(region=>{" in text
    assert 'pc.globalCompositeOperation="destination-in"' in text
    assert 'edge.addColorStop(1,"rgba(255,255,255,0)")' in text
    assert 'regionEdgeBlending:"source_pixel_feather_no_anatomy_approval"' in text
    assert "function createPoseSmoother()" in text
    assert "poseSmoother.next(motionFor(phase,ms,pulse),ms)" in text
    assert "Math.min(70,ms-previousTime)" in text
    assert "if(doc.hidden)poseSmoother.reset()" in text
    assert 'poseEasing:"bounded_time_based_source_pixel_only"' in text
    assert "fullArticulatedMotionProven:false" in text
    assert 'ambientVisualMotion:renderActive()&&phase==="ready"&&!live&&played>0' in text
    assert 'frameRateTargetFps:renderActive()?' in text
    assert 'observedFps:renderActive()?' in text
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
