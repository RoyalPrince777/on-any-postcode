from flask import Blueprint, jsonify, request
import os, time

bank_intelligence = Blueprint('bank_intelligence', __name__)

DOMAINS = [
    'money_basics','accounts','saving','budgeting','payments_literacy','credit_debt',
    'fraud_scam_awareness','consumer_protection','business_finance_basics','sika_boundaries',
    'banking_compliance','financial_education'
]


def _enabled(name):
    return os.environ.get(name,'').strip().lower() in {'1','true','yes','enabled','authorised','authorized'}


def register_bank_intelligence(app, db, uid):
    def now(): return int(time.time())

    with db() as c:
        c.execute("create table if not exists oap_bank_intelligence_registry(name text primary key,status text not null,legal_state text not null,updated_at bigint not null)")
        c.execute("insert into oap_bank_intelligence_registry(name,status,legal_state,updated_at) values('bank_intelligence','active','education_and_advisory_only',%s) on conflict(name) do update set status=excluded.status,legal_state=excluded.legal_state,updated_at=excluded.updated_at",(now(),))

    @bank_intelligence.get('/api/bank-intelligence/health')
    def health():
        authorised=_enabled('OAP_BANKING_AUTHORISED')
        return jsonify(
            ok=True,
            service='oap-bank-intelligence',
            intelligence_live=True,
            banking_service_live=authorised,
            legal_state='authorised' if authorised else 'education_and_advisory_only',
            authority='human_final',
            autonomous_financial_execution=False,
        )

    @bank_intelligence.get('/api/bank-intelligence')
    def overview():
        authorised=_enabled('OAP_BANKING_AUTHORISED')
        return jsonify(
            name='Bank Intelligence',
            parent='ON ANY POSTCODE Intelligence',
            institutional_context='Prince Sovereign Bank',
            domains=DOMAINS,
            purpose='financial_literacy_risk_compliance_and_future_bank_readiness',
            can_explain=True,
            can_assess_risk=True,
            can_move_money=False,
            can_open_accounts=False,
            can_issue_cards=False,
            can_accept_deposits=False,
            regulated_banking_enabled=authorised,
            no_licence_claim=not authorised,
            sika_is_legal_tender=False,
            authority='human_final',
        )

    @bank_intelligence.post('/api/bank-intelligence/check')
    def check():
        d=request.get_json(silent=True) or {}
        action=str(d.get('action','')).strip().lower()[:80]
        regulated={'open_account','accept_deposit','transfer_money','issue_card','lend','exchange_currency','hold_client_funds'}
        if action in regulated and not _enabled('OAP_BANKING_AUTHORISED'):
            return jsonify(ok=False,action=action,status='blocked_pending_authorisation',execution=False,authority='human_final'),403
        if not action:
            return jsonify(error='action_required'),400
        return jsonify(ok=True,action=action,status='advisory_only',execution=False,authority='human_final')

    @bank_intelligence.get('/api/bank-intelligence/sika')
    def sika_boundary():
        regulated=_enabled('OAP_SIKA_REGULATED_ENABLED')
        return jsonify(
            sika_role='created_value_loyalty_credits_vouchers_and_recognition',
            legal_tender=False,
            regulated_payments_enabled=regulated,
            wallet_transfer_card_execution=regulated,
            bank_separate=True,
            authority='human_final',
        )

    app.register_blueprint(bank_intelligence)
