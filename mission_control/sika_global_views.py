"""Authenticated SIKA Global durable software routes."""
from __future__ import annotations

from flask import Blueprint, jsonify, render_template, request

from . import (
    sika_finance_features,
    sika_global,
    sika_intelligence,
    sika_journal_store,
    sika_safety,
    sika_wallet_ledger,
    web_security,
)

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


@bp.get("/api/sika/treasury/rates")
@web_security.login_required(api=True)
def sika_rates():
    owner = web_security.authenticated_identity()
    try:
        return jsonify({
            "rates": sika_journal_store.latest_treasury_rates(owner),
            "execution_enabled": False,
        })
    except sika_journal_store.SikaJournalUnavailable as exc:
        return jsonify({"error": str(exc)}), 503


@bp.post("/api/sika/treasury/rates")
@web_security.login_required(api=True)
def sika_rate_set():
    if not web_security.csrf_valid(request):
        return jsonify({"error": "csrf_failed"}), 403
    body = request.get_json(silent=True) or {}
    try:
        result = sika_journal_store.set_treasury_rate(
            web_security.authenticated_identity(),
            currency=str(body.get("currency") or ""),
            gbp_per_unit=body.get("gbp_per_unit", ""),
            source=str(body.get("source") or ""),
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except sika_journal_store.SikaJournalUnavailable as exc:
        return jsonify({"error": str(exc)}), 503
    return jsonify(result), 201


@bp.post("/api/sika/quote")
@web_security.login_required(api=True)
def sika_quote():
    body = request.get_json(silent=True) or {}
    owner = web_security.authenticated_identity()
    currency = str(body.get("currency") or "GBP")
    try:
        rates = sika_journal_store.latest_treasury_rates(owner)
        rate_map = {
            code: str(item["gbp_per_unit"])
            for code, item in rates.items()
        }
        quote = sika_global.quote_from_sika(
            body.get("amount_sika", "0"),
            currency,
            gbp_per_unit=rate_map,
            rate_source="durable_first_party_treasury",
        )
    except (sika_global.CurrencyError, ArithmeticError, sika_journal_store.SikaJournalUnavailable) as exc:
        return jsonify({"error": str(exc), "executable": False}), 400
    return jsonify(quote.as_dict())


@bp.post("/api/sika/cashback/quote")
@web_security.login_required(api=True)
def sika_cashback_quote():
    if not web_security.csrf_valid(request):
        return jsonify({"error": "csrf_failed"}), 403
    body = request.get_json(silent=True) or {}
    try:
        quote = sika_finance_features.cashback_quote(
            body.get("purchase_sika", "0"),
            body.get("rate_percent", "0"),
            funded_pool_available_sika=body.get("funded_pool_available_sika", "0"),
        )
    except (sika_finance_features.FinanceFeatureError, ArithmeticError) as exc:
        return jsonify({"error": str(exc), "executable": False}), 400
    return jsonify(quote.as_dict())


@bp.post("/api/sika/deferred/preview")
@web_security.login_required(api=True)
def sika_deferred_preview():
    if not web_security.csrf_valid(request):
        return jsonify({"error": "csrf_failed"}), 403
    body = request.get_json(silent=True) or {}
    try:
        return jsonify(sika_finance_features.deferred_payment_preview(
            body.get("purchase_sika", "0"),
            body.get("instalments", 3),
            monthly_disposable_sika=body.get("monthly_disposable_sika"),
        ))
    except (sika_finance_features.FinanceFeatureError, ArithmeticError) as exc:
        return jsonify({"error": str(exc), "executable": False}), 400


@bp.post("/api/sika/trust/preview")
@web_security.login_required(api=True)
def sika_trust_preview():
    if not web_security.csrf_valid(request):
        return jsonify({"error": "csrf_failed"}), 403
    body = request.get_json(silent=True) or {}
    try:
        return jsonify(sika_finance_features.trust_score_preview(
            payment_reliability=body.get("payment_reliability", 0),
            cashflow_resilience=body.get("cashflow_resilience", 0),
            account_stability=body.get("account_stability", 0),
            identity_confidence=body.get("identity_confidence", 0),
        ))
    except (sika_finance_features.FinanceFeatureError, ArithmeticError) as exc:
        return jsonify({"error": str(exc), "executable": False}), 400


@bp.post("/api/sika/security/freeze")
@web_security.login_required(api=True)
def sika_security_freeze():
    if not web_security.csrf_valid(request):
        return jsonify({"error": "csrf_failed"}), 403
    return jsonify({
        "security_action": "freeze_guard",
        "card_frozen": False,
        "payments_frozen": False,
        "reason": "no_live_card_or_payment_rail",
        "executable": False,
        "step_up_required_when_rails_exist": True,
    }), 423


@bp.get("/api/sika/intelligence/alignment")
@web_security.login_required(api=True)
def sika_alignment_intelligence():
    return jsonify(sika_intelligence.alignment_intelligence())


@bp.get("/api/sika/intelligence/bank")
@web_security.login_required(api=True)
def sika_bank_intelligence():
    return jsonify(sika_intelligence.bank_intelligence())


@bp.post("/api/sika/fraud/preflight")
@web_security.login_required(api=True)
def sika_fraud_preflight():
    if not web_security.csrf_valid(request):
        return jsonify({"error": "csrf_failed"}), 403
    body = request.get_json(silent=True) or {}
    try:
        return jsonify(sika_safety.assess(body))
    except (sika_safety.FraudInputError, ValueError, ArithmeticError) as exc:
        return jsonify({"error": str(exc), "executable": False}), 400


@bp.get("/api/sika/install/readiness")
@web_security.login_required(api=True)
def sika_install_readiness():
    return jsonify(sika_safety.install_readiness())
