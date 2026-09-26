"""Founder-only, read-only SMI bank Mind evidence from the canonical contracts."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response

from . import bank_body_integration, bank_soul_policy, prince_sovereign_bank
from .web_security import login_required

bp = Blueprint("smi_bank_mind_controls", __name__)


@bp.get("/mission/smi/bank/mind")
@login_required(api=True, founder_only=True)
def mind():
    identity = prince_sovereign_bank.status()
    body = bank_body_integration.status()
    soul = bank_soul_policy.status()
    response = make_response(jsonify({
        "name": identity["name"],
        "heritage": identity["banking_family"],
        "brand_status": identity["brand_status"],
        "value_classes": identity["currency"]["value_classes"],
        "conversion_enabled": False,
        "identity_and_permissions_operationally_verified": False,
        "risk_engine_operationally_verified": False,
        "accounts_enabled": body["accounts_enabled"],
        "ledger_posting_enabled": body["ledger_posting_enabled"],
        "payment_execution_enabled": body["payment_execution_enabled"],
        "customer_approval_required": identity["customer_approval_required_for_transactions"],
        "founder_approval_is_not_customer_approval": soul["founder_institutional_approval_is_not_customer_approval"],
        "regulated_execution_enabled": identity["regulated_execution_enabled"],
        "install_enabled": soul["install_enabled"],
        "proof_scope": "read_only_contract",
        "release_proven": False,
    }))
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response
