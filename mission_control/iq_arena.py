"""First-party OAP IQ Arena challenge engine.

This is a bounded skills challenge, not a clinical or psychometric IQ test.
It reports a seven-domain skill profile only.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import uuid
from typing import Any

SCHEMA = "oap.arena.iq.v1"
SESSION_KEY = "oap_iq_arena_v1"
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$")

DOMAINS = ("Logic", "Patterns", "Memory", "Spatial", "Numbers", "Language", "Strategy")

QUESTIONS = (
    {"id":"logic-1","domain":"Logic","prompt":"All Falcons are birds. Some birds migrate. Which statement must be true?","choices":[{"id":"a","label":"All Falcons migrate"},{"id":"b","label":"Falcons are birds"},{"id":"c","label":"No birds migrate"}],"answer":"b"},
    {"id":"patterns-1","domain":"Patterns","prompt":"What comes next: 2, 4, 8, 16, ?","choices":[{"id":"a","label":"18"},{"id":"b","label":"24"},{"id":"c","label":"32"}],"answer":"c"},
    {"id":"memory-1","domain":"Memory","prompt":"Remember this sequence: 7 · 2 · 9 · 4. Which is correct?","choices":[{"id":"a","label":"7 · 2 · 9 · 4"},{"id":"b","label":"7 · 9 · 2 · 4"},{"id":"c","label":"4 · 9 · 2 · 7"}],"answer":"a"},
    {"id":"spatial-1","domain":"Spatial","prompt":"A square is rotated 90°. What changes?","choices":[{"id":"a","label":"Its shape"},{"id":"b","label":"Its orientation"},{"id":"c","label":"Its number of sides"}],"answer":"b"},
    {"id":"numbers-1","domain":"Numbers","prompt":"If 3 routes each connect 4 hubs, how many route-to-hub links are counted?","choices":[{"id":"a","label":"7"},{"id":"b","label":"12"},{"id":"c","label":"16"}],"answer":"b"},
    {"id":"language-1","domain":"Language","prompt":"Which word is closest in meaning to 'adapt'?","choices":[{"id":"a","label":"Adjust"},{"id":"b","label":"Freeze"},{"id":"c","label":"Repeat"}],"answer":"a"},
    {"id":"strategy-1","domain":"Strategy","prompt":"You control two connected territories and one isolated territory. Which move best improves network strength?","choices":[{"id":"a","label":"Connect the isolated territory"},{"id":"b","label":"Ignore all routes"},{"id":"c","label":"Remove an existing connection"}],"answer":"a"},
)

def _canonical(value: object) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True, ensure_ascii=False)

def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()

def _seal(state: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(state)
    out.pop("checkpoint", None)
    out["checkpoint"] = _digest(out)
    return out

def _valid_request_id(value: object) -> str:
    result = str(value or "").strip()
    if not REQUEST_ID_PATTERN.fullmatch(result):
        raise ValueError("iq_arena_request_id_invalid")
    return result

def new_session() -> dict[str, Any]:
    state = {
        "schema": SCHEMA,
        "session_id": str(uuid.uuid4()),
        "status": "active",
        "index": 0,
        "score": 0,
        "domain_scores": {domain: 0 for domain in DOMAINS},
        "answered": [],
        "request_receipts": [],
    }
    return _seal(state)

def validate(state: object) -> dict[str, Any]:
    if not isinstance(state, dict):
        return {"passed": False, "errors": ["iq_arena_state_missing"]}
    errors: list[str] = []
    if state.get("schema") != SCHEMA:
        errors.append("iq_arena_schema_invalid")
    if state.get("status") not in {"active", "stopped", "completed"}:
        errors.append("iq_arena_status_invalid")
    index = state.get("index")
    if not isinstance(index, int) or not 0 <= index <= len(QUESTIONS):
        errors.append("iq_arena_index_invalid")
    expected = copy.deepcopy(state)
    expected.pop("checkpoint", None)
    if state.get("checkpoint") != _digest(expected):
        errors.append("iq_arena_checkpoint_invalid")
    return {"passed": not errors, "errors": errors}

def _validated_copy(state: object) -> dict[str, Any]:
    check = validate(state)
    if not check["passed"]:
        raise ValueError(check["errors"][0])
    return copy.deepcopy(state)

def public_state(state: dict[str, Any] | None) -> dict[str, Any]:
    if state is None:
        return {"started": False, "status": "idle"}
    check = validate(state)
    if not check["passed"]:
        raise ValueError(check["errors"][0])
    q = None
    if state["status"] == "active" and state["index"] < len(QUESTIONS):
        src = QUESTIONS[state["index"]]
        q = {"id": src["id"], "domain": src["domain"], "prompt": src["prompt"], "choices": copy.deepcopy(src["choices"]), "number": state["index"] + 1}
    return {
        "started": True,
        "session_id": state["session_id"],
        "status": state["status"],
        "score": state["score"],
        "answered": state["index"],
        "total": len(QUESTIONS),
        "question": q,
        "domain_scores": copy.deepcopy(state["domain_scores"]),
        "skill_profile_only": True,
        "clinical_iq_score": False,
        "diagnostic_use": False,
        "payments": False,
    }

def answer(state: object, *, question_id: object, choice_id: object, request_id: object) -> dict[str, Any]:
    current = _validated_copy(state)
    req = _valid_request_id(request_id)
    for item in current["request_receipts"]:
        if item["request_id"] == req:
            return current
    if current["status"] != "active":
        raise ValueError(f"iq_arena_session_{current['status']}")
    if current["index"] >= len(QUESTIONS):
        raise ValueError("iq_arena_session_completed")
    q = QUESTIONS[current["index"]]
    if str(question_id or "") != q["id"]:
        raise ValueError("iq_arena_question_mismatch")
    choice = str(choice_id or "")
    if choice not in {item["id"] for item in q["choices"]}:
        raise ValueError("iq_arena_choice_invalid")
    correct = choice == q["answer"]
    if correct:
        current["score"] += 1
        current["domain_scores"][q["domain"]] += 1
    current["answered"].append({"question_id": q["id"], "choice_id": choice, "correct": correct})
    current["request_receipts"].append({"request_id": req, "action": "answer"})
    current["index"] += 1
    if current["index"] == len(QUESTIONS):
        current["status"] = "completed"
    return _seal(current)

def stop(state: object, *, request_id: object) -> dict[str, Any]:
    current = _validated_copy(state)
    req = _valid_request_id(request_id)
    for item in current["request_receipts"]:
        if item["request_id"] == req:
            return current
    if current["status"] != "active":
        raise ValueError("iq_arena_stop_denied")
    current["status"] = "stopped"
    current["request_receipts"].append({"request_id": req, "action": "stop"})
    return _seal(current)
