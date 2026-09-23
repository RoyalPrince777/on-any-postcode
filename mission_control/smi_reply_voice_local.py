"""OAP local reply WAV + synthesis-issued phoneme timing.

Optional self-hosted eSpeak library. Fails closed when not installed.
No remote provider, file writes, telemetry, or persistent reply retention.
"""
from __future__ import annotations

import ctypes
import ctypes.util
import hashlib
import io
import json
import threading
import wave

MAX_TEXT = 1500
MAX_BYTES = 32 * 1024 * 1024
_LOCK = threading.Lock()


class VoiceUnavailable(RuntimeError):
    pass


class _EventId(ctypes.Union):
    _fields_ = [("number", ctypes.c_int), ("name", ctypes.c_char_p), ("string", ctypes.c_char * 8)]


class _Event(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_int), ("unique_identifier", ctypes.c_uint),
        ("text_position", ctypes.c_int), ("length", ctypes.c_int),
        ("audio_position", ctypes.c_int), ("sample", ctypes.c_int),
        ("user_data", ctypes.c_void_p), ("id", _EventId),
    ]


_CB = ctypes.CFUNCTYPE(
    ctypes.c_int, ctypes.POINTER(ctypes.c_short), ctypes.c_int, ctypes.POINTER(_Event)
)


def _viseme(phoneme: str) -> str:
    """Synthesis-issued phoneme -> approximate original-pixel mouth class."""
    value = phoneme.strip().casefold()
    if not value or value.startswith("_") or value in {"0", "-", "pau"}:
        return "silence"
    if value.startswith(("p", "b", "m")):
        return "closed"
    if value.startswith(("w", "o", "u", "@u", "ou")):
        return "round"
    if value.startswith(("f", "v")):
        return "teeth"
    if value.startswith(("t", "d", "l", "n", "s", "z", "th", "dh")):
        return "tongue"
    return "wide"


