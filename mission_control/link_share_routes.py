"""Authenticated first-party OAP Link Share routes."""
from __future__ import annotations

from urllib.parse import quote

from flask import Blueprint, jsonify, make_response, request

from . import link_share, web_security

bp = Blueprint("link_share", __name__)


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


def _failure(exc: TypeError | ValueError | link_share.LinkShareUnavailable):
    code = str(exc) or "share_unavailable"
    if isinstance(exc, (TypeError, ValueError)):
        if code in {"link_blocked", "accepted_link_required"}:
            return _error(code, 403)
        if code == "share_too_large":
            return _error(code, 413)
        return _error(code, 400)
    return _error("share_unavailable", 503)


@bp.get("/linkup/share/status")
@web_security.login_required(api=True)
def status():
    state = link_share.status()
    return _no_store(
        make_response(
            jsonify(
                ready=bool(state.get("ready")),
                first_party=bool(state.get("first_party")),
                max_share_bytes=state.get("max_share_bytes"),
                allowed_mime_types=state.get("allowed_mime_types", []),
            )
        )
    )


@bp.get("/linkup/share")
@web_security.login_required(api=True)
def list_share():
    peer_id = request.args.get("peer_id", "")
    try:
        shares = link_share.list_shares(_identity(), peer_id)
        return _no_store(make_response(jsonify(shares=shares)))
    except (TypeError, ValueError, link_share.LinkShareUnavailable) as exc:
        return _failure(exc)


@bp.post("/linkup/share")
@web_security.login_required(api=True)
def create_share():
    identity = _identity()
    if guarded := _mutation_guard(identity):
        return guarded
    try:
        upload = request.files.get("share")
        if upload is None:
            raise ValueError("share_required")
        media = upload.stream.read(link_share.MAX_SHARE_BYTES + 1)
        if len(media) > link_share.MAX_SHARE_BYTES:
            raise ValueError("share_too_large")
        created = link_share.create_share(
            identity,
            request.form.get("recipient_id"),
            media=media,
            mime_type=upload.mimetype,
            original_name=upload.filename,
        )
        return _no_store(make_response(jsonify(created), 201))
    except (TypeError, ValueError, link_share.LinkShareUnavailable) as exc:
        return _failure(exc)


@bp.get("/linkup/share/<share_id>/media")
@web_security.login_required(api=True)
def share_media(share_id: str):
    peer_id = request.args.get("peer_id", "")
    try:
        result = link_share.read_share(_identity(), peer_id, share_id)
        if result is None:
            return _error("share_not_found", 404)
        media, mime_type, digest, original_name, kind = result
        response = make_response(media)
        response.headers["Content-Type"] = mime_type
        response.headers["Content-Length"] = str(len(media))
        response.headers["X-OAP-Content-SHA256"] = digest
        disposition = "inline" if kind in {"photo", "video"} else "attachment"
        encoded_name = quote(original_name, safe="")
        response.headers["Content-Disposition"] = (
            f"{disposition}; filename*=UTF-8''{encoded_name}"
        )
        return _no_store(response)
    except (TypeError, ValueError, link_share.LinkShareUnavailable) as exc:
        return _failure(exc)


@bp.delete("/linkup/share/<share_id>")
@web_security.login_required(api=True)
def delete_share(share_id: str):
    identity = _identity()
    if guarded := _mutation_guard(identity):
        return guarded
    try:
        deleted = link_share.delete_share(identity, share_id)
        if not deleted:
            return _error("share_not_found", 404)
        return _no_store(make_response(jsonify(deleted=True)))
    except (TypeError, ValueError, link_share.LinkShareUnavailable) as exc:
        return _failure(exc)
