"""Authenticated SIKA Global durable software routes."""
from __future__ import annotations

from flask import Blueprint, jsonify, render_template, request

from . import (
    sika_android_evidence_store,
    sika_authenticated_owner_adapter,
    sika_bank_credential_store,
    sika_device_binding_store,
    sika_finance_features,
    sika_global,
    sika_intelligence,
    sika_journal_store,
    sika_safety,
    sika_security_ledger,
    sika_wallet_ledger,
    web_security,
)

bp = Blueprint("sika_global", __name__)

_SIKA_SECURITY_LIMITER = web_security.SlidingWindowLimiter(
    limit=10,
    window_seconds=5 * 60,
    duplicate_seconds=0.5,
    fingerprint_request_body=True,
)


def _authenticated_sika_owner():
    return sika_authenticated_owner_adapter.resolve(
        web_security.authenticated_identity(),
        source="oap_authenticated_session",
    )


def _csrf_or_403():
    if web_security.csrf_valid(request):
        return None
    return jsonify({"error": "csrf_failed"}), 403


def _security_rate_or_429(owner_id: str):
    if _SIKA_SECURITY_LIMITER.allow(f"sika-bank-security:{owner_id}"):
        return None
    return jsonify({"error": "bank_app_security_rate_limited"}), 429


@bp.after_request
def _no_store(response):
    response.headers["Cache-Control"] = "no-store, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = (
        "camera=(), microphone=(), geolocation=(), display-capture=(), "
        "usb=(), payment=()"
    )
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
    owner = _authenticated_sika_owner()
    body = request.get_json(silent=True) or {}
    try:
        result = sika_safety.assess(body)
        severity = (
            "HIGH"
            if result.get("decision") == "block_software_only"
            else "WARNING"
            if result.get("decision") == "review"
            else "NOTICE"
        )
        receipt = sika_security_ledger.record_authenticated_owner(
            owner.owner_id,
            event_type="FRAUD_PREFLIGHT",
            severity=severity,
            details={
                "decision": result.get("decision"),
                "risk_score": result.get("risk_score"),
                "reasons": list(result.get("reasons") or []),
                "scam_detected": bool(result.get("scam_detected")),
            },
        )
        return jsonify({
            **result,
            "security_receipt_id": receipt.get("event_id"),
            "security_event_recorded": True,
        })
    except (sika_safety.FraudInputError, ValueError, ArithmeticError) as exc:
        return jsonify({"error": str(exc), "executable": False}), 400
    except sika_security_ledger.SikaSecurityLedgerUnavailable as exc:
        return jsonify({"error": str(exc), "executable": False}), 503


@bp.get("/api/sika/install/readiness")
@web_security.login_required(api=True)
def sika_install_readiness():
    return jsonify(sika_safety.install_readiness())


@bp.get("/api/sika/security/posture")
@web_security.login_required(api=True)
def sika_security_posture():
    return jsonify(sika_safety.security_posture())


@bp.get("/api/sika/security/session-policy")
@web_security.login_required(api=True)
def sika_security_session_policy():
    return jsonify(sika_safety.session_policy())


