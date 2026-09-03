"""Public Pulse feed routes with bounded first-party persistence."""

from __future__ import annotations

from flask import (
    Flask,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)

from . import pulse_store, web_security


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _error(code: str, message: str, status: int):
    return _no_store(
        make_response(jsonify(error={"code": code, "message": message}), status)
    )


def _write_identity():
    if not web_security.csrf_valid(request):
        return None, _error("csrf_failed", "Request verification failed.", 403)
    identity_id = web_security.ensure_session_identity()
    if not web_security.PUBLIC_WRITE_LIMITER.allow(identity_id):
        return None, _error("rate_limited", "Too many Pulse actions. Try again shortly.", 429)
    return identity_id, None


def _store_error(exc: ValueError):
    code = str(exc)
    if code == "pulse_rate_limit":
        return _error("rate_limited", "Too many Pulse actions. Try again shortly.", 429)
    if code == "pulse_post_not_found":
        return _error(code, "That Pulse is no longer available.", 404)
    if code in {"invalid_pulse_post", "invalid_pulse_reaction"}:
        return _error(code, "That Pulse action is invalid.", 400)
    if code == "pulse_reply_required":
        return _error(code, "Nickname and reply are required.", 400)
    return _error("pulse_content_required", "Nickname and post are required.", 400)


def register(app: Flask) -> None:
    """Register Pulse independently from Signal without creating a second schema."""

    def _render_pulse():
        unavailable = False
        try:
            posts = pulse_store.list_posts()
        except pulse_store.PulseStoreUnavailable:
            posts = []
            unavailable = True
        return _no_store(
            make_response(
                render_template(
                    "pulse.html",
                    pulse_posts=posts,
                    pulse_unavailable=unavailable,
                    pulse_reactions=pulse_store.REACTION_LABELS,
                ),
                200,
            )
        )

    @app.get("/the-spot/pulse")
    def spot_pulse_compat():
        return _render_pulse()

    @app.get("/pulse")
    def pulse_feed():
        return _render_pulse()

    @app.post("/pulse")
    def pulse_post():
        identity_id, failure = _write_identity()
        if failure is not None:
            return failure
        name = str(request.form.get("name", "")).strip()[:80]
        body = str(request.form.get("body", "")).strip()[:2000]
        if not name or not body:
            return _error(
                "pulse_content_required",
                "Nickname and post are required.",
                400,
            )
        try:
            pulse_store.add_post(identity_id, name=name, body=body)
        except ValueError as exc:
            return _store_error(exc)
        except pulse_store.PulseStoreUnavailable:
            return _error("pulse_unavailable", "Pulse is unavailable.", 503)
        return redirect(url_for("pulse_feed"))

    @app.post("/pulse/<post_id>/reaction")
    def pulse_reaction(post_id: str):
        identity_id, failure = _write_identity()
        if failure is not None:
            return failure
        try:
            pulse_store.add_reaction(
                identity_id,
                post_id,
                request.form.get("reaction", ""),
            )
        except ValueError as exc:
            return _store_error(exc)
        except pulse_store.PulseStoreUnavailable:
            return _error("pulse_unavailable", "Pulse is unavailable.", 503)
        return redirect(url_for("pulse_feed"))

    @app.post("/pulse/<post_id>/reply")
    def pulse_reply(post_id: str):
        identity_id, failure = _write_identity()
        if failure is not None:
            return failure
        try:
            pulse_store.add_reply(
                identity_id,
                post_id,
                name=request.form.get("name", ""),
                body=request.form.get("body", ""),
            )
        except ValueError as exc:
            return _store_error(exc)
        except pulse_store.PulseStoreUnavailable:
            return _error("pulse_unavailable", "Pulse is unavailable.", 503)
        return redirect(url_for("pulse_feed"))
