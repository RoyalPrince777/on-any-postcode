"""Real local voice requires WAV bytes and eSpeak-issued phoneme events."""
import hashlib
import io
import json
import wave
from contextlib import contextmanager
from itertools import pairwise

import pytest

from mission_control import postgres_db
from mission_control import smi_reply_voice_local as voice


def test_real_reply_audio_and_synthesis_issued_cues():
    result = voice.render_reply("Hello founder. Welcome to On Any Postcode.")
    raw, alignment = result["audio_wav"], result["alignment"]
    assert raw[:4] == b"RIFF" and raw[8:12] == b"WAVE"
    with wave.open(io.BytesIO(raw)) as wav:
        assert wav.getnchannels() == 1
        assert wav.getsampwidth() == 2
        assert 8000 <= wav.getframerate() <= 48000
        assert abs(
            round(wav.getnframes() / wav.getframerate() * 1000)
            - alignment["audioDurationMs"]
        ) <= 1
    assert hashlib.sha256(raw).hexdigest() == alignment["audioSha256"]
    assert alignment["predictedFromText"] is False
    assert alignment["alignmentErrorMeasured"] is False
    assert alignment["maxAlignmentErrorMs"] is None
    assert alignment["source"] == "decoded_audio_phoneme_timeline"
    assert result["phonemeIssuedBySynth"] is True
    assert result["engine"] == "self_hosted_espeak"
    assert result["engineBuild"] == "espeak-ng-1.51-bundled"
    assert result["voiceLocale"] == "en"
    assert result["retainsAudio"] is False
    assert result["externalVoiceProvider"] is False
    assert result["accurateHumanLipSyncProven"] is False
    assert result["fullRigProven"] is False
    cues = alignment["cues"]
    assert len(cues) >= 3 and len({c["viseme"] for c in cues}) >= 3
    assert cues[0] == {"atMs": 0, "viseme": "silence", "confidence": 1}
    assert cues[-1]["atMs"] == alignment["audioDurationMs"]
    assert cues[-1]["viseme"] == "silence"
    assert all(a["atMs"] < b["atMs"] for a, b in pairwise(cues))
    canonical = {
        "audioSha256": alignment["audioSha256"],
        "audioDurationMs": alignment["audioDurationMs"],
        "cues": alignment["cues"],
    }
    assert hashlib.sha256(
        json.dumps(canonical, separators=(",", ":")).encode()
    ).hexdigest() == alignment["timelineSha256"]


@pytest.mark.parametrize("bad", [None, "", " ", "a" * 1501, "bad\x00text", 9])
def test_unapproved_voice_requests_fail_closed(bad):
    with pytest.raises(ValueError, match="reply_voice_text_invalid"):
        voice.render_reply(bad)


def test_missing_native_voice_stays_disabled(monkeypatch):
    def unavailable():
        raise voice.VoiceUnavailable("local_voice_engine_unavailable")

    monkeypatch.setattr(voice, "_resolve_voice_backend", unavailable)
    with pytest.raises(voice.VoiceUnavailable, match="local_voice_engine_unavailable"):
        voice.render_reply("SMI")


def test_render_runtime_uses_pinned_bundled_voice_library():
    library, data_root, build = voice._resolve_voice_backend()
    assert library.endswith(("libespeak-ng.so", "libespeak-ng.dylib", "espeak-ng.dll"))
    assert data_root and data_root.decode()
    assert build == "espeak-ng-1.51-bundled"


@pytest.mark.parametrize("content", ["a" * 1501, " ", "unsafe\x00reply"])
def test_owned_but_unvoiceable_reply_is_not_misreported_as_missing(monkeypatch, content):
    class FakeConnection:
        def execute(self, _query, _params):
            return self

        def fetchone(self):
            return (content,)

    @contextmanager
    def owned_readonly_connection(*, readonly):
        assert readonly is True
        yield FakeConnection()

    monkeypatch.setattr(postgres_db, "connect", owned_readonly_connection)
    monkeypatch.setattr(
        voice,
        "render_reply",
        lambda _text: pytest.fail("Unvoiceable content must never enter synthesis"),
    )
    target = "12345678-1234-4234-8234-123456789abc"
    with pytest.raises(
        voice.ReplyVoiceContentUnavailable,
        match="reply_voice_content_outside_local_capacity",
    ):
        voice.render_persisted_reply(target, target, target)


def test_missing_owned_reply_remains_a_distinct_fail_closed_error(monkeypatch):
    class MissingConnection:
        def execute(self, _query, _params):
            return self

        def fetchone(self):
            return None

    @contextmanager
    def missing_readonly_connection(*, readonly):
        assert readonly is True
        yield MissingConnection()

    monkeypatch.setattr(postgres_db, "connect", missing_readonly_connection)
    target = "12345678-1234-4234-8234-123456789abc"
    with pytest.raises(ValueError, match="reply_voice_not_owned_or_unrecorded"):
        voice.render_persisted_reply(target, target, target)
