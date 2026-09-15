"""Private gateway-only UI for temporary Founder recovery."""
from __future__ import annotations

from urllib import parse as urlparse

from flask import (
    Blueprint,
    current_app,
    make_response,
    redirect,
    render_template,
    request,
    session,
)

from . import founder_recovery, neon_auth, web_security

bp = Blueprint("founder_recovery", __name__, template_folder="templates")
_DEFAULT_NEXT = "/mission/ollama"

# Recovery is an emergency Founder lane and must not share the normal sign-in /
# activation bucket. Exact rapid retries are coalesced, while distinct attempts
# remain bounded. Session identity also prevents unrelated clients behind the same
# proxy/NAT address from consuming the Founder's recovery allowance. The Founder
# lane deliberately has more recovery headroom than normal auth because the code
# is already high-entropy and stored only as a SHA-256 digest.
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


def _apply_auth_cookies(response, set_cookie_headers) -> bool:
    """Promote only Neon Auth cookies into the normal first-party session."""

    app_cookie_name = str(current_app.config.get("SESSION_COOKIE_NAME", "session"))
    upstream_names = neon_auth.cookie_names(set_cookie_headers)
    safe_names = tuple(name for name in upstream_names if name != app_cookie_name)
    if not safe_names:
        return False

    session.clear()
    session[neon_auth.AUTH_COOKIE_NAMES_SESSION_KEY] = list(safe_names)
    session.permanent = True
    for header in set_cookie_headers:
        scoped = neon_auth.scoped_set_cookie(header)
        name = header.split("=", 1)[0].strip()
        if scoped and name in safe_names:
            response.headers.add("Set-Cookie", scoped)
    return True


@bp.route("/auth/recover-founder", methods=["GET", "POST"])
def recover_founder():
    """Recover Founder ownership and, when needed, rebuild Managed Auth safely."""

    if not founder_recovery.configured():
        return _hidden()

    next_path = _safe_next(request.values.get("next"))
    if request.method == "GET":
        if founder_recovery.session_active():
            return _no_store(redirect(next_path))
        return _render(next_path=next_path)

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

    password = str(request.form.get("password", ""))[:129]
    confirmation = str(request.form.get("password_confirmation", ""))[:129]
    if password != confirmation:
        return _render(
            status_code=400,
            error="The two private password entries do not match.",
            next_path=next_path,
        )
    if len(password) < 12 or len(password) > 128 or not password.strip():
        return _render(
            status_code=400,
            error="Use your private password between 12 and 128 characters.",
            next_path=next_path,
        )

    email = neon_auth.configured_founder_email()
    if not email or not neon_auth.status()["valid"]:
        return _render(
            status_code=503,
            error="Managed Founder identity is temporarily unavailable.",
            next_path=next_path,
        )

    founder_recovery.begin_session()
    try:
        result = neon_auth.sign_in(email, password)
        if not neon_auth.successful(result) and not neon_auth.temporarily_unavailable(result):
            signup = neon_auth.sign_up_founder(password, "OAP Founder")
            if neon_auth.successful(signup):
                result = neon_auth.sign_in(email, password)
    except neon_auth.AuthUnavailable:
        founder_recovery.clear_session()
        return _render(
            status_code=503,
            error="Managed Founder identity is temporarily unavailable.",
            next_path=next_path,
        )

    if neon_auth.temporarily_unavailable(result):
        founder_recovery.clear_session()
        return _render(
            status_code=503,
            error="Managed Founder identity is temporarily unavailable.",
            next_path=next_path,
        )
    if not neon_auth.successful(result):
        founder_recovery.clear_session()
        return _render(
            status_code=401,
            error="Private password could not be reactivated safely.",
            next_path=next_path,
        )

    response = redirect(next_path)
    if not _apply_auth_cookies(response, result.set_cookie_headers):
        founder_recovery.clear_session()
        return _render(
            status_code=502,
            error="A secure Founder session could not be established.",
            next_path=next_path,
        )
    return _no_store(response)