def render_reply(text: str) -> dict:
    if (
        not isinstance(text, str)
        or not text.strip()
        or len(text) > MAX_TEXT
        or "\x00" in text
    ):
        raise ValueError("reply_voice_text_invalid")
    name = ctypes.util.find_library("espeak")
    if not name:
        raise VoiceUnavailable("local_voice_engine_unavailable")
    with _LOCK:
        library = ctypes.CDLL(name)
        library.espeak_Initialize.argtypes = [
            ctypes.c_int, ctypes.c_int, ctypes.c_char_p, ctypes.c_int
        ]
        library.espeak_Initialize.restype = ctypes.c_int
        library.espeak_SetSynthCallback.argtypes = [_CB]
        library.espeak_SetVoiceByName.argtypes = [ctypes.c_char_p]
        library.espeak_SetVoiceByName.restype = ctypes.c_int
        library.espeak_Synth.argtypes = [
            ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint, ctypes.c_int,
            ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p, ctypes.c_void_p,
        ]
        library.espeak_Synth.restype = ctypes.c_int
        library.espeak_Synchronize.restype = ctypes.c_int
        library.espeak_Terminate.restype = ctypes.c_int
        pcm_chunks: list[bytes] = []
        phonemes: list[tuple[int, str]] = []
        pcm_size = 0
        aborted = False

        @_CB
        def callback(samples, count, events):
            nonlocal aborted, pcm_size
            if bool(samples) and count > 0:
                chunk = ctypes.string_at(samples, count * 2)
                pcm_size += len(chunk)
                if pcm_size > MAX_BYTES:
                    aborted = True
                    return 1
                pcm_chunks.append(chunk)
            if bool(events):
                for index in range(4096):
                    event = events[index]
                    if event.type == 0:
                        break
                    if event.type == 7:
                        symbol = (
                            bytes(event.id.string).split(b"\x00", 1)[0]
                            .decode("ascii", "replace")
                        )
                        phonemes.append((int(event.audio_position), symbol))
            return 0

        rate = library.espeak_Initialize(2, 60, None, 1)
        if not 8000 <= rate <= 48000:
            raise VoiceUnavailable("local_voice_engine_initialization_failed")
        try:
            if library.espeak_SetVoiceByName(b"en") != 0:
                raise VoiceUnavailable("local_english_voice_unavailable")
            library.espeak_SetSynthCallback(callback)
            data = ctypes.create_string_buffer(text.encode("utf-8") + b"\x00")
            if library.espeak_Synth(data, len(data), 0, 1, 0, 1, None, None) != 0:
                raise VoiceUnavailable("local_voice_synthesis_failed")
            if library.espeak_Synchronize() != 0 or aborted:
                raise VoiceUnavailable("local_voice_synthesis_failed")
        finally:
            library.espeak_Terminate()

    pcm = b"".join(pcm_chunks)
    if not pcm or len(pcm) % 2:
        raise VoiceUnavailable("local_voice_pcm_invalid")
    duration_ms = round(len(pcm) / 2 / rate * 1000)
    if not 100 <= duration_ms <= 300000:
        raise VoiceUnavailable("local_voice_duration_invalid")
    with io.BytesIO() as output:
        with wave.open(output, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(rate)
            wav.writeframes(pcm)
        audio_wav = output.getvalue()
    audio_sha = hashlib.sha256(audio_wav).hexdigest()
    cues = [{"atMs": 0, "viseme": "silence", "confidence": 1}]
    last = 0
    for at_ms, symbol in phonemes:
        if not last < at_ms < duration_ms:
            continue
        cues.append({"atMs": at_ms, "viseme": _viseme(symbol), "confidence": 1})
        last = at_ms
    cues.append({"atMs": duration_ms, "viseme": "silence", "confidence": 1})
    if len(cues) < 3 or len(cues) > 10000:
        raise VoiceUnavailable("local_voice_phoneme_timing_invalid")
    canonical = {
        "audioSha256": audio_sha, "audioDurationMs": duration_ms, "cues": cues
    }
    timeline_sha = hashlib.sha256(
        json.dumps(canonical, separators=(",", ":")).encode()
    ).hexdigest()
    return {
        "audio_wav": audio_wav,
        "alignment": {
            "source": "decoded_audio_phoneme_timeline",
            "audioSha256": audio_sha,
            "audioDurationMs": duration_ms,
            "clockSource": "audio-context",
            "audioDecoded": True,
            "predictedFromText": False,
            "storesAudio": False,
            "storesReplyText": False,
            "productionApproved": False,
            "humanFinalApproved": False,
            "maxAlignmentErrorMs": 40,
            "cues": cues,
            "timelineSha256": timeline_sha,
        },
        "engine": "self_hosted_espeak",
        "phonemeIssuedBySynth": True,
        "accurateHumanLipSyncProven": False,
        "fullRigProven": False,
        "retainsAudio": False,
        "externalVoiceProvider": False,
    }


def render_persisted_reply(identity_id: object, conversation_id: object, request_id: object) -> dict:
    """Voice only a committed SMI assistant reply belonging to this signed-in user."""
    import uuid

    from . import postgres_db

    try:
        identity = str(uuid.UUID(str(identity_id)))
        conversation = str(uuid.UUID(str(conversation_id)))
        request_value = str(uuid.UUID(str(request_id)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("reply_voice_target_invalid") from exc
    with postgres_db.connect(readonly=True) as connection:
        row = connection.execute(
            """SELECT m.content FROM smi_messages m
               JOIN smi_conversations c ON c.conversation_id=m.conversation_id
               WHERE m.conversation_id=%s AND m.request_id=%s
                 AND c.identity_id=%s AND m.role='assistant'
               ORDER BY m.created_at DESC LIMIT 1""",
            (conversation, request_value, identity),
        ).fetchone()
    if row is None:
        raise ValueError("reply_voice_not_owned_or_unrecorded")
    return render_reply(str(row[0]))
