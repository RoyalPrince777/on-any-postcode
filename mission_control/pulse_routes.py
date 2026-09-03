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
        if not web_security.csrf_valid(request):
            return _error("csrf_failed", "Request verification failed.", 403)
        identity_id = web_security.ensure_session_identity()
        if not web_security.PUBLIC_WRITE_LIMITER.allow(identity_id):
            return _error("rate_limited", "Too many posts. Try again shortly.", 429)
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
            if str(exc) == "pulse_rate_limit":
                return _error("rate_limited", "Too many posts. Try again shortly.", 429)
            return _error(
                "pulse_content_required",
                "Nickname and post are required.",
                400,
            )
        except pulse_store.PulseStoreUnavailable:
            return _error("pulse_unavailable", "Pulse is unavailable.", 503)
        return redirect(url_for("pulse_feed"))
