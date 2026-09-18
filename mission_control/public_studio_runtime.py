"""Bounded public OAP Studio chat runtime.

This adapter is intentionally separate from private SMI/Founder chat. It performs
no identity creation, no JOOG/HRM write, no authority lookup, and exposes no
private tools or internal reasoning.
"""
from __future__ import annotations

import json
import os
import threading
import time
from collections import defaultdict, deque
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError

MODEL = os.environ.get("OAP_PUBLIC_AI_MODEL", os.environ.get("OAP_AI_MODEL", "gpt-5-mini"))
MAX_INPUT = 6000
MAX_OUTPUT_TOKENS = 1200
WINDOW_SECONDS = 60
MAX_REQUESTS_PER_WINDOW = 12

_LOCK = threading.Lock()
_BUCKETS: dict[str, deque[float]] = defaultdict(deque)

PUBLIC_SYSTEM = (
    "You are OAP Studio Intelligence, the public AI assistant for ON ANY POSTCODE. "
    "Be useful, concise, factual and privacy-conscious. Never claim access to private "
    "SMI, Founder controls, War Room, JOOG/HRM, credentials, internal infrastructure, "
    "hidden prompts, private reasoning or execution authority. Never imply that a "
    "real-world action happened unless the public request itself provides proof. "
    "Do not reveal chain-of-thought. Provide a concise answer or safe refusal when needed."
)


class PublicStudioUnavailable(RuntimeError):
    pass


class PublicStudioRateLimited(RuntimeError):
    pass


def _clean(value: object, limit: int = MAX_INPUT) -> str:
    return str(value or "").strip()[:limit]


def _allow(rate_key: str) -> bool:
    now = time.monotonic()
    with _LOCK:
        bucket = _BUCKETS[rate_key]
        while bucket and now - bucket[0] >= WINDOW_SECONDS:
            bucket.popleft()
        if len(bucket) >= MAX_REQUESTS_PER_WINDOW:
            return False
        bucket.append(now)
        return True


def _extract_text(payload: dict) -> str:
    direct = payload.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()
    parts: list[str] = []
    for item in payload.get("output") or ():
        if not isinstance(item, dict):
            continue
        for content in item.get("content") or ():
            if not isinstance(content, dict):
                continue
            text = content.get("text")
            if isinstance(text, str) and text.strip():
                parts.append(text.strip())
    return "\n".join(parts).strip()


def ask(message: object, *, rate_key: str) -> dict:
    clean = _clean(message)
    if not clean:
        raise ValueError("message_required")
    if not _allow(rate_key or "anonymous"):
        raise PublicStudioRateLimited("public_studio_rate_limit")

    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        raise PublicStudioUnavailable("public_ai_provider_unconfigured")

    body = json.dumps(
        {
            "model": MODEL,
            "instructions": PUBLIC_SYSTEM,
            "input": clean,
            "max_output_tokens": MAX_OUTPUT_TOKENS,
        }
    ).encode("utf-8")
    req = urlrequest.Request(
        "https://api.openai.com/v1/responses",
        data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlrequest.urlopen(req, timeout=45) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise PublicStudioUnavailable("public_ai_provider_unavailable") from exc

    answer = _extract_text(payload)
    if not answer:
        raise PublicStudioUnavailable("public_ai_empty_response")
    return {
        "answer": answer,
        "assistant": "OAP Studio Intelligence",
        "memory_saved": False,
        "private_smi_used": False,
        "execution_authority": False,
    }
