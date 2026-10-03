"""OAP Pay public front door.

This is the canonical user-facing payment surface for OAP World. It composes
existing SIKA controls and exposes capability truth. It does not itself call a
payment provider, settle funds, or move money.
"""
from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify, make_response, render_template

from . import (
    oap_pay_intelligence,
    oap_pay_requests,
    sika_customer_payment_authority,
    sika_execution_gate,
    sika_pay_gateway,
)

bp = Blueprint("oap_pay", __name__)

FEATURES = (
    {"id": "pay", "name": "Pay", "capability": "execute_payments"},
    {"id": "request", "name": "Request", "capability": "execute_payments"},
    {"id": "wallet", "name": "Wallet", "capability": "hold_customer_funds"},
    {"id": "activity", "name": "Activity", "capability": None},
    {"id": "business", "name": "Business", "capability": "execute_payments"},
)


def public_status() -> dict[str, Any]:
    try:
        matrix = sika_execution_gate.capability_matrix()
        evidence_available = True
    except (
        sika_execution_gate.bank_authorisation_store.BankEvidenceUnavailable,
        sika_execution_gate.bank_permission_scope.PermissionScopeUnavailable,
        sika_execution_gate.sika_production_evidence_store.ProductionEvidenceUnavailable,
    ):
        matrix = {}
        evidence_available = False

    features = []
    for item in FEATURES:
        capability = item["capability"]
        enabled = True if capability is None else bool(matrix.get(capability, False))
        features.append({**item, "enabled": enabled})

    return {
        "system": "OAP Pay",
        "tagline": "One OAP payment door.",
        "features": features,
        "evidence_available": evidence_available,
        "sika_pay_gateway": bool(sika_pay_gateway.status().get("single_payment_door")),
        "customer_payment_authority_required": bool(
            sika_customer_payment_authority.status().get("customer_authority_required")
        ),
        "real_payment_execution_enabled": bool(matrix.get("execute_payments", False)),
        "customer_fund_holding_enabled": bool(matrix.get("hold_customer_funds", False)),
        "provider_calling": False,
        "money_movement": False,
        "intelligence": oap_pay_intelligence.status(),
        "payment_requests": oap_pay_requests.status(),
        "human_authority_final": True,
    }


def _page():
    response = make_response(render_template("oap_pay.html", pay=public_status()))
    response.headers["Cache-Control"] = "no-store"
    return response


@bp.get("/pay")
def pay_home():
    return _page()


@bp.get("/oap-pay")
def pay_alias():
    return _page()


@bp.get("/pay/status")
def pay_status():
    response = jsonify(public_status())
    response.headers["Cache-Control"] = "no-store"
    return response


@bp.get("/pay/r/<token>")
def public_payment_request(token: str):
    item = oap_pay_requests.read_public_request(token)
    if item is None:
        response = jsonify({"error": {"code": "payment_request_not_found"}})
        response.status_code = 404
    else:
        response = jsonify(item)
    response.headers["Cache-Control"] = "no-store"
    return response
