"""Bounded first-party OAP Arena Challenge Engine.

This module is the first executable Arena slice.  It deliberately stays
non-ranked, session-scoped and payment-free while proving server-authoritative
rules, idempotent answers, STOP, audit receipts and recovery validation.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import uuid
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

ARENA_ID = "oap-arena"
ARENA_NAME = "OAP Arena"
CANONICAL_ORGAN_ID = "arena"
SESSION_SCHEMA = "oap.arena.challenge-session.v1"
SESSION_KEY = "oap_arena_challenge_v1"
MAX_REQUEST_RECEIPTS = 21
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$")

PROGRESSION = (
    "Postcode",
    "Borough / Region",
    "Country",
    "Continent",
    "Global Arena",
)

INTELLIGENCE_LAYERS = (
    {
        "id": "game",
        "name": "Game Intelligence",
        "purpose": "Owns rules, state, choices, scoring and recovery.",
    },
    {
        "id": "competition",
        "name": "Competition Intelligence",
        "purpose": "Prepares fair divisions, fixtures, rankings and progression.",
    },
    {
        "id": "civilisation",
        "name": "Civilization Intelligence",
        "purpose": "Keeps culture, language, dignity and local context intact.",
    },
    {
        "id": "distribution",
        "name": "Distribution Intelligence",
        "purpose": "Routes authorised Arena outputs across owned OAP surfaces.",
    },
    {
        "id": "learning",
        "name": "Learning Intelligence",
        "purpose": "Measures outcomes and proposes bounded improvements.",
    },
    {
        "id": "signals",
        "name": "A7 Signal Intelligence",
        "purpose": "Requires provenance and corroboration before real-life claims.",
    },
    {
        "id": "governance",
        "name": "Governed Autonomy",
        "purpose": "Keeps STOP, recovery and Human Authority final.",
    },
)

CHALLENGE_CATALOG: tuple[dict[str, Any], ...] = (
    {
        "id": "arena-progression",
        "category": "Competition",
        "prompt": "Which path takes an OAP Arena champion from local to global?",
        "choices": (
            {"id": "a", "label": "Postcode → Region → Country → Continent → Global"},
            {"id": "b", "label": "Followers → Sponsors → Country → Global"},
            {"id": "c", "label": "Market → Media → Postcode → Global"},
        ),
        "correct_choice_id": "a",
        "explanation": "Arena progression begins with place and proven results, not popularity or spending.",
    },
    {
        "id": "proof-before-green",
        "category": "Evidence",
        "prompt": "When may a live Arena signal be labelled A7?",
        "choices": (
            {"id": "a", "label": "As soon as one person posts it"},
            {"id": "b", "label": "After provenance, corroboration, context and governance checks"},
            {"id": "c", "label": "Whenever the prediction sounds likely"},
        ),
        "correct_choice_id": "b",
        "explanation": "A7 is a governed evidence standard, not a confidence slogan.",
    },
    {
        "id": "rights-gate",
        "category": "Distribution",
        "prompt": "What must happen before an Arena replay is distributed?",
        "choices": (
            {"id": "a", "label": "Rights, territory and youth-visibility checks pass"},
            {"id": "b", "label": "The event receives enough reactions"},
            {"id": "c", "label": "A sponsor requests it"},
        ),
        "correct_choice_id": "a",
        "explanation": "Distribution stays locked when rights or safeguarding evidence is missing.",
    },
    {
        "id": "fair-ranking",
        "category": "Fairness",
        "prompt": "What should determine an official competitive ranking?",
        "choices": (
            {"id": "a", "label": "Spending and follower count"},
            {"id": "b", "label": "Verified results under published rules"},
            {"id": "c", "label": "Private organiser preference"},
        ),
        "correct_choice_id": "b",
        "explanation": "Rank is earned through verified competition evidence, not wealth or private favour.",
    },
    {
        "id": "stop-boundary",
        "category": "Safety",
        "prompt": "What happens when STOP is activated for this challenge?",
        "choices": (
            {"id": "a", "label": "The current session becomes terminal until a new session starts"},
            {"id": "b", "label": "The game continues silently"},
            {"id": "c", "label": "The score is automatically published"},
        ),
        "correct_choice_id": "a",
        "explanation": "STOP fails closed. Resume is only available after a normal pause.",
    },
    {
        "id": "civilization-rule",
        "category": "Civilization",
        "prompt": "How should OAP Arena handle local culture in global competition?",
        "choices": (
            {"id": "a", "label": "Replace every tradition with one global default"},
            {"id": "b", "label": "Preserve local meaning while applying shared safety and fairness rules"},
            {"id": "c", "label": "Rank cultures from strongest to weakest"},
        ),
        "correct_choice_id": "b",
        "explanation": "Born Local · Built Global means local identity remains intact inside shared governance.",
    },
    {
        "id": "improvement-rule",
        "category": "Learning",
        "prompt": "How may Game Intelligence improve an active ranked competition?",
        "choices": (
            {"id": "a", "label": "Secretly rewrite the rules mid-match"},
            {"id": "b", "label": "Measure outcomes and propose a versioned change for later approval"},
            {"id": "c", "label": "Give the leading player an easier final round"},
        ),
        "correct_choice_id": "b",
        "explanation": "Learning proposes governed future improvements; it does not manipulate an active contest.",
    },
)

PUBLIC_BOUNDARY = {
    "ranked_results": False,
    "durable_player_profile": False,
    "multiplayer": False,
    "payments": False,
    "prizes": False,
    "external_distribution": False,
    "live_a7_feeds": False,
    "precise_location": False,
    "biometrics": False,
}


def _canonical(value: object) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True, ensure_ascii=False)


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def validate_catalog(
    catalog: tuple[Mapping[str, Any], ...] = CHALLENGE_CATALOG,
    layers: tuple[Mapping[str, Any], ...] = INTELLIGENCE_LAYERS,
    boundary: Mapping[str, bool] = PUBLIC_BOUNDARY,
) -> dict[str, Any]:
    errors: list[str] = []
    question_ids = [str(item.get("id", "")) for item in catalog]
    layer_ids = [str(item.get("id", "")) for item in layers]
    if len(question_ids) != len(set(question_ids)) or any(not item for item in question_ids):
        errors.append("Arena question IDs must be unique and non-empty")
    if len(layer_ids) != len(set(layer_ids)) or len(layer_ids) != 7:
        errors.append("Arena requires seven unique intelligence layers")
    for question in catalog:
        choices = tuple(question.get("choices") or ())
        choice_ids = [str(item.get("id", "")) for item in choices]
        if not 2 <= len(choices) <= 5 or len(choice_ids) != len(set(choice_ids)):
            errors.append(f"Invalid choices for {question.get('id')}")
        if str(question.get("correct_choice_id", "")) not in choice_ids:
            errors.append(f"Missing correct choice for {question.get('id')}")
    if not boundary or any(value is not False for value in boundary.values()):
        errors.append("Arena v1 public boundaries must remain locked")
    return {
        "passed": not errors,
        "errors": errors,
        "checks": {
            "questions": len(catalog),
            "intelligence_layers": len(layers),
            "progression_levels": len(PROGRESSION),
            "live_a7_feeds": 0,
            "external_execution_edges": 0,
        },
    }


def status() -> dict[str, Any]:
    validation = validate_catalog()
    return {
        "id": ARENA_ID,
        "name": ARENA_NAME,
        "organ_id": CANONICAL_ORGAN_ID,
        "ready": bool(validation["passed"]),
        "mode": "playable_session_scoped_non_ranked_challenge",
        "server_authoritative_rules": True,
        "idempotent_answers": True,
        "stop_enabled": True,
        "pause_resume_enabled": True,
        "audit_receipts": True,
        "checkpoint_recovery": True,
        "durable_persistence": False,
        "ranked_results": False,
        "multiplayer": False,
        "live_a7_feeds": False,
        "external_execution": False,
        "payments": False,
        "human_authority_final": True,
        "no_fake_green": True,
    }


def _receipt(previous_hash: str, action: str, detail: Mapping[str, Any]) -> dict[str, Any]:
    record = {
        "id": str(uuid.uuid4()),
        "at": datetime.now(UTC).isoformat(),
        "action": action,
        "detail": dict(detail),
        "previous_hash": previous_hash,
    }
    return {**record, "hash": _digest(record)}


def _unsealed(state: Mapping[str, Any]) -> dict[str, Any]:
    return {key: copy.deepcopy(value) for key, value in state.items() if key != "checkpoint"}


def _seal(state: Mapping[str, Any]) -> dict[str, Any]:
    result = _unsealed(state)
    result["checkpoint"] = _digest(result)
    return result


def _append_receipt(state: dict[str, Any], action: str, detail: Mapping[str, Any]) -> None:
    receipts = state.setdefault("receipts", [])
    previous_hash = str(receipts[-1]["hash"]) if receipts else "GENESIS"
    receipts.append(_receipt(previous_hash, action, detail))


def _request_record(state: dict[str, Any], record: Mapping[str, Any]) -> None:
    records = state.setdefault("request_receipts", [])
    records.append(dict(record))
    del records[:-MAX_REQUEST_RECEIPTS]


def _request_result(state: Mapping[str, Any], request_id: str) -> dict[str, Any] | None:
    for item in reversed(tuple(state.get("request_receipts") or ())):
        if item.get("request_id") == request_id:
            return dict(item)
    return None


def _valid_request_id(value: object) -> str:
    request_id = str(value or "").strip()
    if not REQUEST_ID_PATTERN.fullmatch(request_id):
        raise ValueError("invalid_request_id")
    return request_id


def _question(question_id: str) -> dict[str, Any]:
    for item in CHALLENGE_CATALOG:
        if item["id"] == question_id:
            return item
    raise ValueError("unknown_question")


def _answer_feedback(record: Mapping[str, Any]) -> dict[str, Any]:
    question = _question(str(record.get("question_id", "")))
    choices = {item["id"]: item["label"] for item in question["choices"]}
    return {
        "request_id": record.get("request_id"),
        "question_id": question["id"],
        "correct": bool(record.get("correct")),
        "selected_choice_id": record.get("selected_choice_id"),
        "correct_choice_id": question["correct_choice_id"],
        "correct_label": choices[question["correct_choice_id"]],
        "explanation": question["explanation"],
    }


def verify_receipt_chain(state: Mapping[str, Any]) -> bool:
    previous_hash = "GENESIS"
    for item in tuple(state.get("receipts") or ()):
        record = {key: value for key, value in item.items() if key != "hash"}
        if record.get("previous_hash") != previous_hash:
            return False
        if item.get("hash") != _digest(record):
            return False
        previous_hash = str(item["hash"])
    return True


def validate_session(state: object) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(state, dict):
        return {"passed": False, "errors": ["arena_session_missing"]}
    if state.get("schema") != SESSION_SCHEMA:
        errors.append("arena_session_schema_invalid")
    if state.get("status") not in {"active", "paused", "stopped", "completed"}:
        errors.append("arena_session_status_invalid")
    index = state.get("question_index")
    score = state.get("score")
    answered = state.get("answered")
    if not isinstance(index, int) or not 0 <= index <= len(CHALLENGE_CATALOG):
        errors.append("arena_question_index_invalid")
    if not isinstance(score, int) or not 0 <= score <= len(CHALLENGE_CATALOG):
        errors.append("arena_score_invalid")
    if not isinstance(answered, list) or len(answered) != (index if isinstance(index, int) else -1):
        errors.append("arena_answer_history_invalid")
    if state.get("status") == "completed" and index != len(CHALLENGE_CATALOG):
        errors.append("arena_completion_invalid")
    if len(tuple(state.get("request_receipts") or ())) > MAX_REQUEST_RECEIPTS:
        errors.append("arena_request_receipts_unbounded")
    if not verify_receipt_chain(state):
        errors.append("arena_receipt_chain_invalid")
    expected = _digest(_unsealed(state))
    if state.get("checkpoint") != expected:
        errors.append("arena_checkpoint_invalid")
    return {"passed": not errors, "errors": errors}


def new_session() -> dict[str, Any]:
    state: dict[str, Any] = {
        "schema": SESSION_SCHEMA,
        "session_id": str(uuid.uuid4()),
        "owner_scope": "signed_browser_session",
        "status": "active",
        "question_index": 0,
        "score": 0,
        "answered": [],
        "request_receipts": [],
        "receipts": [],
    }
    _append_receipt(state, "session_started", {"ranked": False, "durable": False})
    return _seal(state)


def _validated_copy(state: object) -> dict[str, Any]:
    validation = validate_session(state)
    if not validation["passed"]:
        raise ValueError(str(validation["errors"][0]))
    return copy.deepcopy(state)


def public_state(
    state: Mapping[str, Any] | None,
    *,
    feedback: Mapping[str, Any] | None = None,
    duplicate: bool = False,
) -> dict[str, Any]:
    if state is None:
        return {
            "started": False,
            "status": "idle",
            "score": 0,
            "answered": 0,
            "total": len(CHALLENGE_CATALOG),
            "question": None,
            "feedback": None,
            "duplicate": False,
        }
    validation = validate_session(dict(state))
    if not validation["passed"]:
        raise ValueError(str(validation["errors"][0]))
    index = int(state["question_index"])
    question = None
    if index < len(CHALLENGE_CATALOG) and state["status"] not in {"stopped", "completed"}:
        source = CHALLENGE_CATALOG[index]
        question = {
            "id": source["id"],
            "category": source["category"],
            "prompt": source["prompt"],
            "choices": tuple(dict(item) for item in source["choices"]),
            "number": index + 1,
        }
    receipts = tuple(state.get("receipts") or ())
    return {
        "started": True,
        "session_id": state["session_id"],
        "status": state["status"],
        "score": state["score"],
        "answered": index,
        "total": len(CHALLENGE_CATALOG),
        "question": question,
        "feedback": dict(feedback) if feedback else None,
        "duplicate": duplicate,
        "ranked": False,
        "durable": False,
        "receipt_count": len(receipts),
        "latest_receipt_hash": receipts[-1]["hash"] if receipts else None,
        "human_authority_final": True,
    }


def answer(
    state: object,
    *,
    question_id: object,
    choice_id: object,
    request_id: object,
) -> tuple[dict[str, Any], dict[str, Any]]:
    current = _validated_copy(state)
    request_key = _valid_request_id(request_id)
    previous = _request_result(current, request_key)
    if previous is not None:
        feedback = _answer_feedback(previous) if previous.get("kind") == "answer" else previous
        return current, public_state(current, feedback=feedback, duplicate=True)
    if current["status"] != "active":
        raise ValueError(f"arena_session_{current['status']}")
    index = int(current["question_index"])
    if index >= len(CHALLENGE_CATALOG):
        raise ValueError("arena_session_completed")
    question = CHALLENGE_CATALOG[index]
    if str(question_id or "") != question["id"]:
        raise ValueError("arena_question_mismatch")
    selected = str(choice_id or "")
    choices = {item["id"]: item["label"] for item in question["choices"]}
    if selected not in choices:
        raise ValueError("arena_choice_invalid")
    correct = selected == question["correct_choice_id"]
    if correct:
        current["score"] += 1
    current["answered"].append(question["id"])
    current["question_index"] += 1
    if current["question_index"] == len(CHALLENGE_CATALOG):
        current["status"] = "completed"
    request_record = {
        "request_id": request_key,
        "kind": "answer",
        "question_id": question["id"],
        "correct": correct,
        "selected_choice_id": selected,
    }
    feedback = _answer_feedback(request_record)
    _request_record(current, request_record)
    _append_receipt(
        current,
        "answer_recorded",
        {"question_id": question["id"], "correct": correct, "request_id": request_key},
    )
    sealed = _seal(current)
    return sealed, public_state(sealed, feedback=feedback)


def transition(
    state: object,
    *,
    action: str,
    request_id: object,
) -> tuple[dict[str, Any], dict[str, Any]]:
    current = _validated_copy(state)
    request_key = _valid_request_id(request_id)
    previous = _request_result(current, request_key)
    if previous is not None:
        return current, public_state(current, feedback=previous, duplicate=True)
    allowed = {
        ("active", "pause"): "paused",
        ("paused", "resume"): "active",
        ("active", "stop"): "stopped",
        ("paused", "stop"): "stopped",
    }
    target = allowed.get((str(current["status"]), action))
    if target is None:
        raise ValueError("arena_transition_denied")
    current["status"] = target
    record = {
        "request_id": request_key,
        "kind": "transition",
        "action": action,
        "status": target,
    }
    _request_record(current, record)
    _append_receipt(current, f"session_{action}", {"request_id": request_key})
    sealed = _seal(current)
    return sealed, public_state(sealed, feedback=record)


def get_public_arena_hub(state: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return {
        "id": ARENA_ID,
        "name": ARENA_NAME,
        "tagline": "One Combined Global Arena",
        "progression": PROGRESSION,
        "intelligence_layers": tuple(dict(item) for item in INTELLIGENCE_LAYERS),
        "challenge": public_state(state),
        "boundary": dict(PUBLIC_BOUNDARY),
        "status": status(),
        "truth": (
            "This release is a real session-scoped, non-ranked Challenge Engine. "
            "Multiplayer, durable profiles, rankings, payments, prizes, external "
            "distribution and live A7 signals remain locked."
        ),
    }
