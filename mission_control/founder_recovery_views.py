"""Private gateway-only UI for temporary Founder recovery."""
from __future__ import annotations

from urllib import parse as urlparse

from flask import Blueprint, make_response, redirect, render_template, request

from . import founder_recovery, web_security

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


@bp.route("/auth/recover-founder", methods=["GET", "POST"])
def recover_founder():
    """Open a bounded recovery session only while server recovery is enabled."""

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

    founder_recovery.begin_session()
    return _no_store(redirect(next_path))
