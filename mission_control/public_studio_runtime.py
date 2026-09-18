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
from . import oap_inference_gateway as smi_inference

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

SPECIALIST_INTELLIGENCE = {
    "research": {"label": "Research Intelligence", "ready": True},
    "creation": {"label": "Creation Intelligence", "ready": True},
    "code": {"label": "Code Intelligence", "ready": True},
    "learning": {"label": "Learning Intelligence", "ready": True},
    "planning": {"label": "Planning Intelligence", "ready": True},
    "language": {"label": "Language Intelligence", "ready": True},
    "location": {"label": "Location Intelligence", "ready": True},
    "movement": {"label": "Movement Intelligence", "ready": True},
    "commerce": {"label": "Commerce Intelligence", "ready": True},
    "creator": {"label": "Creator Intelligence", "ready": True},
    "safety": {"label": "Safety Intelligence", "ready": True},
    "truth": {"label": "Truth-Light Intelligence", "ready": True},
    "tool": {"label": "Tool Intelligence", "ready": True},
    "image": {"label": "Image Intelligence", "ready": False},
    "video": {"label": "Video Intelligence", "ready": False},
    "audio": {"label": "Audio Intelligence", "ready": False},
    "file": {"label": "File Intelligence", "ready": False},
    "voice": {"label": "Voice Intelligence", "ready": False},
}




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


def _specialist_route(message: str) -> dict:
    text = message.casefold()
    rules = (
        ("research", ("research", "evidence", "source", "compare", "fact check", "latest")),
        ("code", ("code", "debug", "python", "javascript", "html", "css", "sql", "api")),
        ("learning", ("teach", "explain", "learn", "quiz", "practice", "lesson")),
        ("planning", ("plan", "steps", "schedule", "organise", "organize", "strategy")),
        ("language", ("translate", "translation", "language", "french", "spanish", "twi", "akan")),
        ("movement", ("route", "travel", "journey", "delivery", "movement", "eta")),
        ("location", ("postcode", "location", "place", "nearby", "borough", "region")),
        ("commerce", ("buy", "sell", "product", "market", "merchant", "price", "checkout")),
        ("creator", ("creator", "campaign", "content strategy", "publish", "audience")),
        ("creation", ("write", "rewrite", "create", "brainstorm", "idea", "story", "caption", "name")),
        ("image", ("image", "photo", "picture", "visual")),
        ("video", ("video", "scene", "animate", "motion")),
        ("audio", ("audio", "music", "sound", "transcribe")),
        ("file", ("pdf", "document", "spreadsheet", "file", "upload")),
        ("voice", ("voice", "speak", "microphone")),
        ("tool", ("tool", "use a tool", "which tool")),
        ("truth", ("true", "truth", "verify", "proven", "uncertain")),
        ("safety", ("safe", "privacy", "security", "harm", "abuse")),
    )
    for key, terms in rules:
        if any(term in text for term in terms):
            item = SPECIALIST_INTELLIGENCE[key]
            return {"id": key, "name": item["label"], "ready": bool(item["ready"])}
    return {"id": "chat", "name": "Chat Intelligence", "ready": True}


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


def _compatibility_engine(
    message: str,
    history: list[dict[str, str]] | None,
    brain: dict | None,
    *,
    code_mode: bool = False,
) -> str:
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        raise PublicStudioUnavailable("public_ai_provider_unconfigured")
    context = {
        "surface": "public",
        "execution_authority": False,
        "private_memory_allowed": False,
        "task_type": (brain or {}).get("task_type"),
        "intelligence_capabilities": (brain or {}).get("intelligence_capabilities", ()),
    }
    items = []
    for item in (history or [])[-8:]:
        role = str(item.get("role") or "")
        content = str(item.get("content") or "")[:2400]
        if role in {"user", "assistant"} and content:
            items.append({"role": role, "content": content})
    prompt = (
        PUBLIC_SYSTEM
        + "\nSMI public routing context: "
        + json.dumps(context, separators=(",", ":"))
        + "\nRecent conversation: "
        + json.dumps(items, separators=(",", ":"))
        + "\nCurrent user message: "
        + message
    )
    body = json.dumps(
        {
            "model": MODEL,
            "instructions": PUBLIC_SYSTEM,
            "input": prompt,
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
    return answer


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

    mode = _chat_mode(clean)
    specialist = _specialist_route(clean)
    safe_history = _bounded_history(history)
    route = intelligence_lenses.public_route(clean)
    provider_input = _context_input(clean, safe_history, mode, route)
    smi_history = [
        {"role": item["role"], "content": item["text"]}
        for item in safe_history
    ]
    brain = {
        "task_type": specialist.get("id"),
        "public_chat_mode": mode,
        "public_intelligence_route": route,
        "execution_authority": False,
    }
    try:
        answer = smi_inference.generate_public(
            _compatibility_engine,
            provider_input,
            smi_history,
            brain,
            code_mode=(mode == "code"),
        )
    except (RuntimeError, PublicStudioUnavailable) as exc:
        raise PublicStudioUnavailable("public_smi_unavailable") from exc

    return {
        "answer": answer,
        "assistant": "OAP Studio Intelligence",
        "brain": "SMI",
        "smi_surface": "public",
        "memory_saved": False,
        "private_smi_used": False,
        "execution_authority": False,
        "chat_intelligence": {
            "mode": mode,
            "specialist": specialist,
            "context_turns": len(safe_history),
            "routing": route,
            "private_reasoning_exposed": False,
        },
    }
