"""Guard real live browser voice-to-original-character wiring, without invented visemes."""
from pathlib import Path

CONTROLLER = (
    Path(__file__).resolve().parents[1]
    / "mission_control/static/smi_canonical_controller.js"
)


def test_original_character_receives_real_browser_playback_lifecycle_only():
    source = CONTROLLER.read_text(encoding="utf-8")
    assert "function oapPlaybackState(phase,epoch)" in source
    assert "oapCharacter.dataset.audioPlayback=phase" in source
    assert "oap-smi-playback-state" in source
    assert "source:'browser-speech-synthesis'" in source
    assert "decodedAudio:false" in source
    assert "accurateLipSyncProven:false" in source
    assert "oapPlaybackState('playing',oapRuntime?.epoch)" in source
    assert "utterance.onend=()=>finish('ended')" in source
    assert "utterance.onerror=()=>finish('error')" in source


def test_stop_and_live_off_invalidate_before_playback_receipt():
    source = CONTROLLER.read_text(encoding="utf-8")
    stop = source[source.index("function oapStopAll()"):source.index("function oapTogglePause()")]
    assert stop.index("oapSpeechSeq+=1") < stop.index("oapApply('STOP')")
    assert stop.index("oapApply('STOP')") < stop.index("oapPlaybackState('stopped'")
    assert stop.index("oapPlaybackState('stopped'") < stop.index("speechSynthesis.cancel()")
    live_off = source[source.index("function oapSetLive("):source.index("function oapRequestListening(")]
    assert live_off.index("oapSpeechSeq+=1") < live_off.index("oapApply('LIVE_OFF')")
    assert live_off.index("oapApply('LIVE_OFF')") < live_off.index("oapPlaybackState('cancelled'")
    assert "seq!==oapSpeechSeq||!oapStateApi.tokenIsCurrent(oapRuntime,expected)" in source


def test_error_never_counts_as_successful_audio_end():
    source = CONTROLLER.read_text(encoding="utf-8")
    finish = source[source.index("const finish=phase=>"):source.index("window.speechSynthesis.speak(utterance);")]
    assert "if(phase==='ended')oapProof('speakEnd'" in finish
    assert "Voice playback failed" in finish
    assert "utterance.onerror=()=>finish('error')" in finish
    assert "mouthScaleY" not in finish


def test_stale_voice_results_cannot_refill_composer_after_stop_or_live_off():
    source = CONTROLLER.read_text(encoding="utf-8")
    result = source[source.index("oapRecognition.onresult=event=>"):source.index("oapRecognition.onend=()=>")]
    assert "tokenIsCurrent(oapRuntime,oapRecognitionToken)" in result
    assert "!oapRuntime?.listening" in result
    assert result.index("staleCallbackSuppressed") < result.index("oapInput.value=full")
    stop = source[source.index("function oapStopAll()"):source.index("function oapTogglePause()")]
    live_off = source[source.index("function oapSetLive("):source.index("function oapRequestListening(")]
    assert "oapRecognitionToken=null;oapFinalTranscript=''" in stop
    assert "oapRecognitionToken=null;oapFinalTranscript=''" in live_off
    pagehide = source[source.index("window.addEventListener('pagehide'"):]
    assert "oapFinalTranscript='';oapShowLiveReply('')" in pagehide
