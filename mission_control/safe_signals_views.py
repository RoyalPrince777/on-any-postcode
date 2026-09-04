"""Public Safe Signals boards and Founder-only governed write routes."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, render_template, request

from . import safe_signals, web_security

bp = Blueprint("safe_signals", __name__)
_STORE = safe_signals.SafeSignalsStore()


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _error(code: str, message: str, status_code: int):
    return _no_store(
        make_response(jsonify(error={"code": code, "message": message}), status_code)
    )


def _payload() -> dict:
    value = request.get_json(silent=True)
    if not isinstance(value, dict):
        raise TypeError("json_object_required")
    return value


def _founder_write(operation):
    if not web_security.csrf_valid(request):
        return _error("csrf_failed", "The secure session expired.", 403)
    try:
        result = operation(_payload())
    except PermissionError as exc:
        return _error("safe_signals_not_authorized", str(exc)[:160], 403)
    except (TypeError, ValueError) as exc:
        return _error("invalid_safe_signal", str(exc)[:160], 400)
    except RuntimeError as exc:
        return _error("safe_signals_unavailable", str(exc)[:160], 503)
    return _no_store(make_response(jsonify(result)))


def _signals_board(kind: str | None, title: str):
    try:
        data = safe_signals.public_signals(
            kind=kind,
            area_level=request.args.get("area_level"),
            youth_safe=request.args.get("youth_safe") == "1",
            limit=request.args.get("limit", "50"),
        )
    except (TypeError, ValueError) as exc:
        data = {"ready": True, "items": [], "count": 0, "error": str(exc)}
    return _no_store(
        make_response(
            render_template(
                "safe_signals_board.html",
                board_title=title,
                board_kind=kind or "ALL",
                data=data,
                public_promise=safe_signals.PUBLIC_PROMISE,
            )
        )
    )


@bp.get("/signals")
def signals_board():
    return _signals_board(None, "World Signals")


@bp.get("/weather")
def weather_board():
    return _signals_board("WEATHER", "Weather Signals")


@bp.get("/news-facts")
def news_facts_board():
    return _signals_board("NEWS", "News Facts")


@bp.get("/civic-voice")
def civic_voice_board():
    data = safe_signals.public_civic_voice(limit=request.args.get("limit", "50"))
    return _no_store(
        make_response(
            render_template(
                "safe_signals_board.html",
                board_title="Civic Voice",
                board_kind="CIVIC",
                data=data,
                public_promise=safe_signals.PUBLIC_PROMISE,
            )
        )
    )


@bp.get("/mentorship")
def mentorship_board():
    try:
        data = safe_signals.public_mentorship(
            audience=request.args.get("audience"), limit=request.args.get("limit", "50")
        )
    except (TypeError, ValueError) as exc:
        data = {"ready": True, "items": [], "count": 0, "error": str(exc)}
    return _no_store(
        make_response(
            render_template(
                "safe_signals_board.html",
                board_title="Better World Mentorship",
                board_kind="MENTORSHIP",
                data=data,
                public_promise=safe_signals.PUBLIC_PROMISE,
            )
        )
    )


@bp.get("/signals/api")
def signals_api():
    try:
        result = safe_signals.public_signals(
            kind=request.args.get("kind"),
            area_level=request.args.get("area_level"),
            youth_safe=request.args.get("youth_safe") == "1",
            limit=request.args.get("limit", "50"),
        )
    except (TypeError, ValueError) as exc:
        return _error("invalid_signal_filter", str(exc)[:120], 400)
    return _no_store(make_response(jsonify(result)))


@bp.get("/civic-voice/api")
def civic_voice_api():
    try:
        result = safe_signals.public_civic_voice(limit=request.args.get("limit", "50"))
    except (TypeError, ValueError) as exc:
        return _error("invalid_civic_filter", str(exc)[:120], 400)
    return _no_store(make_response(jsonify(result)))


@bp.get("/mentorship/api")
def mentorship_api():
    try:
        result = safe_signals.public_mentorship(
            audience=request.args.get("audience"), limit=request.args.get("limit", "50")
        )
    except (TypeError, ValueError) as exc:
        return _error("invalid_mentorship_filter", str(exc)[:120], 400)
    return _no_store(make_response(jsonify(result)))


@bp.get("/mission/safe-signals/status")
@web_security.login_required(api=True, founder_only=True)
def founder_status():
    return _no_store(make_response(jsonify(safe_signals.status())))


@bp.post("/mission/safe-signals/signals")
@web_security.login_required(api=True, founder_only=True)
def create_signal():
    return _founder_write(_STORE.create_signal)


@bp.post("/mission/safe-signals/signals/activate")
@web_security.login_required(api=True, founder_only=True)
def activate_signal():
    return _founder_write(_STORE.activate_signal)


@bp.post("/mission/safe-signals/signals/correct")
@web_security.login_required(api=True, founder_only=True)
def correct_signal():
    return _founder_write(_STORE.add_correction)


@bp.post("/mission/safe-signals/civic")
@web_security.login_required(api=True, founder_only=True)
def create_civic():
    return _founder_write(_STORE.create_civic_item)


@bp.post("/mission/safe-signals/mentorship")
@web_security.login_required(api=True, founder_only=True)
def create_mentorship():
    return _founder_write(_STORE.create_mentorship_guide)
