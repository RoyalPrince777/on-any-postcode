"""OAP Pay public front door.

This is the canonical user-facing payment surface for OAP World. It composes
existing SIKA controls and exposes capability truth. It does not itself call a
payment provider, settle funds, or move money.
"""
from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify, make_response, render_template

from . import (
    bank_authorisation,
    bank_authorisation_store,
    bank_permission_scope,
    oap_pay_intelligence,
    oap_pay_requests,
    sika_customer_payment_authority,
    sika_execution_gate,
    sika_pay_gateway,
    sika_production_evidence_store,
)

bp = Blueprint("oap_pay", __name__)

PHONE_PAYMENT_METHODS = (
    {"id": "qr", "name": "Scan QR", "enabled": True, "requires": None},
    {"id": "link", "name": "Payment Link", "enabled": True, "requires": None},
    {"id": "tap", "name": "Tap to Pay", "enabled": False, "requires": "contactless_provider_authority"},
    {"id": "phone", "name": "Phone-to-Phone", "enabled": False, "requires": "contactless_provider_authority"},
)

FEATURES = (
    {"id": "home", "name": "Home", "description": "Balance view, incoming requests, recent activity.", "capability": None, "section": "primary"},
    {"id": "pay", "name": "Pay", "description": "Send payment through the governed SIKA Pay door.", "capability": "execute_payments", "section": "primary"},
    {"id": "request", "name": "Request", "description": "Create payment request, link or QR-ready request.", "capability": None, "section": "primary"},
    {"id": "wallet", "name": "Wallet", "description": "SIKA wallet/account view.", "capability": "hold_customer_funds", "section": "more"},
    {"id": "activity", "name": "Activity", "description": "Payments, requests, submissions, disputes and refunds.", "capability": None, "section": "primary"},
    {"id": "business", "name": "Business", "description": "Merchant tools, checkout and sales activity.", "capability": "execute_payments", "section": "more"},
    {"id": "sika", "name": "SIKA", "description": "Currency view, value classes and issuance status.", "capability": None, "section": "primary"},
    {"id": "treasury", "name": "Treasury", "description": "Liquidity, reserves, commitments and release gates.", "capability": None, "section": "more"},
    {"id": "rights", "name": "Rights & Remedy", "description": "Rights decisions, explanations, appeals and disputes.", "capability": None, "section": "more"},
    {"id": "guardian", "name": "Guardian", "description": "Fraud/risk warnings and human-review gates.", "capability": None, "section": "more"},
    {"id": "cards", "name": "Cards", "description": "Locked until real card authority/provider evidence exists.", "capability": "issue_payment_cards", "section": "regulated"},
    {"id": "cash", "name": "Cash / Post Office", "description": "Locked until lawful cash-in/out capability is proven.", "capability": "cash_out", "section": "regulated"},
    {"id": "fx", "name": "FX", "description": "Locked until foreign-exchange permission and execution are proven.", "capability": "foreign_exchange", "section": "regulated"},
    {"id": "bank", "name": "Bank", "description": "Accounts/deposits capability screen, evidence-gated.", "capability": "bank_accounts", "section": "regulated"},
    {"id": "smi-pay", "name": "SMI Pay", "description": "Intelligence dashboard across all payment-control layers.", "capability": None, "section": "more"},
    {"id": "settings", "name": "Settings", "description": "Security, authority, privacy, notifications and limits.", "capability": None, "section": "more"},
    {"id": "control-center", "name": "Control Center", "description": "Founder/admin evidence gates, provider status and regulator scope.", "capability": None, "section": "admin"},
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
        "phone_payment_methods": [dict(item) for item in PHONE_PAYMENT_METHODS],
        "primary_menu": [item for item in features if item["section"] == "primary"],
        "more_menu": [item for item in features if item["section"] == "more"],
        "regulated_menu": [item for item in features if item["section"] == "regulated"],
        "admin_menu": [item for item in features if item["section"] == "admin"],
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



def bank_status() -> dict[str, Any]:
    """Return a read-only bank truth projection from governed evidence stores."""

    try:
        readiness = bank_authorisation_store.readiness_status()
        scope = bank_permission_scope.current_scope()
        production = sika_production_evidence_store.readiness_status()
        matrix = sika_execution_gate.capability_matrix()
        evidence_available = True
    except (
        bank_authorisation_store.BankEvidenceUnavailable,
        bank_permission_scope.PermissionScopeUnavailable,
        sika_production_evidence_store.ProductionEvidenceUnavailable,
    ):
        readiness = bank_authorisation.readiness_status()
        scope = None
        production = {
            "evidence_total": len(sika_production_evidence_store.PRODUCTION_EVIDENCE),
            "evidence_proven": 0,
            "evidence_missing": tuple(sika_production_evidence_store.PRODUCTION_EVIDENCE),
            "production_gate_passed": False,
            "money_movement_enabled": False,
            "human_authority_final": True,
        }
        matrix = {capability: False for capability in bank_authorisation.REGULATED_CAPABILITIES}
        evidence_available = False

    return {
        "institution": readiness["institution"],
        "parent": readiness["parent"],
        "jurisdiction": readiness["jurisdiction"],
        "route": readiness["route"],
        "evidence_available": evidence_available,
        "evidence_total": readiness["evidence_total"],
        "evidence_proven": readiness["evidence_proven"],
        "application_ready": readiness["application_ready"],
        "authorised_bank": readiness["authorised_bank"],
        "permission_scope_present": scope is not None,
        "permission_scope_effective": bool(scope and scope.effective()),
        "permission_scope_capabilities": sorted(scope.permitted_capabilities) if scope else [],
        "mobilisation": bool(scope and scope.mobilisation),
        "deposit_cap_gbp": str(scope.deposit_cap_gbp) if scope and scope.deposit_cap_gbp is not None else None,
        "production_evidence_total": production["evidence_total"],
        "production_evidence_proven": production["evidence_proven"],
        "production_gate_passed": bool(production["production_gate_passed"]),
        "capabilities": matrix,
        "bank_accounts_enabled": bool(matrix.get("bank_accounts", False)),
        "deposit_taking_enabled": bool(matrix.get("accept_deposits", False)),
        "customer_fund_holding_enabled": bool(matrix.get("hold_customer_funds", False)),
        "regulated_execution_enabled": any(matrix.values()),
        "money_movement_enabled": False,
        "humanitarian_or_human_rights_purpose_bypasses_authorisation": False,
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


@bp.get("/pay/bank")
def bank_page():
    response = make_response(render_template("oap_pay_bank.html", bank=bank_status()))
    response.headers["Cache-Control"] = "no-store"
    return response


@bp.get("/pay/bank/status")
def bank_status_api():
    response = jsonify(bank_status())
    response.headers["Cache-Control"] = "no-store"
    return response


@bp.get("/pay/bank/manifest.webmanifest")
def bank_manifest():
    manifest = {
        "id": "/pay/bank",
        "name": "OAP Bank",
        "short_name": "OAP Bank",
        "description": "Evidence-gated OAP Bank capability and readiness dashboard.",
        "start_url": "/pay/bank",
        "scope": "/pay/bank",
        "display": "standalone",
        "background_color": "#050706",
        "theme_color": "#050706",
        "icons": [
            {"src": "/assets/oap-os-icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/assets/oap-os-icon-512.png", "sizes": "512x512", "type": "image/png"},
        ],
        "shortcuts": [
            {"name": "Bank Status", "short_name": "Status", "url": "/pay/bank"},
            {"name": "Capability Status", "short_name": "Capabilities", "url": "/pay/bank#capabilities"},
            {"name": "OAP Pay", "short_name": "OAP Pay", "url": "/pay"},
        ],
    }
    response = jsonify(manifest)
    response.content_type = "application/manifest+json"
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response
