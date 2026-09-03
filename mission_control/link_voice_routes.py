"""Authenticated first-party OAP Link Voice routes."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, request

from . import link_voice, web_security

bp = Blueprint("link_voice", __name__)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _error(code: str, status_code: int):
    return _no_store(make_response(jsonify(error={"code": code}), status_code))


def _identity() -> str:
    return web_security.authenticated_identity()


def _mutation_guard(identity: str):
    if not web_security.csrf_valid(request):
        return _error("csrf_failed", 403)
    if not web_security.PUBLIC_WRITE_LIMITER.allow(identity):
        return _error("rate_limited", 429)
    return None


def _failure(exc: Exception):
    code = str(exc) or "voice_unavailable"
    if isinstance(exc, (TypeError, ValueError)):
        if code in {"link_blocked", "accepted_link_required"}:
            return _error(code, 403)
        if code == "voice_too_large":
            return _error(code, 413)
        return _error(code, 400)
    if isinstance(exc, link_voice.LinkVoiceUnavailable):
        return _error("voice_unavailable", 503)
    return _error("voice_unavailable", 503)


@bp.get("/linkup/voice/status")
@web_security.login_required(api=True)
def status():
    state = link_voice.status()
    return _no_store(
        make_response(
            jsonify(
                ready=bool(state.get("ready")),
                first_party=bool(state.get("first_party")),
                max_voice_bytes=state.get("max_voice_bytes"),
                max_voice_duration_ms=state.get("max_voice_duration_ms"),
            )
        )
    )


@bp.get("/linkup/voice")
@web_security.login_required(api=True)
def list_voice():
    peer_id = request.args.get("peer_id", "")
    try:
        notes = link_voice.list_voice(_identity(), peer_id)
        return _no_store(make_response(jsonify(voices=notes)))
    except Exception as exc:
        return _failure(exc)


@bp.post("/linkup/voice")
@web_security.login_required(api=True)
def create_voice():
    identity = _identity()
    if guarded := _mutation_guard(identity):
        return guarded
    try:
        upload = request.files.get("voice")
        if upload is None:
            raise ValueError("voice_required")
        media = upload.stream.read(link_voice.MAX_VOICE_BYTES + 1)
        if len(media) > link_voice.MAX_VOICE_BYTES:
            raise ValueError("voice_too_large")
        created = link_voice.create_voice(
            identity,
            request.form.get("recipient_id"),
            media=media,
            mime_type=upload.mimetype,
            duration_ms=request.form.get("duration_ms"),
        )
        return _no_store(make_response(jsonify(created), 201))
    except Exception as exc:
        return _failure(exc)


@bp.get("/linkup/voice/<voice_id>/media")
@web_security.login_required(api=True)
def voice_media(voice_id: str):
    peer_id = request.args.get("peer_id", "")
    try:
        result = link_voice.read_voice(_identity(), peer_id, voice_id)
        if result is None:
            return _error("voice_not_found", 404)
        media, mime_type, digest = result
        response = make_response(media)
        response.headers["Content-Type"] = mime_type
        response.headers["Content-Length"] = str(len(media))
        response.headers["X-OAP-Content-SHA256"] = digest
        response.headers["Content-Disposition"] = 'inline; filename="voice"'
        return _no_store(response)
    except Exception as exc:
        return _failure(exc)


@bp.delete("/linkup/voice/<voice_id>")
@web_security.login_required(api=True)
def delete_voice(voice_id: str):
    identity = _identity()
    if guarded := _mutation_guard(identity):
        return guarded
    try:
        deleted = link_voice.delete_voice(identity, voice_id)
        if not deleted:
            return _error("voice_not_found", 404)
        return _no_store(make_response(jsonify(deleted=True)))
    except Exception as exc:
        return _failure(exc)
