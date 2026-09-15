"""Private gateway-only UI for temporary Founder recovery and password migration."""
from __future__ import annotations

from urllib import parse as urlparse

from flask import Blueprint, make_response, redirect, render_template, request, url_for

from . import founder_local_auth, founder_recovery, web_security

bp = Blueprint("founder_recovery", __name__, template_folder="templates")
_DEFAULT_NEXT = "/mission/ollama"

# Recovery is an emergency Founder lane and must not share the normal sign-in /
# activation bucket. Exact rapid retries are coalesced, while distinct attempts
# remain bounded. Session identity also prevents unrelated clients behind the same
# proxy/NAT address from consuming the Founder's recovery allowance.
RECOVERY_BURST_LIMITER = web_security.SlidingWindowLimiter(
    limit=30,
    window_seconds=5 * 60,
    duplicate_seconds=5.0,
    fingerprint_request_body=True,
)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return response


def _hidden():
    return _no_store(make_response("", 404))


def _safe_next(value: object) -> str:
    candidate = str(value or _DEFAULT_NEXT).strip()
    try:
        parsed = urlparse.urlparse(candidate)
    except ValueError:
        return _DEFAULT_NEXT
    if parsed.scheme or parsed.netloc or not candidate.startswith("/"):
        return _DEFAULT_NEXT
    path = parsed.path.rstrip("/") or "/"
    return path if founder_recovery.private_path_allowed(path) else _DEFAULT_NEXT


def _render(*, status_code: int = 200, error: str | None = None, next_path: str = _DEFAULT_NEXT):
    response = make_response(
        render_template(
            "founder_recovery.html",
            recovery_error=error,
            next_path=_safe_next(next_path),
        ),
        status_code,
    )
    return _no_store(response)


def _render_bind(*, status_code: int = 200, error: str | None = None, next_path: str = _DEFAULT_NEXT):
    response = make_response(
        render_template(
            "founder_password_bind.html",
            bind_error=error,
            next_path=_safe_next(next_path),
        ),
        status_code,
    )
    return _no_store(response)


def _bind_existing_password(next_path: str):
    if not founder_recovery.session_active():
        return _render(
            status_code=403,
            error="Founder proof expired. Confirm the Founder recovery code again.",
            next_path=next_path,
        )
    if founder_local_auth.bound():
        founder_recovery.clear_session()
        return _no_store(redirect(url_for("auth_page", next=next_path)))
    if not web_security.csrf_valid(request):
        return _render_bind(
            status_code=403,
            error="Session expired. Refresh and try again.",
            next_path=next_path,
        )

    password = str(request.form.get("password") or "")
    confirmation = str(request.form.get("password_confirmation") or "")
    if password != confirmation:
        return _render_bind(
            status_code=400,
            error="The two private password entries do not match.",
            next_path=next_path,
        )
    if len(password) < 12 or len(password) > 128 or not password.strip():
        return _render_bind(
            status_code=400,
            error="Use your existing private password between 12 and 128 characters.",
            next_path=next_path,
        )

    try:
        result = founder_local_auth.bind_existing_password(password)
    except founder_local_auth.FounderLocalAuthUnavailable:
        return _render_bind(
            status_code=503,
            error="Render Founder password storage is temporarily unavailable.",
            next_path=next_path,
        )
    if result not in {"bound", "complete"}:
        return _render_bind(
            status_code=503,
            error="Render Founder password storage is temporarily unavailable.",
            next_path=next_path,
        )

    founder_recovery.clear_session()
    response = redirect(url_for("auth_page", next=next_path, render_bound="1"))
    response.headers["X-OAP-Founder-Lane"] = "render-local"
    return _no_store(response)


@bp.route("/auth/recover-founder", methods=["GET", "POST"])
def recover_founder():
    """Open bounded Founder recovery and bind the existing password once.

    No second Founder account is created. When the Render-local verifier is
    absent, a successful recovery proof may bind the existing private password
    to the canonical Human Authority identity. Once bound, normal /auth sign-in
    uses Render-local verification and recovery returns to emergency-only use.
    """

    if not founder_recovery.configured():
        return _hidden()

    next_path = _safe_next(request.values.get("next"))
    action = str(request.values.get("action") or "")

    if request.method == "GET":
        if founder_recovery.session_active():
            if not founder_local_auth.bound():
                return _render_bind(next_path=next_path)
            return _no_store(redirect(next_path))
        return _render(next_path=next_path)

    if action == "bind-password":
        return _bind_existing_password(next_path)

    if not web_security.csrf_valid(request):
        return _render(
            status_code=403,
            error="Session expired. Refresh and try again.",
            next_path=next_path,
        )

    session_id = web_security.ensure_session_identity()
    rate_key = f"recovery:{session_id}:{request.remote_addr or 'unknown'}"
    if not RECOVERY_BURST_LIMITER.allow(rate_key):
        response = _render(
            status_code=429,
            error="Founder recovery is temporarily protected. Wait briefly, then try once.",
            next_path=next_path,
        )
        response.headers["Retry-After"] = "60"
        return response

    if not founder_recovery.token_allowed(request.form.get("recovery_code")):
        return _render(
            status_code=403,
            error="Code not recognised.",
            next_path=next_path,
        )

    founder_recovery.begin_session()
    if not founder_local_auth.bound():
        return _render_bind(next_path=next_path)
    return _no_store(redirect(next_path))
