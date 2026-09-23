"""Authenticated private OAP Mail API; no send/delivery interface."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, request

from . import mail_smi_adapter, mail_store, public_store, web_security
from .mail_contract import require_folder

bp = Blueprint("oap_mail_private", __name__)


def _reply(payload: dict, status: int = 200):
    response = make_response(jsonify(payload), status)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@bp.get("/mail/<folder>")
@web_security.login_required(api=True)
def folder_items(folder: str):
    try:
        owner_id = web_security.authenticated_identity()
        items = mail_store.list_items(owner_id, owner_id, require_folder(folder))
    except ValueError:
        return _reply({"error": {"code": "mail_folder_invalid"}}, 400)
    except PermissionError:
        return _reply({"error": {"code": "mail_owner_required"}}, 403)
    except mail_store.MailUnavailable:
        return _reply({"error": {"code": "mail_store_unavailable"}}, 503)
    return _reply({"items": items, "delivery_enabled": False})


@bp.post("/mail/drafts")
@web_security.login_required(api=True)
def create_draft():
    if not web_security.csrf_valid(request):
        return _reply({"error": {"code": "csrf_failed"}}, 403)
    owner_id = web_security.authenticated_identity()
    if not web_security.PUBLIC_WRITE_LIMITER.allow(owner_id):
        return _reply({"error": {"code": "rate_limited"}}, 429)
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _reply({"error": {"code": "json_object_required"}}, 400)
    user = web_security.current_authenticated_user()
    try:
        public_store.ensure_authenticated_user(
            owner_id, email=str(user["email"]), display_name=str(user["name"]),
        )
        draft_id = mail_store.save_draft(
            owner_id, owner_id, subject=payload.get("subject"),
            body=payload.get("body"), correspondent=payload.get("correspondent"),
        )
    except (TypeError, ValueError) as exc:
        return _reply({"error": {"code": str(exc)}}, 400)
    except PermissionError:
        return _reply({"error": {"code": "mail_owner_required"}}, 403)
    except (mail_store.MailUnavailable, public_store.PublicStoreUnavailable):
        return _reply({"error": {"code": "mail_store_unavailable"}}, 503)
    return _reply({"draft_id": draft_id, "sent": False}, 201)



@bp.post("/mail/smi/read")
@web_security.login_required(api=True)
def smi_read_owner_folder():
    """One explicit, authenticated, consented read; no retained Mail authority."""
    if not web_security.csrf_valid(request):
        return _reply({"error": {"code": "csrf_failed"}}, 403)
    owner_id = web_security.authenticated_identity()
    if not web_security.PUBLIC_WRITE_LIMITER.allow(owner_id):
        return _reply({"error": {"code": "rate_limited"}}, 429)
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _reply({"error": {"code": "json_object_required"}}, 400)
    if "owner_id" in payload or "mailbox_owner_id" in payload:
        return _reply({"error": {"code": "mail_owner_override_forbidden"}}, 403)
    try:
        result = mail_smi_adapter.read_owner_folder(
            actor_id=owner_id,
            mailbox_owner_id=owner_id,
            folder=payload.get("folder"),
            owner_consent=payload.get("owner_consent") is True,
            ability=payload.get("ability", "mail.read"),
        )
    except ValueError:
        return _reply({"error": {"code": "mail_folder_invalid"}}, 400)
    except PermissionError:
        return _reply({"error": {"code": "mail_smi_access_denied"}}, 403)
    except mail_store.MailUnavailable:
        return _reply({"error": {"code": "mail_store_unavailable"}}, 503)
    return _reply(result)
