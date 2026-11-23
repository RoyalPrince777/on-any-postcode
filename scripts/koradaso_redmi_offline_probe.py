#!/usr/bin/env python3
"""Read-only Redmi/Termux proof of locally installed Ollama inference.

No model pull, network discovery, remote URL, server startup or credentials.
This does NOT independently verify airplane mode or a production installation.
"""
from __future__ import annotations

import argparse
import json
import time
from urllib import error, request

_TAGS = "http://127.0.0.1:11434/api/tags"
_CHAT = "http://127.0.0.1:11434/api/chat"


def probe_local(model: str, *, timeout: float = 45, opener=None) -> dict[str, object]:
    """Probe exactly two fixed loopback paths, never a caller-provided URL."""
    if not isinstance(model, str) or not model or len(model) > 160 or any(
        c.isspace() or ord(c) < 33 for c in model
    ):
        raise ValueError("invalid_local_model_name")
    if not 3 <= timeout <= 120:
        raise ValueError("timeout_out_of_bounds")
    client = opener or request.build_opener(request.ProxyHandler({}))
    try:
        req = request.Request(_TAGS, headers={"Accept": "application/json"})
        with client.open(req, timeout=5) as response:
            tags = json.load(response)
        models = tags.get("models", []) if isinstance(tags, dict) else []
        installed = isinstance(models, list) and any(
            isinstance(item, dict) and model in (item.get("name"), item.get("model"))
            for item in models
        )
        if not installed:
            return {"status": "not_ready", "reason": "model_not_installed", "local_only": True}
        payload = {
            "model": model, "stream": False, "keep_alive": "0s",
            "messages": [{"role": "user", "content": "Reply with exactly: LOCAL OK"}],
            "options": {"num_predict": 24, "temperature": 0},
        }
        req = request.Request(
            _CHAT, method="POST", data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        started = time.monotonic()
        with client.open(req, timeout=timeout) as response:
            result = json.load(response)
        if not isinstance(result, dict):
            return {"status": "not_ready", "reason": "invalid_local_response", "local_only": True}
        latency = round(time.monotonic() - started, 2)
        answer = (result.get("message") or {}).get("content") or ""
        if not isinstance(answer, str) or not answer.strip():
            return {"status": "not_ready", "reason": "empty_local_response", "local_only": True}
        return {
            "status": "local_inference_passed", "local_only": True,
            "latency_seconds": latency, "response_characters": len(answer),
            "airplane_mode_independently_verified": False,
            "production_ready": False,
        }
    except (error.URLError, error.HTTPError, TimeoutError, OSError,
            json.JSONDecodeError, ValueError, TypeError, KeyError):
        return {"status": "not_ready", "reason": "local_runtime_unavailable", "local_only": True}


def main() -> int:
    parser = argparse.ArgumentParser(description="KORADASO Redmi local inference proof")
    parser.add_argument("--model", required=True, help="Name of a model ALREADY installed on local Ollama")
    parser.add_argument("--timeout", type=float, default=45)
    args = parser.parse_args()
    try:
        result = probe_local(args.model, timeout=args.timeout)
    except ValueError as exc:
        result = {"status": "blocked", "reason": str(exc)}
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("status") == "local_inference_passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
