"""Governed OAP Studio media-generation provider adapter.

Provider calls are optional execution backends, never authority. Missing credentials,
unsupported inputs, provider errors, and incomplete video jobs fail closed. Secret
values and raw prompts are never returned by status().
"""
from __future__ import annotations

import base64
import json
import os
import uuid
from typing import Any
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError

OPENAI_BASE_URL = "https://api.openai.com/v1"
IMAGE_MODEL = os.environ.get("OAP_STUDIO_IMAGE_MODEL", "gpt-image-2").strip() or "gpt-image-2"
VIDEO_MODEL = os.environ.get("OAP_STUDIO_VIDEO_MODEL", "sora-2").strip() or "sora-2"
MAX_IMAGE_BYTES = 20 * 1024 * 1024


def _key() -> str:
    return os.environ.get("OPENAI_API_KEY", "").strip()


def status() -> dict[str, Any]:
    configured = bool(_key())
    return {
        "provider": "openai",
        "configured": configured,
        "image_model": IMAGE_MODEL,
        "video_model": VIDEO_MODEL,
        "imagine_ready": configured,
        "scene_builder_ready": configured,
        "bring_alive_ready": configured,
        "provider_is_authority": False,
        "execution_authority_expanded": False,
        "human_authority_final": True,
    }


def _json_call(path: str, payload: dict[str, Any], *, method: str = "POST") -> dict[str, Any]:
    key = _key()
    if not key:
        raise RuntimeError("studio_generation_provider_unconfigured")
    req = urlrequest.Request(
        OPENAI_BASE_URL + path,
        data=json.dumps(payload).encode("utf-8") if method != "GET" else None,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method=method,
    )
    try:
        with urlrequest.urlopen(req, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        raise RuntimeError("studio_generation_provider_unavailable") from exc


def _multipart_call(path: str, fields: dict[str, str], *, file_field: tuple[str, str, str, bytes] | None = None) -> dict[str, Any]:
    key = _key()
    if not key:
        raise RuntimeError("studio_generation_provider_unconfigured")
    boundary = "oapstudio" + uuid.uuid4().hex
    body = bytearray()
    for name, value in fields.items():
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        body.extend(str(value).encode("utf-8"))
        body.extend(b"\r\n")
    if file_field is not None:
        name, filename, mime, raw = file_field
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(
            f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode()
        )
        body.extend(f"Content-Type: {mime}\r\n\r\n".encode())
        body.extend(raw)
        body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode())
    req = urlrequest.Request(
        OPENAI_BASE_URL + path,
        data=bytes(body),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    try:
        with urlrequest.urlopen(req, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        raise RuntimeError("studio_generation_provider_unavailable") from exc


def generate_image(prompt: str, *, size: str = "1024x1024") -> dict[str, Any]:
    clean = str(prompt or "").strip()[:4000]
    if not clean:
        raise ValueError("studio_prompt_required")
    payload = _json_call(
        "/images/generations",
        {"model": IMAGE_MODEL, "prompt": clean, "size": size},
    )
    data = payload.get("data") or []
    first = data[0] if data and isinstance(data[0], dict) else {}
    b64 = str(first.get("b64_json") or "")
    if not b64:
        raise RuntimeError("studio_generation_artifact_missing")
    return {
        "kind": "image",
        "model": IMAGE_MODEL,
        "mime_type": "image/png",
        "b64_json": b64,
        "artifact_proven": True,
        "provider_is_authority": False,
    }


def _decode_image_data_url(value: str) -> tuple[str, bytes]:
    clean = str(value or "").strip()
    if not clean.startswith("data:image/") or ";base64," not in clean:
        raise ValueError("studio_source_image_data_required")
    header, encoded = clean.split(",", 1)
    mime = header[5:].split(";", 1)[0].lower()
    if mime not in {"image/png", "image/jpeg", "image/webp"}:
        raise ValueError("studio_source_image_type_unsupported")
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (ValueError, TypeError) as exc:
        raise ValueError("studio_source_image_invalid") from exc
    if not raw or len(raw) > MAX_IMAGE_BYTES:
        raise ValueError("studio_source_image_invalid")
    return mime, raw


def create_video(prompt: str, *, source_image_data: str = "", seconds: str = "4", size: str = "720x1280") -> dict[str, Any]:
    clean = str(prompt or "").strip()[:4000]
    if not clean:
        raise ValueError("studio_prompt_required")
    file_field = None
    if source_image_data:
        mime, raw = _decode_image_data_url(source_image_data)
        suffix = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}[mime]
        file_field = ("input_reference", f"oap-studio-reference.{suffix}", mime, raw)
    payload = _multipart_call(
        "/videos",
        {"model": VIDEO_MODEL, "prompt": clean, "seconds": seconds, "size": size},
        file_field=file_field,
    )
    video_id = str(payload.get("id") or "")
    state = str(payload.get("status") or "")
    if not video_id:
        raise RuntimeError("studio_generation_job_missing")
    return {
        "kind": "video_job",
        "id": video_id,
        "model": str(payload.get("model") or VIDEO_MODEL),
        "status": state,
        "progress": int(payload.get("progress") or 0),
        "artifact_proven": state == "completed",
        "provider_is_authority": False,
    }


def video_status(video_id: str) -> dict[str, Any]:
    clean_id = str(video_id or "").strip()
    if not clean_id.startswith("video_"):
        raise ValueError("studio_video_id_invalid")
    payload = _json_call(f"/videos/{clean_id}", {}, method="GET")
    state = str(payload.get("status") or "")
    return {
        "kind": "video_job",
        "id": clean_id,
        "model": str(payload.get("model") or VIDEO_MODEL),
        "status": state,
        "progress": int(payload.get("progress") or 0),
        "artifact_proven": state == "completed",
        "content_path": f"/videos/{clean_id}/content" if state == "completed" else None,
        "provider_is_authority": False,
    }
