"""Standalone SIKA Global application shell.

Run locally with:
    flask --app sika_global_app run --port 5011
"""
from __future__ import annotations

from decimal import Decimal
from flask import Flask, jsonify, render_template, request

from mission_control import sika_global

app = Flask(__name__, template_folder="mission_control/templates")


@app.after_request
def security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
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
    return render_template("sika_global.html", status=sika_global.status())


@app.get("/api/sika/status")
def sika_status():
    return jsonify(sika_global.status())


@app.post("/api/sika/quote")
def sika_quote():
    body = request.get_json(silent=True) or {}
    rates = body.get("gbp_per_unit") or {}
    try:
        quote = sika_global.quote_from_sika(
            body.get("amount_sika", "0"),
            body.get("currency", "GBP"),
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