@bp.post("/api/sika/security/payment-controls")
@web_security.login_required(api=True)
def sika_security_payment_controls():
    if not web_security.csrf_valid(request):
        return jsonify({"error": "csrf_failed"}), 403
    owner = _authenticated_sika_owner()
    body = request.get_json(silent=True) or {}
    try:
        state = sika_security_ledger.latest_state(owner.owner_id)
        beneficiary_id = str(body.get("beneficiary_id") or "").strip()
        beneficiary_age = (
            sika_security_ledger.beneficiary_age_minutes(
                owner.owner_id, beneficiary_id
            )
            if beneficiary_id
            else 0
        )
        daily_activity = sika_security_ledger.daily_payment_activity(owner.owner_id)
        result = sika_safety.payment_controls({
            **body,
            "daily_used_sika": daily_activity["daily_attempted_sika"],
            "daily_limit_sika": state["daily_limit_sika"],
            "recipient_age_minutes": beneficiary_age,
            "suspicious_device": state["suspicious_device"],
        })
        payment_intent = None
        step_up = None
        elevated = (
            result.get("over_limit")
            or result.get("new_recipient_cooling_off")
            or result.get("suspicious_device")
            or result.get("step_up_required")
        )
        if elevated:
            payment_intent = sika_security_ledger.create_payment_intent(
                owner.owner_id,
                beneficiary_id=beneficiary_id or "unregistered-beneficiary",
                amount_sika=body.get("amount_sika", "0"),
                reference=body.get("reference", ""),
            )
            sika_security_ledger.record_authenticated_owner(
                owner.owner_id,
                event_type="PAYMENT_CONTROL_HOLD",
                severity="WARNING",
                details={
                    "over_limit": bool(result.get("over_limit")),
                    "new_recipient_cooling_off": bool(
                        result.get("new_recipient_cooling_off")
                    ),
                    "suspicious_device": bool(result.get("suspicious_device")),
                    "beneficiary_id": beneficiary_id,
                    "amount_sika": str(body.get("amount_sika") or "0"),
                    "payment_intent_id": payment_intent["payment_intent_id"],
                },
            )
            step_up = sika_security_ledger.create_step_up_for_payment_intent(
                owner.owner_id,
                payment_intent_id=payment_intent["payment_intent_id"],
                reason="elevated_payment_security_review",
                amount_sika=body.get("amount_sika", "0"),
            )
        return jsonify({
            **result,
            "payment_intent_id": (
                payment_intent["payment_intent_id"] if payment_intent else None
            ),
            "step_up_challenge_id": (
                step_up["challenge_id"] if step_up else None
            ),
            "payment_execution_authorised": False,
        })
    except (sika_safety.FraudInputError, ValueError, ArithmeticError) as exc:
        return jsonify({"error": str(exc), "executable": False}), 400
    except sika_security_ledger.SikaSecurityLedgerUnavailable as exc:
        return jsonify({"error": str(exc), "executable": False}), 503


@bp.get("/api/sika/security/ledger/readiness")
@web_security.login_required(api=True)
def sika_security_ledger_readiness():
    return jsonify(sika_security_ledger.readiness())


@bp.get("/api/sika/security/ledger/history")
@web_security.login_required(api=True)
def sika_security_ledger_history():
    owner = _authenticated_sika_owner()
    try:
        return jsonify({"events": sika_security_ledger.history(owner.owner_id)})
    except sika_security_ledger.SikaSecurityLedgerUnavailable as exc:
        return jsonify({"error": str(exc), "events": []}), 503


@bp.get("/api/sika/security/state")
@web_security.login_required(api=True)
def sika_security_state():
    owner = _authenticated_sika_owner()
    try:
        return jsonify(sika_security_ledger.latest_state(owner.owner_id))
    except sika_security_ledger.SikaSecurityLedgerUnavailable as exc:
        return jsonify({"error": str(exc), "durable": False}), 503


@bp.post("/api/sika/security/limit")
@web_security.login_required(api=True)
def sika_security_limit():
    csrf_error = _csrf_or_403()
    if csrf_error:
        return csrf_error
    owner = _authenticated_sika_owner()
    body = request.get_json(silent=True) or {}
    try:
        result = sika_security_ledger.set_transfer_limit(
            owner.owner_id, body.get("daily_limit_sika")
        )
    except ValueError as exc:
        return jsonify({"error": str(exc), "recorded": False}), 400
    except sika_security_ledger.SikaSecurityLedgerUnavailable as exc:
        return jsonify({"error": str(exc), "recorded": False}), 503
    return jsonify({**result, "recorded": True}), 201


@bp.post("/api/sika/security/beneficiary")
@web_security.login_required(api=True)
def sika_security_beneficiary():
    csrf_error = _csrf_or_403()
    if csrf_error:
        return csrf_error
    owner = _authenticated_sika_owner()
    body = request.get_json(silent=True) or {}
    try:
        result = sika_security_ledger.register_beneficiary(
            owner.owner_id, body.get("beneficiary_id")
        )
    except ValueError as exc:
        return jsonify({"error": str(exc), "recorded": False}), 400
    except sika_security_ledger.SikaSecurityLedgerUnavailable as exc:
        return jsonify({"error": str(exc), "recorded": False}), 503
    return jsonify({**result, "recorded": True}), 201


