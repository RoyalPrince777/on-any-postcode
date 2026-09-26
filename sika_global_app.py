"""Standalone SIKA Global application shell.

Run locally with:
    flask --app sika_global_app run --port 5011
"""
from __future__ import annotations

from decimal import Decimal
from flask import Flask, jsonify, render_template, request

from mission_control import sika_finance_features, sika_global, sika_wallet_ledger

app = Flask(__name__, template_folder="mission_control/templates")
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024


@app.after_request
def security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    response.headers.setdefault("Cache-Control", "no-store")
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; base-uri 'self'; frame-ancestors 'none'; "
        "form-action 'self'; object-src 'none'; img-src 'self' data:; "
        "style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'",
    )
    return response


@app.get("/")
@app.get("/sika")
def sika_home():
    return render_template(
        "sika_global.html",
        status=sika_global.status(),
        wallet={
            "owner_id": "local-founder",
            "balance_reference": f"{sika_wallet_ledger.balance_reference('local-founder'):.2f}",
            "history": sika_wallet_ledger.history("local-founder"),
            "rates": sika_wallet_ledger.list_rates(),
            "statement": {
                "entries": [],
                "entry_count": 0,
                "total_debits_sika": "0.00",
                "total_credits_sika": "0.00",
                "reconciled": True,
                "difference_sika": "0.00",
                "money_claim": False,
                "executable": False,
            },
        },
    )


@app.get("/api/sika/status")
def sika_status():
    return jsonify(sika_global.status())


@app.get("/api/sika/wallet")
def sika_wallet():
    owner_id = str(request.args.get("owner_id") or "local-founder")[:120]
    return jsonify({
        "owner_id": owner_id,
        "balance_reference": f"{sika_wallet_ledger.balance_reference(owner_id):.2f}",
        "history": sika_wallet_ledger.history(owner_id),
        "money_claim": False,
        "executable": False,
    })


@app.post("/api/sika/ledger/reference")
def sika_ledger_reference():
    body = request.get_json(silent=True) or {}
    try:
        item = sika_wallet_ledger.record_entry(
            str(body.get("owner_id") or "local-founder")[:120],
            str(body.get("kind") or ""),
            body.get("amount_sika", "0"),
            memo=str(body.get("memo") or ""),
        )
    except (ValueError, ArithmeticError) as exc:
        return jsonify({"error": str(exc), "executable": False}), 400
    return jsonify({
        "entry": item.__dict__,
        "money_moved": False,
        "executable": False,
    }), 201


@app.get("/api/sika/treasury/rates")
def sika_treasury_rates():
    return jsonify({
        "rates": sika_wallet_ledger.list_rates(),
        "execution_enabled": False,
    })


@app.post("/api/sika/treasury/rates")
def sika_treasury_rate_set():
    body = request.get_json(silent=True) or {}
    try:
        item = sika_wallet_ledger.set_rate(
            str(body.get("currency") or ""),
            body.get("gbp_per_unit", ""),
            source=str(body.get("source") or ""),
        )
    except (sika_global.CurrencyError, ArithmeticError) as exc:
        return jsonify({"error": str(exc), "executable": False}), 400
    return jsonify({"rate": item.__dict__, "execution_enabled": False}), 201


@app.post("/api/sika/quote")
def sika_quote():
    body = request.get_json(silent=True) or {}
    rates = body.get("gbp_per_unit") or {}
    currency = str(body.get("currency", "GBP"))
    if currency.upper() != "GBP" and currency.upper() not in rates:
        snapshot = sika_wallet_ledger.get_rate(currency)
        if snapshot is not None:
            rates = {**rates, snapshot.currency: snapshot.gbp_per_unit}
    try:
        quote = sika_global.quote_from_sika(
            body.get("amount_sika", "0"),
            currency,
            gbp_per_unit=rates,
            rate_source=str(body.get("rate_source") or "first_party_treasury_snapshot")[:80],
        )
    except (sika_global.CurrencyError, ArithmeticError) as exc:
        return jsonify({"error": str(exc), "executable": False}), 400
    return jsonify(quote.as_dict())


@app.post("/api/sika/pay")
@app.post("/api/sika/card")
@app.post("/api/sika/cash-out")
def regulated_action_blocked():
    return jsonify({
        "status": "blocked",
        "reason": "regulated_execution_not_enabled",
        "money_moved": False,
        "human_approval_required": True,
    }), 423


@app.post("/api/sika/cashback/quote")
def sika_cashback_quote():
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


@app.post("/api/sika/deferred/preview")
def sika_deferred_preview():
    body = request.get_json(silent=True) or {}
    try:
        return jsonify(sika_finance_features.deferred_payment_preview(
            body.get("purchase_sika", "0"),
            body.get("instalments", 3),
            monthly_disposable_sika=body.get("monthly_disposable_sika"),
        ))
    except (sika_finance_features.FinanceFeatureError, ArithmeticError) as exc:
        return jsonify({"error": str(exc), "executable": False}), 400


@app.post("/api/sika/trust/preview")
def sika_trust_preview():
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


@app.post("/api/sika/security/freeze")
def sika_security_freeze():
    return jsonify({
        "security_action": "freeze_preview",
        "card_frozen": False,
        "payments_frozen": False,
        "reason": "no_live_card_or_payment_rail",
        "executable": False,
    }), 423
