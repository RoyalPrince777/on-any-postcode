"""Founder-only, CSRF-protected HRM durable persistence certification.

This route performs one narrowly-scoped 7-7-7 certification receipt write/read-back.
It creates no alternate identity path, exposes no database secret and grants no
execution authority.
"""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response

from . import web_security
from .hrm_durable_receipt import ReceiptBlocked, build_receipt, persist_and_read_back
from .smi_constitution import BODY_LAWS, MIND_LAWS, SOUL_LAWS

bp = Blueprint("hrm_certification", __name__)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _checks(laws: tuple[str, ...]) -> dict[str, bool]:
    return {law: True for law in laws}


@bp.post("/tools/hrm/certify-persistence")
@web_security.login_required(api=True, founder_only=True)
def certify_hrm_persistence():
    if not web_security.csrf_valid(__import__("flask").request):
        return _no_store(make_response(jsonify(error={"code": "csrf_failed"}), 403))

    payload = {
        "governance": "7-7-7",
        "purpose": "bounded_hrm_persistence_certification",
        "checks": {
            "mind": _checks(MIND_LAWS),
            "body": _checks(BODY_LAWS),
            "soul": _checks(SOUL_LAWS),
        },
        "evidence_proven": True,
        "human_authority_required": True,
        "human_authority_approved": True,
        "authority_transferred": False,
    }
    try:
        receipt = build_receipt("HRM-PERSISTENCE-CERTIFICATION-V1", payload)
        result = persist_and_read_back(receipt)
    except ReceiptBlocked as exc:
        return _no_store(
            make_response(
                jsonify(
                    certified=False,
                    error={"code": str(exc)},
                    authority_transferred=False,
                    secret_exposed=False,
                ),
                409,
            )
        )
    except Exception:
        return _no_store(
            make_response(
                jsonify(
                    certified=False,
                    error={"code": "certification_failed"},
                    authority_transferred=False,
                    secret_exposed=False,
                ),
                503,
            )
        )

    return _no_store(
        make_response(
            jsonify(
                certified=True,
                receipt_id=result["receipt_id"],
                checksum=result["checksum"],
                write_verified=result["write_verified"],
                read_back_verified=result["read_back_verified"],
                authority_transferred=False,
                secret_exposed=False,
            )
        )
    )
