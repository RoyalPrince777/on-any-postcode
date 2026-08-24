"""Bounded multimodal preparation for SMI; raw attachments are never persisted."""
from __future__ import annotations

import base64
import hashlib
import json
import re
import uuid
from typing import Any
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError

MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_VIDEO_FRAMES = 4
MAX_FRAME_BYTES = 1_500_000
DOCUMENT_MIMES = {
    "application/pdf",
    "text/plain",
    "text/markdown",
    "text/csv",
    "application/json",
    "text/html",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}
AUDIO_MIMES = {
    "audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav",
    "audio/mp4", "audio/m4a", "audio/webm", "audio/ogg",
}
IMAGE_MIMES = {"image/jpeg", "image/png", "image/webp"}
_DATA_URL = re.compile(
    r"^data:([a-z0-9.+-]+/[a-z0-9.+-]+);base64,([A-Za-z0-9+/=]+)$",
    re.I,
)


def _safe_name(value: object, fallback: str) -> str:
    name=re.sub(r"[^A-Za-z0-9._ -]+", "_", str(value or ""))[:120].strip(" .")
    return name or fallback


def _decode_data_url(value: object, allowed: set[str], max_bytes: int) -> tuple[str, bytes, str]:
    match=_DATA_URL.fullmatch(str(value or ""))
    if not match:
        raise ValueError("invalid_attachment_data")
    mime=match.group(1).lower()
    if mime not in allowed:
        raise ValueError("unsupported_attachment_type")
    try:
        raw=base64.b64decode(match.group(2), validate=True)
    except ValueError as exc:
        raise ValueError("invalid_attachment_data") from exc
    if not raw or len(raw) > max_bytes:
        raise ValueError("attachment_size_invalid")
    return mime,raw,match.group(2)


def _transcribe_audio(key: str, mime: str, raw: bytes, filename: str) -> str:
    boundary="----oap-smi-"+uuid.uuid4().hex
    parts=[
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"model\"\r\n\r\ngpt-4o-mini-transcribe\r\n".encode(),
        (
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
            f"filename=\"{filename}\"\r\nContent-Type: {mime}\r\n\r\n"
        ).encode()+raw+b"\r\n",
        f"--{boundary}--\r\n".encode(),
    ]
    req=urlrequest.Request(
        "https://api.openai.com/v1/audio/transcriptions",
        data=b"".join(parts),
        headers={
            "Authorization":f"Bearer {key}",
            "Content-Type":f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    try:
        with urlrequest.urlopen(req,timeout=60) as response:
            data=json.loads(response.read().decode())
    except HTTPError as exc:
        raise RuntimeError(f"transcription_http_{exc.code}") from exc
    except (URLError,TimeoutError,json.JSONDecodeError) as exc:
        raise RuntimeError("transcription_unavailable") from exc
    text=str(data.get("text","")).strip()
    if not text:
        raise RuntimeError("transcription_empty")
    return text[:12_000]


def prepare(value: object, key: str) -> dict[str, Any]:
    """Validate and convert one UI attachment into Responses API content blocks."""
    if not value:
        return {
            "kind":None,"filename":None,"content_items":[],"transcript":"",
            "sha256":None,"frame_count":0,"retained":False,
        }
    if not isinstance(value,dict):
        raise ValueError("invalid_attachment")
    kind=str(value.get("kind","")).strip().lower()
    name=_safe_name(value.get("name"),"attachment")
    if kind=="document":
        mime,raw,b64=_decode_data_url(value.get("data"),DOCUMENT_MIMES,MAX_FILE_BYTES)
        return {
            "kind":kind,"filename":name,
            "content_items":[{"type":"input_file","filename":name,"file_data":str(value.get("data"))}],
            "transcript":"","sha256":hashlib.sha256(raw).hexdigest(),
            "frame_count":0,"retained":False,"mime":mime,
        }
    if kind=="audio":
        mime,raw,_=_decode_data_url(value.get("data"),AUDIO_MIMES,MAX_FILE_BYTES)
        transcript=_transcribe_audio(key,mime,raw,name)
        return {
            "kind":kind,"filename":name,"content_items":[],
            "transcript":transcript,"sha256":hashlib.sha256(raw).hexdigest(),
            "frame_count":0,"retained":False,"mime":mime,
        }
    if kind=="video":
        frames=value.get("frames")
        if not isinstance(frames,list) or not 1 <= len(frames) <= MAX_VIDEO_FRAMES:
            raise ValueError("video_frames_invalid")
        content_items=[];digests=[]
        for frame in frames:
            _,raw,_=_decode_data_url(frame,IMAGE_MIMES,MAX_FRAME_BYTES)
            content_items.append({"type":"input_image","image_url":frame,"detail":"low"})
            digests.append(hashlib.sha256(raw).hexdigest())
        return {
            "kind":kind,"filename":name,"content_items":content_items,
            "transcript":"","sha256":hashlib.sha256("".join(digests).encode()).hexdigest(),
            "frame_count":len(frames),"retained":False,"mime":"video/sampled-frames",
        }
    raise ValueError("unsupported_attachment_kind")
