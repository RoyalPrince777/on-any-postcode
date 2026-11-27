#!/usr/bin/env python3
"""Founder-invoked local model quality check. No DB, bridge, tools or fallback."""
import argparse
import hashlib
import json
import re
import statistics
import time
import unittest
from datetime import datetime, timezone
from urllib import request
from unittest.mock import patch

BASE = "http://127.0.0.1:11434"
CASES = (
    ("instruction", "Output only the word READY.", "READY"),
    ("arithmetic", "What is 17 + 28? Output only the integer.", "45"),
    ("retrieval", "Record: the workshop closes at 18:00. What time does it close? Output only the time HH:MM.", "18:00"),
    ("abstention", "Record: Ada owns a bicycle. Its colour is not stated. What colour is it? If not stated output UNKNOWN. Output only the answer.", "UNKNOWN"),
    ("format", 'Return only a JSON object with the key "ready" and boolean value true.', {"ready": True}),
)
MAX_BYTES = 262144
MODEL_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}")

class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None

def local_json(path, payload=None, timeout=30):
    if path not in ("/api/tags", "/api/chat"):
        raise ValueError("unsupported_path")
    data = None if payload is None else json.dumps(payload).encode()
    req = request.Request(BASE + path, data=data,
                          headers={"Content-Type": "application/json"})
    opener = request.build_opener(request.ProxyHandler({}), NoRedirect())
    with opener.open(req, timeout=timeout) as response:
        raw = response.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("response_too_large")
    body = json.loads(raw)
    if not isinstance(body, dict):
        raise ValueError("invalid_response")
    return body

def correct(answer, expected):
    if isinstance(expected, dict):
        try:
            obj = json.loads(answer)
        except (ValueError, TypeError):
            return False
        return (isinstance(obj, dict) and set(obj) == {"ready"}
                and obj["ready"] is True)
    return answer.strip() == expected

def sample(model, case, timeout):
    name, prompt, expected = case
    start = time.monotonic()
    row = {"case": name, "completed": False, "correct": False}
    try:
        body = local_json("/api/chat", {
            "model": model, "messages": [{"role": "user", "content": prompt}],
            "stream": False, "options": {"temperature": 0, "seed": 42,
                                        "num_ctx": 1024, "num_predict": 32},
        }, timeout)
        message = body.get("message")
        answer = message.get("content") if isinstance(message, dict) else None
        tokens = body.get("eval_count")
        if (body.get("model") != model or body.get("done") is not True
                or body.get("done_reason") == "length"
                or not isinstance(answer, str) or not answer.strip()
                or type(tokens) is not int or not 0 < tokens <= 32):
            raise ValueError("invalid_completion")
        row.update(completed=True, correct=correct(answer, expected),
                   response_sha256=hashlib.sha256(answer.strip().encode()).hexdigest(),
                   reported_output_tokens=tokens)
        duration = body.get("eval_duration")
        if type(duration) is int and duration > 0:
            row["reported_tokens_per_second"] = round(tokens * 1e9 / duration, 3)
    except Exception as exc:
        # Never persist raw responses, prompts, host details or exception messages.
        row["error_type"] = type(exc).__name__
    row["elapsed_ms"] = round((time.monotonic() - start) * 1000, 3)
    return row