@bp.post("/api/sika/security/device-risk")
@web_security.login_required(api=True)
def sika_security_device_risk():
    csrf_error = _csrf_or_403()
    if csrf_error:
        return csrf_error
    owner = _authenticated_sika_owner()
    body = request.get_json(silent=True) or {}
    try:
        result = sika_security_ledger.set_device_risk(
            owner.owner_id, bool(body.get("suspicious_device"))
        )
    except sika_security_ledger.SikaSecurityLedgerUnavailable as exc:
        return jsonify({"error": str(exc), "recorded": False}), 503
    return jsonify({**result, "recorded": True}), 201


@bp.get("/api/sika/security/reauth-lock")
@web_security.login_required(api=True)
def sika_security_reauth_lock():
    owner = _authenticated_sika_owner()
    try:
        return jsonify(sika_security_ledger.reauth_lock_state(owner.owner_id))
    except sika_security_ledger.SikaSecurityLedgerUnavailable as exc:
        return jsonify({"error": str(exc), "locked": True}), 503


@bp.post("/api/sika/security/reauth-result")
@web_security.login_required(api=True)
def sika_security_reauth_result():
    csrf_error = _csrf_or_403()
    if csrf_error:
        return csrf_error
    owner = _authenticated_sika_owner()
    body = request.get_json(silent=True) or {}
    try:
        receipt = sika_security_ledger.record_reauth_result(
            owner.owner_id, success=bool(body.get("success"))
        )
        state = sika_security_ledger.reauth_lock_state(owner.owner_id)
        return jsonify({
            **state,
            "security_receipt_id": receipt.get("event_id"),
            "recorded": True,
        }), 201
    except sika_security_ledger.SikaSecurityLedgerUnavailable as exc:
        return jsonify({"error": str(exc), "recorded": False}), 503


@bp.get("/api/sika/security/daily-activity")
@web_security.login_required(api=True)
def sika_security_daily_activity():
    owner = _authenticated_sika_owner()
    try:
        return jsonify(sika_security_ledger.daily_payment_activity(owner.owner_id))
    except sika_security_ledger.SikaSecurityLedgerUnavailable as exc:
        return jsonify({"error": str(exc), "daily_executed_spend_sika": "0.00"}), 503


@bp.post("/api/sika/security/step-up")
@web_security.login_required(api=True)
def sika_security_step_up_create():
    csrf_error = _csrf_or_403()
    if csrf_error:
        return csrf_error
    owner = _authenticated_sika_owner()
    body = request.get_json(silent=True) or {}
    try:
        result = sika_security_ledger.create_step_up_challenge(
            owner.owner_id,
            reason=str(body.get("reason") or "security_review"),
            amount_sika=body.get("amount_sika", "0"),
        )
    except (ValueError, ArithmeticError) as exc:
        return jsonify({"error": str(exc), "created": False}), 400
    except sika_security_ledger.SikaSecurityLedgerUnavailable as exc:
        return jsonify({"error": str(exc), "created": False}), 503
    return jsonify({**result, "created": True}), 201


@bp.post("/api/sika/security/step-up/resolve")
@web_security.login_required(api=True)
def sika_security_step_up_resolve():
    csrf_error = _csrf_or_403()
    if csrf_error:
        return csrf_error
    owner = _authenticated_sika_owner()
    body = request.get_json(silent=True) or {}
    try:
        result = sika_security_ledger.resolve_step_up_challenge(
            owner.owner_id,
            challenge_id=body.get("challenge_id"),
            approved=bool(body.get("approved")),
        )
    except ValueError as exc:
        return jsonify({"error": str(exc), "resolved": False}), 400
    except sika_security_ledger.SikaSecurityLedgerUnavailable as exc:
        return jsonify({"error": str(exc), "resolved": False}), 503
    return jsonify({**result, "resolved": True})


