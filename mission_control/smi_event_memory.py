"""Automatic, privacy-reduced memory receipts for meaningful OAP actions.

The hook runs after successful requests. It deliberately ignores harmless page
navigation and never stores request bodies, headers, cookies, credentials,
payment values or precise location values. Existing SMI Chat persistence remains
the owner of chat memory, so chat endpoints are excluded here.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

from flask import Flask, request

from . import postgres_db, smi_auto, web_security

MEMORY_LIGHT = "purple"
WRITE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
_EXCLUDED_PREFIXES = (
    "/static",
    "/auth",
    "/enter-my-world",
    "/health",
    "/healthz",
    "/favicon",
    "/mission/ollama/chat",
    "/mission/smi/chat",
    "/api/smi/chat",
)
_MEANINGFUL_GET_TERMS = (
    "atlas",
    "map",
    "route",
    "movement",
    "travel",
    "booking",
    "direct",
)


def _clean_path(value: object) -> str:
    path = "/" + str(value or "").split("?", 1)[0].lstrip("/").lower()
    return path.rstrip("/") or "/"


def should_record(method: object, path: object, status_code: object, *, has_query: bool = False) -> bool:
    """Return whether a completed request is meaningful enough for HRM memory."""

    method_key = str(method or "GET").upper()
    clean = _clean_path(path)
    try:
        status = int(status_code)
    except (TypeError, ValueError):
        return False
    if not 200 <= status < 400:
        return False
    if any(clean == prefix or clean.startswith(prefix + "/") for prefix in _EXCLUDED_PREFIXES):
        return False
    if method_key in WRITE_METHODS:
        return True
    return method_key == "GET" and bool(has_query) and any(term in clean for term in _MEANINGFUL_GET_TERMS)


def _domain(path: str) -> str:
    if any(term in path for term in ("travel", "booking", "direct", "reservation", "supply")):
        return "BOOKING"
    if any(term in path for term in ("atlas", "map", "route")):
        return "MAPS"
    if any(term in path for term in ("movement", "ride", "drop", "delivery")):
        return "MOVEMENT"
    if any(term in path for term in ("link", "message", "voice", "call", "circle", "presence")):
        return "THE_LINK"
    if any(term in path for term in ("signal", "pulse", "room", "flag", "the-spot")):
        return "THE_SPOT"
    if any(term in path for term in ("market", "product", "commerce")):
        return "MARKET"
    if any(term in path for term in ("sika", "wallet", "transaction")):
        return "SIKA"
    if any(term in path for term in ("my-world", "myworld", "profile")):
        return "MY_WORLD"
    if any(term in path for term in ("judgement", "approval", "certify", "governance")):
        return "GOVERNANCE"
    return "OAP"


def descriptor(method: object, path: object, endpoint: object, status_code: object, query_keys: tuple[str, ...] = ()) -> dict[str, Any]:
    """Return only privacy-reduced metadata safe for SMI/HRM."""

    clean = _clean_path(path)
    route = smi_auto.observe(method, clean, endpoint)
    safe_keys = tuple(sorted({str(item)[:40] for item in query_keys if str(item).strip()}))[:12]
    return {
        "domain": _domain(clean),
        "method": str(method or "GET").upper(),
        "path": clean[:240],
        "endpoint": str(endpoint or "")[:120],
        "status_code": int(status_code),
        "query_keys": safe_keys,
        "memory_light": MEMORY_LIGHT,
        "automatic_intelligence_lenses": tuple(route.get("lenses") or ()),
        "war_room_escalation": bool(route.get("war_room_escalation")),
        "request_body_retained": False,
        "query_values_retained": False,
        "headers_retained": False,
        "cookies_retained": False,
        "credentials_retained": False,
        "precise_live_location_retained": False,
        "execution_granted": False,
        "approval_granted": False,
        "human_authority_final": True,
    }


def _summary(meta: dict[str, Any]) -> str:
    query_note = f"; query fields {', '.join(meta['query_keys'])}" if meta["query_keys"] else ""
    return (
        f"{meta['domain']} meaningful action completed: {meta['method']} "
        f"{meta['path']} returned {meta['status_code']}{query_note}. "
        "Privacy-reduced receipt only; request values were not retained."
    )[:600]


def _persist(identity_id: str, meta: dict[str, Any]) -> None:
    request_id = str(uuid.uuid4())
    summary = _summary(meta)
    content_hash = hashlib.sha256(
        json.dumps(meta, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    with postgres_db.connect() as connection:
        connection.execute(
            """INSERT INTO smi_memory_records
               (request_id,identity_id,task_type,content_hash,summary,output_state,
                signal_level,rationale_json,processing_states_json)
               VALUES (%s,%s,'OAP_EVENT',%s,%s,'SYSTEM_LOG_ONLY','WHITE',%s::jsonb,%s::jsonb)""",
            (
                request_id,
                identity_id,
                content_hash,
                summary,
                json.dumps({**meta, "memory_light": MEMORY_LIGHT}),
                json.dumps(["EVENT_OBSERVED", "PRIVACY_REDUCED", "HRM_RECORDED"]),
            ),
        )
        connection.execute("SELECT pg_advisory_xact_lock(%s)", (24680259,))
        previous = connection.execute(
            "SELECT curr_hash FROM audit_events ORDER BY event_seq DESC LIMIT 1"
        ).fetchone()
        prev_hash = str(previous[0]) if previous else "GENESIS"
        audit_meta = {
            "request_id": request_id,
            "identity_id": identity_id,
            "memory_light": MEMORY_LIGHT,
            "event": meta,
        }
        canonical = json.dumps(audit_meta, sort_keys=True, separators=(",", ":"))
        curr_hash = hashlib.sha256((prev_hash + canonical).encode()).hexdigest()
        connection.execute(
            """INSERT INTO audit_events
               (prev_hash,curr_hash,actor_id,actor_type,authority_level,
                action,target,reason,correlation_id,metadata)
               VALUES (%s,%s,%s,'HUMAN',NULL,'OAP_MEMORY_RECORDED',%s,%s,%s,%s::jsonb)""",
            (
                prev_hash,
                curr_hash,
                identity_id,
                meta["domain"],
                "Meaningful OAP action recorded as privacy-reduced SMI/HRM memory.",
                request_id,
                canonical,
            ),
        )
        connection.commit()


def register(app: Flask) -> None:
    """Attach the automatic memory receipt after successful meaningful actions."""

    @app.after_request
    def _remember_meaningful_oap_action(response):
        try:
            if not should_record(
                request.method,
                request.path,
                response.status_code,
                has_query=bool(request.args),
            ):
                return response
            user = web_security.current_authenticated_user()
            if user is None:
                return response
            identity_id = str(user.get("id") or "")
            if not identity_id:
                return response
            meta = descriptor(
                request.method,
                request.path,
                request.endpoint,
                response.status_code,
                tuple(request.args.keys()),
            )
            _persist(identity_id, meta)
        except Exception:  # noqa: BLE001 -- memory must never break the user action.
            pass
        return response


def status() -> dict[str, object]:
    return {
        "component": "SMI Meaningful Event Memory",
        "active": True,
        "memory_light": MEMORY_LIGHT,
        "successful_writes_recorded": True,
        "meaningful_map_route_queries_recorded": True,
        "harmless_navigation_recorded": False,
        "anonymous_personal_memory_created": False,
        "smi_chat_duplicate_memory_created": False,
        "request_values_retained": False,
        "credentials_retained": False,
        "precise_live_location_retained": False,
        "audit_receipt_written": True,
        "execution_granted": False,
        "approval_granted": False,
        "human_authority_final": True,
    }
