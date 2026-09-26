"""Authenticated SIKA Global durable software routes."""
from __future__ import annotations

from flask import Blueprint, jsonify, render_template, request

from . import sika_global, sika_journal_store, sika_wallet_ledger, web_security

bp = Blueprint("sika_global", __name__)


@bp.after_request
def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    return response


@bp.get("/sika")
@web_security.login_required()
def sika_home():
    user = web_security.current_authenticated_user()
    owner_id = str(user["id"])
    try:
        statement = sika_journal_store.statement(owner_id)
    except sika_journal_store.SikaJournalUnavailable:
        statement = {
            "entries": [],
            "entry_count": 0,
            "total_debits_sika": "0.00",
            "total_credits_sika": "0.00",
            "reconciled": False,
            "difference_sika": "0.00",
            "unavailable": True,
        }
    return render_template(
        "sika_global.html",
        status=sika_global.status(),
        wallet={
            "owner_id": owner_id,
            "balance_reference": f"{sika_wallet_ledger.balance_reference(owner_id):.2f}",
            "history": sika_wallet_ledger.history(owner_id),
            "rates": sika_wallet_ledger.list_rates(),
            "statement": statement,
        },
    )


@bp.get("/api/sika/statement")
@web_security.login_required(api=True)
def sika_statement():
    owner = web_security.authenticated_identity()
    try:
        return jsonify(sika_journal_store.statement(owner))
    except sika_journal_store.SikaJournalUnavailable as exc:
        return jsonify({"error": str(exc)}), 503


@bp.post("/api/sika/journal/reference")
@web_security.login_required(api=True)
def sika_journal_reference():
    if not web_security.csrf_valid(request):
        return jsonify({"error": "csrf_failed"}), 403
    body = request.get_json(silent=True) or {}
    try:
        result = sika_journal_store.post_reference(
            web_security.authenticated_identity(),
            debit_account=str(body.get("debit_account") or ""),
            credit_account=str(body.get("credit_account") or ""),
            amount_sika=body.get("amount_sika", "0"),
            memo=str(body.get("memo") or ""),
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except sika_journal_store.SikaJournalUnavailable as exc:
        return jsonify({"error": str(exc)}), 503
    return jsonify(result), 201
