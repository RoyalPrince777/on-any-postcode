"""Standalone SIKA Global application shell.

Run locally with:
    flask --app sika_global_app run --port 5011
"""
from __future__ import annotations

import os
from decimal import Decimal
from flask import Flask, jsonify, make_response, render_template, request, send_from_directory

from mission_control import (
    sika_a5_preparation,
    sika_a6_readiness,
    sika_android_acceptance,
    sika_finance_features,
    sika_global,
    sika_intelligence,
    sika_open_banking,
    sika_os_alignment,
    sika_payment_licence_gate,
    sika_closed_loop_value,
    sika_deep_dive_21,
    sika_safety,
    sika_wallet_ledger,
)

app = Flask(__name__, template_folder="mission_control/templates")
STATIC_ROOT = os.path.join(app.root_path, "static")
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


@app.get("/manifest.webmanifest")
def oap_os_manifest():
    response = send_from_directory(
        STATIC_ROOT,
        "manifest.webmanifest",
        mimetype="application/manifest+json",
        max_age=3600,
    )
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response


@app.get("/service-worker.js")
def oap_os_service_worker():
    response = send_from_directory(
        STATIC_ROOT,
        "oap-os-sw.js",
        mimetype="application/javascript",
        max_age=0,
    )
    response.headers["Cache-Control"] = "no-cache"
    response.headers["Service-Worker-Allowed"] = "/"
    return response


@app.get("/assets/oap-os.js")
def oap_os_install_controller():
    return send_from_directory(
        STATIC_ROOT,
        "oap-os.js",
        mimetype="application/javascript",
        max_age=3600,
    )


@app.get("/assets/oap-os-icon-<int:size>.png")
def oap_os_icon(size):
    if size not in {192, 512}:
        response = make_response("", 404)
        response.headers["Cache-Control"] = "no-store"
        return response
    return send_from_directory(
        STATIC_ROOT,
        f"oap-os-icon-{size}.png",
        mimetype="image/png",
        max_age=86400,
    )


@app.get("/offline")
def oap_os_offline():
    response = send_from_directory(
        STATIC_ROOT,
        "oap-os-offline.html",
        mimetype="text/html",
        max_age=3600,
    )
    response.headers["Cache-Control"] = "public, max-age=3600"
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


@app.get("/api/sika/intelligence/alignment")
def sika_alignment_intelligence():
    return jsonify(sika_intelligence.alignment_intelligence())


@app.get("/api/sika/intelligence/bank")
def sika_bank_intelligence():
    return jsonify(sika_intelligence.bank_intelligence())


@app.post("/api/sika/fraud/preflight")
def sika_fraud_preflight():
    body = request.get_json(silent=True) or {}
    try:
        return jsonify(sika_safety.assess(body))
    except (sika_safety.FraudInputError, ValueError, ArithmeticError) as exc:
        return jsonify({"error": str(exc), "executable": False}), 400


@app.get("/api/sika/install/readiness")
def sika_install_readiness():
    return jsonify(sika_safety.install_readiness())


@app.get("/api/sika/payment-licence")
def sika_payment_licence_status():
    return jsonify(sika_payment_licence_gate.status())


@app.get("/api/sika/a5-preparation")
def sika_a5_preparation_status():
    return jsonify(sika_a5_preparation.pack())


@app.get("/api/sika/a6-readiness")
def sika_a6_readiness_status():
    return jsonify(sika_a6_readiness.status())


@app.get("/api/sika/a6-evidence-pack")
def sika_a6_evidence_pack():
    return jsonify(sika_a6_readiness.evidence_pack())


@app.get("/api/sika/open-banking/status")
def sika_open_banking_status():
    return jsonify(sika_open_banking.status())


@app.get("/api/sika/open-banking/trial")
def sika_open_banking_trial():
    return jsonify(sika_open_banking.trial_snapshot())


@app.get("/api/sika/open-banking/red-team")
def sika_open_banking_red_team():
    return jsonify(sika_open_banking.red_team())


@app.get("/api/sika/value-model")
def sika_value_model():
    return jsonify(sika_closed_loop_value.model_status())


@app.post("/api/sika/value-trial")
def sika_value_trial():
    body = request.get_json(silent=True) or {}
    receipt = sika_closed_loop_value.InboundReceipt(
        receipt_id=str(body.get("receipt_id") or "trial-receipt"),
        gbp_amount=str(body.get("gbp_amount") or "0"),
        bank_reference=str(body.get("bank_reference") or "sandbox-bank-ref"),
        settlement_verified=bool(body.get("settlement_verified", False)),
        safeguarding_or_partner_evidence=bool(body.get("safeguarding_or_partner_evidence", False)),
        regulatory_basis_verified=bool(body.get("regulatory_basis_verified", False)),
    )
    try:
        return jsonify(sika_closed_loop_value.issue_from_gbp(receipt))
    except sika_closed_loop_value.SikaValueError as exc:
        return jsonify({"error": str(exc), "issuance_authorised": False}), 400


@app.post("/api/sika/internal-transfer/preview")
def sika_internal_transfer_preview():
    body = request.get_json(silent=True) or {}
    try:
        return jsonify(sika_closed_loop_value.internal_transfer(
            body.get("amount_sika", "0"),
            sender_balance_sika=body.get("sender_balance_sika", "0"),
        ))
    except sika_closed_loop_value.SikaValueError as exc:
        return jsonify({"error": str(exc), "transfer_allowed": False}), 400


@app.get("/api/sika/android-acceptance")
def sika_android_acceptance_status():
    return jsonify(sika_android_acceptance.evaluate())


@app.get("/api/sika/os-alignment")
def sika_os_alignment_status():
    return jsonify(sika_os_alignment.status())


@app.get("/api/sika/deep-dive-21")
def sika_deep_dive_21_status():
    return jsonify(sika_deep_dive_21.status())
