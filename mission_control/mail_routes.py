"""Private OAP Mail outbound routes."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, render_template, request

from . import mail_mailbox, mail_outbound, web_security

bp = Blueprint("oap_mail", __name__)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@bp.get("/mail")
@web_security.login_required(founder_only=True)
def mailbox_home():
    folder = str(request.args.get("folder") or "inbox").strip().casefold()
    mailbox_state = mail_mailbox.status()
    items = []
    error = None
    if folder not in mail_mailbox.FOLDERS:
        folder = "inbox"
        error = "invalid_mail_folder"
    elif mailbox_state.get("ready"):
        try:
            items = mail_mailbox.list_folder(_identity(), folder)
        except (ValueError, mail_mailbox.MailboxUnavailable):
            error = "oap_mail_mailbox_unavailable"
    else:
        error = str(mailbox_state.get("error") or "oap_mail_mailbox_unavailable")
    return _no_store(
        make_response(
            render_template(
                "oap_mail.html",
                folder=folder,
                folders=tuple(sorted(mail_mailbox.FOLDERS)),
                items=items,
                mailbox=mailbox_state,
                outbound=mail_outbound.status(),
                error=error,
            ),
            200,
        )
    )


@bp.get("/mail/status")
def mail_status():
    return _no_store(make_response(jsonify(mail_outbound.status()), 200))


def _identity() -> str:
    return web_security.authenticated_identity()


def _mailbox_error(exc: Exception):
    if isinstance(exc, ValueError):
        return _no_store(make_response(jsonify(error={"code": str(exc)[:80]}), 400))
    if isinstance(exc, mail_mailbox.MailboxUnavailable):
        return _no_store(
            make_response(jsonify(error={"code": "oap_mail_mailbox_unavailable"}), 503)
        )
    return _no_store(
        make_response(jsonify(error={"code": "oap_mail_mailbox_unavailable"}), 503)
    )


@bp.get("/mail/mailbox/status")
@web_security.login_required(api=True, founder_only=True)
def mailbox_status():
    return _no_store(make_response(jsonify(mail_mailbox.status()), 200))


@bp.get("/mail/<folder>")
@web_security.login_required(api=True, founder_only=True)
def mailbox_folder(folder: str):
    try:
        items = mail_mailbox.list_folder(_identity(), folder)
        return _no_store(make_response(jsonify(folder=folder, items=items), 200))
    except Exception as exc:  # noqa: BLE001
        return _mailbox_error(exc)


@bp.get("/mail/search")
@web_security.login_required(api=True, founder_only=True)
def mailbox_search():
    try:
        items = mail_mailbox.search(_identity(), request.args.get("q"))
        return _no_store(make_response(jsonify(items=items), 200))
    except Exception as exc:  # noqa: BLE001
        return _mailbox_error(exc)


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