def benchmark(models, repeats=2, timeout=30):
    if (not 1 <= len(models) <= 2 or len(set(models)) != len(models)
            or any(not MODEL_PATTERN.fullmatch(m) for m in models)
            or not 1 <= repeats <= 2 or not 1 <= timeout <= 120):
        raise ValueError("invalid_benchmark_parameters")
    receipt = {"schema": "oap.smi.local_quality.v1",
               "started_at": datetime.now(timezone.utc).isoformat(),
               "suite_sha256": hashlib.sha256(json.dumps(CASES).encode()).hexdigest(),
               "external_fallback_used": False, "production_approved": False,
               "independent_verification": False, "models": [],
               "recommendation": None}
    try:
        tags = local_json("/api/tags", timeout=min(timeout, 10)).get("models")
        if not isinstance(tags, list):
            raise ValueError("invalid_model_inventory")
        inventory = {item.get("name"): item.get("digest") for item in tags
                     if isinstance(item, dict) and isinstance(item.get("name"), str)}
    except Exception as exc:
        return {**receipt, "status": "blocked", "reason": type(exc).__name__}
    for model in models:
        if model not in inventory:
            receipt["models"].append({"model": model, "status": "blocked",
                                      "reason": "model_not_installed"})
            continue
        rows = [dict(sample(model, case, timeout), repetition=i + 1)
                for i in range(repeats) for case in CASES]
        completed = [row for row in rows if row["completed"]]
        digest = inventory[model]
        receipt["models"].append({
            "model": model, "status": "observed", "reported_digest": digest
                if isinstance(digest, str) and re.fullmatch(r"[a-f0-9]{64}", digest) else None,
            "attempted": len(rows), "completed": len(completed),
            "correct": sum(row["correct"] for row in rows),
            "median_completed_ms": round(statistics.median(
                row["elapsed_ms"] for row in completed), 3) if completed else None,
            "repeat_consistency": None if repeats == 1 else sum(
                rows[j]["completed"] and rows[j+len(CASES)]["completed"]
                and rows[j]["response_sha256"] == rows[j+len(CASES)]["response_sha256"]
                for j in range(len(CASES))),
            "samples": rows,
        })
    receipt["finished_at"] = datetime.now(timezone.utc).isoformat()
    eligible = [m for m in receipt["models"] if m.get("completed") == len(CASES)*repeats
                and m.get("correct") == len(CASES)*repeats
                and repeats == 2 and m.get("repeat_consistency") == len(CASES)]
    # Do not choose a winner if any candidate was unavailable or incomplete.
    if len(models) == 2 and all(m.get("completed") == len(CASES)*repeats
                               for m in receipt["models"]) and eligible:
        best = min(eligible, key=lambda m: m["median_completed_ms"])
        receipt["recommendation"] = {"model": best["model"],
            "scope": "small_fixed_suite_only", "automatic_switch": False}
    receipt["status"] = "incomplete" if all(m.get("completed") == len(CASES)*repeats
                                         for m in receipt["models"]) else "blocked"
    return receipt

class Checks(unittest.TestCase):
    def test_exact(self):
        self.assertTrue(correct(" READY\n", "READY"))
        self.assertFalse(correct("NOT READY", "READY"))
    def test_json(self):
        self.assertTrue(correct('{"ready":true}', {"ready": True}))
        for bad in ('{"ready":1}', '{"ready":true,"extra":0}', 'yes'):
            self.assertFalse(correct(bad, {"ready": True}))
    def test_invalid_completion(self):
        with patch(__name__ + ".local_json", return_value={"done": True}):
            self.assertFalse(sample("a", CASES[0], 1)["completed"])
    def test_wrong_answer(self):
        with patch(__name__ + ".local_json", return_value={"model": "a", "done": True,
                   "message": {"content": "WRONG"}, "eval_count": 1}):
            row = sample("a", CASES[0], 1)
        self.assertTrue(row["completed"])
        self.assertFalse(row["correct"])
        self.assertNotIn("content", row)
    def test_missing_model(self):
        with patch(__name__ + ".local_json", return_value={"models": []}):
            out = benchmark(["a"])
        self.assertEqual(out["status"], "blocked")
        self.assertIsNone(out["recommendation"])
    def test_offline(self):
        with patch(__name__ + ".local_json", side_effect=TimeoutError):
            self.assertEqual(benchmark(["a"])["status"], "blocked")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", action="append")
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(Checks)
        return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1
    result = benchmark(args.model or ["oap-core:latest"], args.repeats, args.timeout)
    print(json.dumps(result, indent=2))
    return 2 if result["status"] == "blocked" else 0

if __name__ == "__main__":
    raise SystemExit(main())
