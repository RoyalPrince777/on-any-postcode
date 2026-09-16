"""Private Founder recovery and bounded normal-login password repair UI."""
from __future__ import annotations

import hashlib
import hmac
import os
import time
from urllib import parse as urlparse

from flask import (
    Blueprint,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from . import founder_local_auth, founder_recovery, web_security

bp = Blueprint("founder_recovery", __name__, template_folder="templates")
_DEFAULT_NEXT = "/mission/ollama"
_BIND_MODE = "bind"
_NORMAL_REPAIR_HASH_ENV = "OAP_FOUNDER_NORMAL_REPAIR_TOKEN_SHA256"
_NORMAL_REPAIR_EXPIRES_ENV = "OAP_FOUNDER_NORMAL_REPAIR_EXPIRES_AT"
_NORMAL_REPAIR_SESSION_KEY = "oap_founder_normal_repair"
_NORMAL_REPAIR_SESSION_SECONDS = 15 * 60

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


def _render(
    *,
    status_code: int = 200,
    error: str | None = None,
    next_path: str = _DEFAULT_NEXT,
    bind_mode: bool = False,
):
    response = make_response(
        render_template(
            "founder_recovery.html",
            recovery_error=error,
            next_path=_safe_next(next_path),
            bind_mode=bind_mode,
        ),
        status_code,
    )
    return _no_store(response)


def _render_bind(
    *,
    status_code: int = 200,
    error: str | None = None,
    next_path: str = _DEFAULT_NEXT,
    form_action: str | None = None,
    action_value: str = "bind-password",
    eyebrow: str | None = None,
    heading: str | None = None,
    subcopy: str | None = None,
    button_label: str | None = None,
    fine_print: str | None = None,
):
    response = make_response(
        render_template(
            "founder_password_bind.html",
            bind_error=error,
            next_path=_safe_next(next_path),
            bind_form_action=form_action,
            bind_action_value=action_value,
            bind_eyebrow=eyebrow,
            bind_heading=heading,
            bind_subcopy=subcopy,
            bind_button_label=button_label,
            bind_fine_print=fine_print,
        ),
        status_code,
    )
    return _no_store(response)


def _password_fields():
    password = str(request.form.get("password") or "")
    confirmation = str(request.form.get("password_confirmation") or "")
    if password != confirmation:
        return None, "The two private password entries do not match."
    if len(password) < 12 or len(password) > 128 or not password.strip():
        return None, "Use your existing private password between 12 and 128 characters."
    return password, None


def _bind_existing_password(next_path: str):
    if not founder_recovery.session_active():
        return _render(
            status_code=403,
            error="Founder proof expired. Confirm the Founder recovery code again.",
            next_path=next_path,
            bind_mode=True,
        )
    if not web_security.csrf_valid(request):
        return _render_bind(
            status_code=403,
            error="Session expired. Refresh and try again.",
            next_path=next_path,
        )

    password, error = _password_fields()
    if error:
        return _render_bind(status_code=400, error=error, next_path=next_path)

    try:
        result = founder_local_auth.bind_existing_password(password)
    except founder_local_auth.FounderLocalAuthUnavailable:
        return _render_bind(
            status_code=503,
            error="Render Founder password storage is temporarily unavailable.",
            next_path=next_path,
        )
    if result not in {"bound", "rebound", "complete"}:
        return _render_bind(
            status_code=503,
            error="Render Founder password storage is temporarily unavailable.",
            next_path=next_path,
        )

    founder_recovery.clear_session()
    response = redirect(url_for("auth_page", next=next_path, render_bound="1"))
    response.headers["X-OAP-Founder-Lane"] = "render-local"
    response.headers["X-OAP-Founder-Password-State"] = (
        "rebound" if result == "rebound" else "bound"
    )
    return _no_store(response)


def _normal_repair_hash() -> str:
    return os.environ.get(_NORMAL_REPAIR_HASH_ENV, "").strip().casefold()


def _normal_repair_expiry() -> int:
    try:
        return int(os.environ.get(_NORMAL_REPAIR_EXPIRES_ENV, "0").strip())
    except (TypeError, ValueError):
        return 0


def _normal_repair_configured(*, now: int | None = None) -> bool:
    current = int(time.time()) if now is None else int(now)
    digest = _normal_repair_hash()
    return (
        len(digest) == 64
        and all(char in "0123456789abcdef" for char in digest)
        and _normal_repair_expiry() > current
    )


def _normal_repair_token_allowed(candidate: object, *, now: int | None = None) -> bool:
    if not _normal_repair_configured(now=now):
        return False
    supplied = str(candidate or "")
    if len(supplied) < 32 or len(supplied) > 256:
        return False
    digest = hashlib.sha256(supplied.encode("utf-8")).hexdigest()
    return hmac.compare_digest(_normal_repair_hash(), digest)


def _begin_normal_repair_session(*, now: int | None = None) -> None:
    current = int(time.time()) if now is None else int(now)
    expires_at = min(
        current + _NORMAL_REPAIR_SESSION_SECONDS,
        _normal_repair_expiry(),
    )
    session[_NORMAL_REPAIR_SESSION_KEY] = {
        "version": 1,
        "token_hash": _normal_repair_hash(),
        "expires_at": expires_at,
    }
    session.permanent = True


def _clear_normal_repair_session() -> None:
    session.pop(_NORMAL_REPAIR_SESSION_KEY, None)


def _normal_repair_session_active(*, now: int | None = None) -> bool:
    current = int(time.time()) if now is None else int(now)
    if not _normal_repair_configured(now=current):
        _clear_normal_repair_session()
        return False
    value = session.get(_NORMAL_REPAIR_SESSION_KEY)
    if not isinstance(value, dict) or value.get("version") != 1:
        return False
    try:
        expires_at = int(value.get("expires_at", 0))
    except (TypeError, ValueError):
        _clear_normal_repair_session()
        return False
    if expires_at <= current or expires_at > current + _NORMAL_REPAIR_SESSION_SECONDS:
        _clear_normal_repair_session()
        return False
    if expires_at > _normal_repair_expiry():
        _clear_normal_repair_session()
        return False
    return hmac.compare_digest(
        str(value.get("token_hash") or ""),
        _normal_repair_hash(),
    )


def _render_normal_repair(
    *,
    status_code: int = 200,
    error: str | None = None,
    next_path: str = _DEFAULT_NEXT,
):
    return _render_bind(
        status_code=status_code,
        error=error,
        next_path=next_path,
        form_action=url_for("founder_recovery.repair_founder_password"),
        action_value="repair-normal-password",
        eyebrow="Private Founder Repair",
        heading="Restore normal Founder login",
        subcopy=(
            "Enter your original private password twice. OAP will replace only the "
            "salted Render-local verifier for the existing Human Authority identity."
        ),
        button_label="Restore Normal Login",
        fine_print=(
            "No second Founder is created. After this repair, use Enter My World with "
            "your normal private password."
        ),
    )


@bp.route("/auth/repair-founder-password", methods=["GET", "POST"])
def repair_founder_password():
    """Short-lived control-plane-authorized repair for normal Founder login."""

    next_path = _safe_next(request.values.get("next"))
    if request.method == "GET":
        proof = request.args.get("proof")
        if proof:
            if not _normal_repair_token_allowed(proof):
                return _hidden()
            _begin_normal_repair_session()
            return _no_store(
                redirect(
                    url_for(
                        "founder_recovery.repair_founder_password",
                        next=next_path,
                    )
                )
            )
        if not _normal_repair_session_active():
            return _hidden()
        return _render_normal_repair(next_path=next_path)

    if not _normal_repair_session_active():
        return _hidden()
    if not web_security.csrf_valid(request):
        return _render_normal_repair(
            status_code=403,
            error="Repair session expired. Open the repair link again.",
            next_path=next_path,
        )
    if str(request.form.get("action") or "") != "repair-normal-password":
        return _hidden()

    password, error = _password_fields()
    if error:
        return _render_normal_repair(
            status_code=400,
            error=error,
            next_path=next_path,
        )

    try:
        result = founder_local_auth.bind_existing_password(password)
    except founder_local_auth.FounderLocalAuthUnavailable:
        return _render_normal_repair(
            status_code=503,
            error="Render Founder password storage is temporarily unavailable.",
            next_path=next_path,
        )
    if result not in {"bound", "rebound", "complete"}:
        return _render_normal_repair(
            status_code=503,
            error="Render Founder password storage is temporarily unavailable.",
            next_path=next_path,
        )

    _clear_normal_repair_session()
    response = redirect(url_for("auth_page", next=next_path, render_bound="1"))
    response.headers["X-OAP-Founder-Lane"] = "render-local-normal"
    response.headers["X-OAP-Founder-Password-State"] = (
        "rebound" if result == "rebound" else "bound"
    )
    return _no_store(response)


@bp.route("/auth/recover-founder", methods=["GET", "POST"])
def recover_founder():
    """Open bounded recovery, with explicit password bind/repair mode.

    Ordinary recovery keeps its established emergency behavior. Password binding
    or repair occurs only when the Founder deliberately opens ``mode=bind`` and
    completes the existing recovery proof. No second Founder identity is created.
    """

    if not founder_recovery.configured():
        return _hidden()

    next_path = _safe_next(request.values.get("next"))
    action = str(request.values.get("action") or "")
    bind_mode = str(request.values.get("mode") or "").casefold() == _BIND_MODE

    if request.method == "GET":
        if founder_recovery.session_active():
            if bind_mode:
                return _render_bind(next_path=next_path)
            return _no_store(redirect(next_path))
        return _render(next_path=next_path, bind_mode=bind_mode)

    if action == "bind-password":
        return _bind_existing_password(next_path)

    if not web_security.csrf_valid(request):
        return _render(
            status_code=403,
            error="Session expired. Refresh and try again.",
            next_path=next_path,
            bind_mode=bind_mode,
        )

    session_id = web_security.ensure_session_identity()
    rate_key = f"recovery:{session_id}:{request.remote_addr or 'unknown'}"
    if not RECOVERY_BURST_LIMITER.allow(rate_key):
        response = _render(
            status_code=429,
            error="Founder recovery is temporarily protected. Wait briefly, then try once.",
            next_path=next_path,
            bind_mode=bind_mode,
        )
        response.headers["Retry-After"] = "60"
        return response

    if not founder_recovery.token_allowed(request.form.get("recovery_code")):
        return _render(
            status_code=403,
            error="Code not recognised.",
            next_path=next_path,
            bind_mode=bind_mode,
        )

    founder_recovery.begin_session()
    if bind_mode:
        return _render_bind(next_path=next_path)
    return _no_store(redirect(next_path))
