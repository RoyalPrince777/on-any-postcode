"""Authenticated Founder SIKA account provisioning HTTP bridge."""
from __future__ import annotations

from uuid import uuid4

from flask import Blueprint, jsonify

from . import sika_founder_account, web_security

bp = Blueprint("sika_founder_provision", __name__)


@bp.post("/pay/bank/founder/provision")
@web_security.login_required(api=True, founder_only=True)
def provision_founder_bank():
    """Provision only the currently authenticated Founder identity."""
    owner_reference = web_security.authenticated_identity()
    try:
        founder = sika_founder_account.provision(
            account_id=str(uuid4()),
            owner_reference=owner_reference,
            legal_entity="ON ANY POSTCODE LTD",
            jurisdiction="United Kingdom",
            currency="GBP",
            ledger_account_id=str(uuid4()),
        )
        response = jsonify({
            "founder": True,
            "sika_number": founder.sika_number,
            "account_status": founder.account.status,
            "currency": founder.account.currency,
            "treasury_authority": False,
            "creates_balance": False,
            "money_movement": False,
        })
    except sika_founder_account.FounderProvisioningError as exc:
        response = jsonify({"error": {"code": str(exc)}})
        response.status_code = 403
    except sika_founder_account.FounderProvisioningUnavailable:
        response = jsonify({"error": {"code": "founder_sika_provisioning_unavailable"}})
        response.status_code = 503
    response.headers["Cache-Control"] = "no-store"
    return response
