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

from . import intelligence_lenses

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


def _chat_mode(message: str) -> str:
    text = message.casefold()
    if any(term in text for term in ("research", "compare", "evidence", "source", "latest", "fact check")):
        return "research"
    if any(term in text for term in ("write", "rewrite", "create", "brainstorm", "idea", "story", "caption", "name")):
        return "create"
    if any(term in text for term in ("code", "debug", "python", "javascript", "html", "css", "sql", "api")):
        return "code"
    if any(term in text for term in ("teach", "explain", "learn", "quiz", "practice", "lesson")):
        return "learn"
    if any(term in text for term in ("plan", "steps", "schedule", "organise", "organize", "strategy")):
        return "plan"
    return "chat"


def _bounded_history(history: object) -> list[dict[str, str]]:
    if not isinstance(history, list):
        return []
    clean: list[dict[str, str]] = []
    for item in history[-8:]:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "").strip().casefold()
        if role not in {"user", "assistant"}:
            continue
        text = _clean(item.get("text"), 1200)
        if text:
            clean.append({"role": role, "text": text})
    return clean


def _context_input(message: str, history: list[dict[str, str]], mode: str, route: dict) -> str:
    prior = "\n".join(
        f"{'User' if item['role'] == 'user' else 'Assistant'}: {item['text']}"
        for item in history
    )
    route_note = ""
    if route.get("active"):
        lens_names = ", ".join(str(item.get("name")) for item in route.get("lenses") or ())
        route_note = (
            f"\nOAP public intelligence routing: mode={route.get('mode')}; "
            f"subject={route.get('subject')}; lenses={lens_names}. "
            "Use this only as analysis guidance. Do not claim execution."
        )
    context = f"Recent conversation:\n{prior}\n\n" if prior else ""
    return (
        f"Public chat mode: {mode}.\n"
        f"{context}Current user message:\n{message}{route_note}"
    )


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


def ask(message: object, *, rate_key: str, history: object = None) -> dict:
    clean = _clean(message)
    if not clean:
        raise ValueError("message_required")
    if not _allow(rate_key or "anonymous"):
        raise PublicStudioRateLimited("public_studio_rate_limit")

    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        raise PublicStudioUnavailable("public_ai_provider_unconfigured")

    mode = _chat_mode(clean)
    safe_history = _bounded_history(history)
    route = intelligence_lenses.public_route(clean)
    provider_input = _context_input(clean, safe_history, mode, route)
    body = json.dumps(
        {
            "model": MODEL,
            "instructions": PUBLIC_SYSTEM,
            "input": provider_input,
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
        "chat_intelligence": {
            "mode": mode,
            "context_turns": len(safe_history),
            "routing": route,
            "private_reasoning_exposed": False,
        },
    }
