"""Private OAP Mail outbound routes."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, request

from . import mail_outbound, web_security

bp = Blueprint("oap_mail", __name__)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@bp.get("/mail/status")
def mail_status():
    return _no_store(make_response(jsonify(mail_outbound.status()), 200))


@bp.post("/mail/send")
@web_security.login_required(api=True, founder_only=True)
def mail_send():
    if not web_security.csrf_valid(request):
        return _no_store(
            make_response(jsonify(error={"code": "csrf_failed"}), 403)
        )
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _no_store(
            make_response(jsonify(error={"code": "invalid_request"}), 400)
        )
    try:
        receipt = mail_outbound.send(
            recipients=payload.get("to"),
            subject=payload.get("subject"),
            body=payload.get("body"),
        )
    except ValueError as exc:
        return _no_store(
            make_response(jsonify(error={"code": str(exc)[:80]}), 400)
        )
    except mail_outbound.MailUnavailable as exc:
        code = str(exc)[:80]
        status = 503 if code in {
            "oap_mail_send_disabled",
            "oap_mail_relay_not_configured",
            "oap_mail_relay_unavailable",
        } else 502
        return _no_store(make_response(jsonify(error={"code": code}), status))
    return _no_store(make_response(jsonify(receipt), 202))
