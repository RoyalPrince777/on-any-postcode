"""Private gateway-only UI for temporary Founder recovery."""
from __future__ import annotations

import uuid
from urllib import parse as urlparse

from flask import (
    Blueprint,
    current_app,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from . import (
    authority,
    founder_activation,
    founder_recovery,
    neon_auth,
    postgres_db,
    web_security,
)

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


def _render(
    *,
    status_code: int = 200,
    error: str | None = None,
    next_path: str = _DEFAULT_NEXT,
):
    response = make_response(
        render_template(
            "founder_recovery.html",
            recovery_error=error,
            next_path=_safe_next(next_path),
        ),
        status_code,
    )
    return _no_store(response)


def _render_reactivation(
    *,
    status_code: int = 200,
    error: str | None = None,
    next_path: str = _DEFAULT_NEXT,
):
    response = make_response(
        render_template(
            "founder_reactivation.html",
            reactivation_error=error,
            next_path=_safe_next(next_path),
        ),
        status_code,
    )
    return _no_store(response)


def _apply_auth_cookies(response, set_cookie_headers) -> bool:
    """Promote only Better Auth cookies into the normal first-party session."""

    app_cookie_name = str(current_app.config.get("SESSION_COOKIE_NAME", "session"))
    upstream_names = neon_auth.cookie_names(set_cookie_headers)
    safe_names = tuple(name for name in upstream_names if name != app_cookie_name)
    if not safe_names:
        return False

    founder_recovery.clear_session()
    session.clear()
    session[neon_auth.AUTH_COOKIE_NAMES_SESSION_KEY] = list(safe_names)
    session.permanent = True
    for header in set_cookie_headers:
        scoped = neon_auth.scoped_set_cookie(header)
        name = header.split("=", 1)[0].strip()
        if scoped and name in safe_names:
            response.headers.add("Set-Cookie", scoped)
    return True


def _result_identity(result: neon_auth.AuthResult) -> str:
    payload = result.payload
    user = payload.get("user") if isinstance(payload, dict) else None
    raw_identity = user.get("id") if isinstance(user, dict) else None
    try:
        return str(uuid.UUID(str(raw_identity)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise founder_activation.ActivationUnavailable(
            "managed_founder_identity_missing"
        ) from exc


def _bind_reactivated_authority(identity_id: str) -> None:
    """Move the active Human Authority binding to the rebuilt Auth identity.

    This may only be called from the recovery-proven, zero-user reactivation
    ceremony below. Historical authority rows are retained for audit/history but
    made inactive so exactly one managed identity remains active authority.
    """

    email = neon_auth.configured_founder_email()
    if not email or not neon_auth.founder_email_allowed(email):
        raise founder_activation.ActivationUnavailable(
            "founder_selector_not_configured"
        )
    try:
        with postgres_db.connect() as connection:
            record = authority.sync_authenticated_identity(
                connection,
                identity_id=identity_id,
                email=email,
                display_name=founder_activation.FOUNDER_DISPLAY_NAME,
                # The recovery proof + zero-user directory check is the trusted
                # one-time ownership ceremony for this replacement UUID.
                email_verified=True,
            )
            if not record.get("is_human_authority"):
                raise founder_activation.ActivationUnavailable(
                    "founder_authority_binding_failed"
                )
            connection.execute(
                """UPDATE oap_identities
                   SET status='SUSPENDED', updated_at=CURRENT_TIMESTAMP
                   WHERE identity_type='HUMAN_AUTHORITY'
                     AND status='ACTIVE'
                     AND identity_id<>%s""",
                (identity_id,),
            )
            connection.commit()
    except founder_activation.ActivationUnavailable:
        raise
    except Exception as exc:
        raise founder_activation.ActivationUnavailable(
            "founder_authority_binding_unavailable"
        ) from exc


@bp.route("/auth/recover-founder", methods=["GET", "POST"])
def recover_founder():
    """Open a short-lived Render-local Founder session during auth outages.

    The recovery credential is already a high-entropy server-side SHA-256 proof.
    A successful proof creates only the existing bounded recovery principal. If
    Managed Auth is provably empty, the user is sent to a separate one-time
    reactivation ceremony so future entry returns to the normal password lane.
    """

    if not founder_recovery.configured():
        return _hidden()

    next_path = _safe_next(request.values.get("next"))
    if request.method == "GET":
        if founder_recovery.session_active():
            if founder_activation.managed_directory_state() == "empty":
                return _no_store(
                    redirect(
                        url_for(
                            "founder_recovery.reactivate_founder",
                            next=next_path,
                        )
                    )
                )
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
    if founder_activation.managed_directory_state() == "empty":
        return _no_store(
            redirect(
                url_for(
                    "founder_recovery.reactivate_founder",
                    next=next_path,
                )
            )
        )
    return _no_store(redirect(next_path))


@bp.route("/auth/reactivate-founder", methods=["GET", "POST"])
def reactivate_founder():
    """Rebuild the normal Founder password identity after a valid recovery proof."""

    if not founder_recovery.session_active():
        return _hidden()

    next_path = _safe_next(request.values.get("next"))
    directory_state = founder_activation.managed_directory_state()
    if directory_state == "founder_present":
        founder_recovery.clear_session()
        return _no_store(redirect(url_for("auth_page", next=next_path)))
    if directory_state != "empty":
        return _render_reactivation(
            status_code=503,
            error="Normal Founder password reactivation is temporarily unavailable.",
            next_path=next_path,
        )
    if request.method == "GET":
        return _render_reactivation(next_path=next_path)

    if not web_security.csrf_valid(request):
        return _render_reactivation(
            status_code=403,
            error="Session expired. Refresh and try again.",
            next_path=next_path,
        )

    password = str(request.form.get("password", ""))[:129]
    confirmation = str(request.form.get("password_confirmation", ""))[:129]
    if password != confirmation:
        return _render_reactivation(
            status_code=400,
            error="The two private password entries do not match.",
            next_path=next_path,
        )
    if len(password) < 12 or len(password) > 128 or not password.strip():
        return _render_reactivation(
            status_code=400,
            error="Choose a private password between 12 and 128 characters.",
            next_path=next_path,
        )

    try:
        result = founder_activation.reactivate_managed_founder(password)
        identity_id = _result_identity(result)
        _bind_reactivated_authority(identity_id)
    except founder_activation.ActivationUnavailable:
        return _render_reactivation(
            status_code=503,
            error="Normal Founder password reactivation could not be completed safely.",
            next_path=next_path,
        )

    response = redirect(next_path)
    if not _apply_auth_cookies(response, result.set_cookie_headers):
        return _render_reactivation(
            status_code=502,
            error="A secure Founder session could not be established.",
            next_path=next_path,
        )
    return _no_store(response)