@bp.post("/api/sika/security/alert/ack")
@web_security.login_required(api=True)
def sika_security_alert_ack():
    csrf_error = _csrf_or_403()
    if csrf_error:
        return csrf_error
    owner = _authenticated_sika_owner()
    body = request.get_json(silent=True) or {}
    try:
        return jsonify(sika_security_ledger.acknowledge_alert(
            owner.owner_id, body.get("security_event_id")
        ))
    except ValueError as exc:
        return jsonify({"error": str(exc), "acknowledged": False}), 400
    except sika_security_ledger.SikaSecurityLedgerUnavailable as exc:
        return jsonify({"error": str(exc), "acknowledged": False}), 503


@bp.post("/api/sika/security/alert/recover")
@web_security.login_required(api=True)
def sika_security_alert_recover():
    csrf_error = _csrf_or_403()
    if csrf_error:
        return csrf_error
    owner = _authenticated_sika_owner()
    body = request.get_json(silent=True) or {}
    try:
        return jsonify(sika_security_ledger.recover_alert(
            owner.owner_id, body.get("security_event_id")
        ))
    except ValueError as exc:
        return jsonify({"error": str(exc), "recovered": False}), 400
    except sika_security_ledger.SikaSecurityLedgerUnavailable as exc:
        return jsonify({"error": str(exc), "recovered": False}), 503


@bp.post("/api/sika/security/ledger/event")
@web_security.login_required(api=True)
def sika_security_ledger_event():
    csrf_error = _csrf_or_403()
    if csrf_error:
        return csrf_error
    owner = _authenticated_sika_owner()
    body = request.get_json(silent=True) or {}
    try:
        result = sika_security_ledger.record_authenticated_owner(
            owner.owner_id,
            event_type=str(body.get("event_type") or ""),
            severity=str(body.get("severity") or "NOTICE"),
            details=dict(body.get("details") or {}),
        )
    except ValueError as exc:
        return jsonify({"error": str(exc), "recorded": False}), 400
    except sika_security_ledger.SikaSecurityLedgerUnavailable as exc:
        return jsonify({"error": str(exc), "recorded": False}), 503
    return jsonify({**result, "recorded": True}), 201



@bp.post("/api/sika/security/credential/create")
@web_security.login_required(api=True)
def sika_bank_credential_create():
    csrf_error = _csrf_or_403()
    if csrf_error:
        return csrf_error
    owner = _authenticated_sika_owner()
    rate_error = _security_rate_or_429(owner.owner_id)
    if rate_error:
        return rate_error
    body = request.get_json(silent=True) or {}
    try:
        result = sika_bank_credential_store.create_authenticated_owner(
            owner.owner_id,
            body.get("password"),
        )
    except ValueError as exc:
        return jsonify({"error": str(exc), "created": False}), 400
    except sika_bank_credential_store.SikaCredentialStoreUnavailable as exc:
        return jsonify({"error": str(exc), "created": False}), 503
    return jsonify({
        **result,
        "authenticated_owner_source": owner.source,
        "caller_supplied_owner_id_trusted": False,
    }), (201 if result.get("created") else 409)


@bp.post("/api/sika/security/credential/verify")
@web_security.login_required(api=True)
def sika_bank_credential_verify():
    csrf_error = _csrf_or_403()
    if csrf_error:
        return csrf_error
    owner = _authenticated_sika_owner()
    rate_error = _security_rate_or_429(owner.owner_id)
    if rate_error:
        return rate_error
    body = request.get_json(silent=True) or {}
    try:
        result = sika_bank_credential_store.verify_authenticated_owner(
            owner.owner_id,
            body.get("password"),
        )
    except ValueError as exc:
        return jsonify({"error": str(exc), "verified": False}), 400
    except sika_bank_credential_store.SikaCredentialStoreUnavailable as exc:
        return jsonify({"error": str(exc), "verified": False}), 503
    return jsonify({
        **result,
        "authenticated_owner_source": owner.source,
        "caller_supplied_owner_id_trusted": False,
    }), (200 if result.get("verified") else 401)


