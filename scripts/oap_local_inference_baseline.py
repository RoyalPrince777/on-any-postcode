#!/usr/bin/env python3
"""Bounded, localhost-only Ollama-compatible inference baseline. No external requests."""
from __future__ import annotations

import argparse
import json
import os
import time
from urllib import request
from urllib.parse import urlsplit

PROMPT = "Reply with exactly one word: ready"


def benchmark(url: str, model: str, timeout: float = 90.0) -> dict:
    parsed = urlsplit(url)
    if (parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}
            or parsed.username is not None or parsed.password is not None
            or parsed.port is None or parsed.path != "/api/chat"
            or parsed.query or parsed.fragment):
        raise ValueError("Inference benchmark requires explicit localhost HTTP /api/chat endpoint")
    if not model or len(model) > 128:
        raise ValueError("model name required")
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": PROMPT}],
        "stream": False,
        "options": {"num_ctx": 512, "num_predict": 16, "temperature": 0},
    }).encode()
    req = request.Request(url, data=payload, method="POST",
                          headers={"Content-Type": "application/json"})
    start = time.monotonic()
    with request.build_opener(_NoRedirects).open(req, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError("local inference HTTP failure")
        body = json.loads(response.read(1024 * 1024))
    elapsed = time.monotonic() - start
    if not isinstance(body, dict) or not isinstance(body.get("message"), dict):
        raise ValueError("unexpected local inference response")
    if not isinstance(body["message"].get("content"), str):
        raise ValueError("local inference response missing text")
    tokens = body.get("eval_count")
    duration_ns = body.get("eval_duration")
    rate = (tokens * 1e9 / duration_ns
            if isinstance(tokens, int) and tokens >= 0
            and isinstance(duration_ns, int) and duration_ns > 0 else None)
    return {
        "event": "oap_local_inference_baseline",
        "local_only": True,
        "model": model,
        "elapsed_s": round(elapsed, 3),
        "generation_tokens": tokens if isinstance(tokens, int) and tokens >= 0 else None,
        "generation_tokens_per_s": round(rate, 2) if rate is not None else None,
        "model_reported_duration_ns": duration_ns if isinstance(duration_ns, int) else None,
        "response_received": True,
        "native_acceleration_proven": False,
        "production_ready": False,
    }


class _NoRedirects(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("local inference redirect rejected")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:11434/api/chat")
    parser.add_argument("--model", default=os.environ.get("OAP_INFERENCE_LOCAL_MODEL", "oap-core:latest"))
    args = parser.parse_args()
    print(json.dumps(benchmark(args.url, args.model), sort_keys=True))


if __name__ == "__main__":
    main()
