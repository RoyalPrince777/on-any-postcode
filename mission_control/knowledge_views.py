"""Authenticated My World Vault API for private OAP Knowledge."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, request

from . import knowledge_core, public_store, web_security

bp = Blueprint("oap_knowledge", __name__)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _error(code: str, message: str, status_code: int):
    return _no_store(
        make_response(jsonify(error={"code": code, "message": message}), status_code)
    )


def _identity() -> str:
    user = web_security.current_authenticated_user()
    if user is None:
        raise PermissionError("authentication_required")
    public_store.ensure_authenticated_user(
        str(user["id"]),
        email=str(user["email"]),
        display_name=str(user["name"]),
        email_verified=bool(user.get("email_verified")),
    )
    return str(user["id"])


def _payload() -> dict[str, object]:
    value = request.get_json(silent=True)
    if not isinstance(value, dict):
        raise TypeError("json_object_required")
    return value


def _csrf_error():
    if web_security.csrf_valid(request):
        return None
    return _error("csrf_failed", "The secure session expired. Refresh and try again.", 403)


@bp.get("/my-world/vault/cards")
@web_security.login_required(api=True)
def list_cards():
    try:
        cards = knowledge_core.list_cards(_identity(), query=request.args.get("q", ""))
        return _no_store(make_response(jsonify(cards=cards)))
    except (ValueError, knowledge_core.KnowledgeUnavailable):
        return _error("vault_unavailable", "The private Vault is temporarily unavailable.", 503)


@bp.get("/my-world/vault/cards/<card_id>")
@web_security.login_required(api=True)
def get_card(card_id: str):
    try:
        card = knowledge_core.get_card(_identity(), card_id)
    except ValueError:
        return _error("invalid_card", "That knowledge card is invalid.", 400)
    except knowledge_core.KnowledgeUnavailable:
        return _error("vault_unavailable", "The private Vault is temporarily unavailable.", 503)
    if card is None:
        return _error("card_not_found", "That knowledge card was not found.", 404)
    return _no_store(make_response(jsonify(card=card)))


@bp.post("/my-world/vault/cards")
@web_security.login_required(api=True)
def create_card():
    csrf = _csrf_error()
    if csrf is not None:
        return csrf
    try:
        payload = _payload()
        card = knowledge_core.create_card(
            _identity(),
            title=payload.get("title"),
            insight=payload.get("insight"),
            summary=payload.get("summary"),
        )
        return _no_store(make_response(jsonify(card=card), 201))
    except (TypeError, ValueError) as exc:
        return _error(str(exc) or "invalid_request", "Check the card and try again.", 400)
    except knowledge_core.KnowledgeUnavailable:
        return _error("vault_unavailable", "The private Vault is temporarily unavailable.", 503)


@bp.put("/my-world/vault/cards/<card_id>")
@web_security.login_required(api=True)
def update_card(card_id: str):
    csrf = _csrf_error()
    if csrf is not None:
        return csrf
    try:
        payload = _payload()
        card = knowledge_core.update_card(
            _identity(),
            card_id,
            title=payload.get("title"),
            insight=payload.get("insight"),
            summary=payload.get("summary"),
        )
    except (TypeError, ValueError) as exc:
        return _error(str(exc) or "invalid_request", "Check the card and try again.", 400)
    except knowledge_core.KnowledgeUnavailable:
        return _error("vault_unavailable", "The private Vault is temporarily unavailable.", 503)
    if card is None:
        return _error("card_not_found", "That knowledge card was not found.", 404)
    return _no_store(make_response(jsonify(card=card)))


@bp.delete("/my-world/vault/cards/<card_id>")
@web_security.login_required(api=True)
def delete_card(card_id: str):
    csrf = _csrf_error()
    if csrf is not None:
        return csrf
    try:
        deleted = knowledge_core.delete_card(_identity(), card_id)
    except ValueError:
        return _error("invalid_card", "That knowledge card is invalid.", 400)
    except knowledge_core.KnowledgeUnavailable:
        return _error("vault_unavailable", "The private Vault is temporarily unavailable.", 503)
    if not deleted:
        return _error("card_not_found", "That knowledge card was not found.", 404)
    return _no_store(make_response(jsonify(deleted=True)))


@bp.post("/my-world/vault/collections")
@web_security.login_required(api=True)
def create_collection():
    csrf = _csrf_error()
    if csrf is not None:
        return csrf
    try:
        payload = _payload()
        collection = knowledge_core.create_collection(
            _identity(), title=payload.get("title")
        )
        return _no_store(make_response(jsonify(collection=collection), 201))
    except (TypeError, ValueError) as exc:
        return _error(str(exc) or "invalid_request", "Check the collection and try again.", 400)
    except knowledge_core.KnowledgeUnavailable:
        return _error("vault_unavailable", "The private Vault is temporarily unavailable.", 503)


@bp.post("/my-world/vault/collections/<collection_id>/cards/<card_id>")
@web_security.login_required(api=True)
def add_card_to_collection(collection_id: str, card_id: str):
    csrf = _csrf_error()
    if csrf is not None:
        return csrf
    try:
        linked = knowledge_core.add_card_to_collection(
            _identity(), collection_id, card_id
        )
    except ValueError:
        return _error("invalid_request", "That collection link is invalid.", 400)
    except knowledge_core.KnowledgeUnavailable:
        return _error("vault_unavailable", "The private Vault is temporarily unavailable.", 503)
    if not linked:
        return _error("not_found", "The card or collection was not found.", 404)
    return _no_store(make_response(jsonify(linked=True)))