@bp.post("/api/sika/security/credential/recover")
@web_security.login_required(api=True)
def sika_bank_credential_recover():
    csrf_error = _csrf_or_403()
    if csrf_error:
        return csrf_error
    owner = _authenticated_sika_owner()
    rate_error = _security_rate_or_429(owner.owner_id)
    if rate_error:
        return rate_error
    try:
        result = sika_bank_credential_store.recover_authenticated_owner(owner.owner_id)
    except sika_bank_credential_store.SikaCredentialStoreUnavailable as exc:
        return jsonify({"error": str(exc), "recovered": False}), 503
    return jsonify({
        **result,
        "authenticated_owner_source": owner.source,
        "caller_supplied_owner_id_trusted": False,
    }), (200 if result.get("recovered") else 404)


@bp.post("/api/sika/device/bind")
@web_security.login_required(api=True)
def sika_authenticated_device_bind():
    csrf_error = _csrf_or_403()
    if csrf_error:
        return csrf_error
    owner = _authenticated_sika_owner()
    body = request.get_json(silent=True) or {}
    try:
        result = sika_authenticated_owner_adapter.bind(owner, body.get("device_id"))
    except ValueError as exc:
        return jsonify({"error": str(exc), "bound": False}), 400
    except sika_device_binding_store.SikaDeviceBindingUnavailable as exc:
        return jsonify({"error": str(exc), "bound": False}), 503
    return jsonify(result), (201 if result.get("bound") else 409)


@bp.get("/api/sika/device/status")
@web_security.login_required(api=True)
def sika_authenticated_device_status():
    owner = _authenticated_sika_owner()
    try:
        result = sika_authenticated_owner_adapter.status(
            owner,
            request.args.get("device_id"),
        )
    except ValueError as exc:
        return jsonify({"error": str(exc), "matched": False}), 400
    except sika_device_binding_store.SikaDeviceBindingUnavailable as exc:
        return jsonify({"error": str(exc), "matched": False}), 503
    return jsonify(result)


@bp.post("/api/sika/device/recover")
@web_security.login_required(api=True)
def sika_authenticated_device_recover():
    csrf_error = _csrf_or_403()
    if csrf_error:
        return csrf_error
    owner = _authenticated_sika_owner()
    body = request.get_json(silent=True) or {}
    try:
        result = sika_authenticated_owner_adapter.recover(owner, body.get("device_id"))
    except ValueError as exc:
        return jsonify({"error": str(exc), "recovered": False}), 400
    except sika_device_binding_store.SikaDeviceBindingUnavailable as exc:
        return jsonify({"error": str(exc), "recovered": False}), 503
    return jsonify(result), (200 if result.get("recovered") else 404)



@bp.get("/api/sika/android/evidence/readiness")
@web_security.login_required(api=True)
def sika_android_evidence_readiness():
    return jsonify(sika_android_evidence_store.readiness())


@bp.get("/api/sika/android/evidence/latest")
@web_security.login_required(api=True)
def sika_android_evidence_latest():
    owner = _authenticated_sika_owner()
    try:
        return jsonify(sika_android_evidence_store.latest(owner.owner_id))
    except sika_android_evidence_store.SikaAndroidEvidenceUnavailable as exc:
        return jsonify({"error": str(exc), "real_android_pwa_acceptance": False}), 503


@bp.post("/api/sika/android/evidence")
@web_security.login_required(api=True)
def sika_android_evidence_record():
    csrf_error = _csrf_or_403()
    if csrf_error:
        return csrf_error
    owner = _authenticated_sika_owner()
    body = request.get_json(silent=True) or {}
    try:
        result = sika_android_evidence_store.record_authenticated_owner(
            owner.owner_id,
            body,
        )
    except ValueError as exc:
        return jsonify({"error": str(exc), "real_android_pwa_acceptance": False}), 400
    except sika_android_evidence_store.SikaAndroidEvidenceUnavailable as exc:
        return jsonify({"error": str(exc), "real_android_pwa_acceptance": False}), 503
    return jsonify({
        **result,
        "authenticated_owner_source": owner.source,
        "caller_supplied_owner_id_trusted": False,
    }), 201
