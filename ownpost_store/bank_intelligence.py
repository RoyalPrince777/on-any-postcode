from flask import Blueprint, jsonify, request
import os, time

bank_intelligence = Blueprint('bank_intelligence', __name__)

DOMAINS = [
    'money_basics','accounts','saving','budgeting','payments_literacy','credit_debt',
    'fraud_scam_awareness','consumer_protection','business_finance_basics','sika_boundaries',
    'banking_compliance','financial_education','global_money','family_banking','human_support'
]

ACCOUNT_MODES = [
    'personal','joint','family','youth','young_adult','business','elder_safe'
]

FEATURES = [
    {'slug':'smart_accounts','name':'Smart Accounts','role':'account structures and money views','regulated_execution':True},
    {'slug':'royal_pots','name':'Royal Pots','role':'bills, rent, food, travel, emergency, goals and savings buckets','regulated_execution':False},
    {'slug':'money_intelligence','name':'Money Intelligence','role':'spending categories, budgets, cash-flow explanations and safe-to-spend simulations','regulated_execution':False},
    {'slug':'salary_intelligence','name':'Salary Intelligence','role':'salary split planning across bills, savings, goals and spending','regulated_execution':False},
    {'slug':'card_intelligence','name':'Card Intelligence','role':'freeze, controls, virtual-card concepts, travel and merchant-risk guidance','regulated_execution':True},
    {'slug':'family_banking_intelligence','name':'Family Banking Intelligence','role':'age-appropriate money learning, guardian controls and progressive independence','regulated_execution':False},
    {'slug':'fraud_guardian','name':'Fraud Guardian','role':'scam warnings, unusual-recipient risk, device/account risk and payment education','regulated_execution':False},
    {'slug':'global_money_intelligence','name':'Global Money Intelligence','role':'currency, FX, travel budgets and cross-border cost education','regulated_execution':False},
    {'slug':'credit_intelligence','name':'Credit Intelligence','role':'APR, affordability, borrowing cost and debt-risk education','regulated_execution':False},
    {'slug':'business_intelligence','name':'Business Banking Intelligence','role':'invoices, expenses, cash flow, tax pots, bookkeeping and payroll awareness','regulated_execution':False},
    {'slug':'rewards_intelligence','name':'Rewards Intelligence','role':'cashback and benefit comparison concepts without guaranteed reward claims','regulated_execution':False},
    {'slug':'open_banking_intelligence','name':'Open Banking Intelligence','role':'future consent-based connected-account aggregation and explanation','regulated_execution':True},
    {'slug':'human_support','name':'Human Support','role':'clear escalation to a human for sensitive, disputed or high-risk financial situations','regulated_execution':False},
    {'slug':'financial_education','name':'Financial Education','role':'explain consequences before financial action','regulated_execution':False},
    {'slug':'sika_bridge','name':'SIKA Bridge','role':'explain separation between SIKA created value and regulated fiat banking','regulated_execution':True},
]

YOUTH_RULES = {
    'targeted_credit_marketing': False,
    'autonomous_borrowing': False,
    'autonomous_card_issuance': False,
    'public_balance_visibility': False,
    'guardian_controls_where_required': True,
    'age_appropriate_financial_education': True,
}


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
            education_before_action=True,
            adaptive=True,
            coherent=True,
        )

    @bank_intelligence.get('/api/bank-intelligence')
    def overview():
        authorised=_enabled('OAP_BANKING_AUTHORISED')
        return jsonify(
            name='Bank Intelligence',
            parent='ON ANY POSTCODE Intelligence',
            institutional_context='Prince Sovereign Bank',
            domains=DOMAINS,
            account_modes=ACCOUNT_MODES,
            purpose='financial_literacy_risk_compliance_and_future_bank_readiness',
            product_direction='modern_digital_bank_intelligence',
            education_before_action=True,
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

    @bank_intelligence.get('/api/bank-intelligence/features')
    def features():
        authorised=_enabled('OAP_BANKING_AUTHORISED')
        items=[]
        for feature in FEATURES:
            item=dict(feature)
            item['execution_enabled']=bool(authorised and feature['regulated_execution'])
            item['mode']='regulated_future' if feature['regulated_execution'] else 'intelligence_now'
            items.append(item)
        return jsonify(
            features=items,
            design_principles=['simple_mobile_first','global_capable','strong_controls','human_support','education_before_action','privacy_first','no_fake_bank_claims'],
            independent_oap_design=True,
            banking_service_authorised=authorised,
            authority='human_final',
        )

    @bank_intelligence.get('/api/bank-intelligence/family')
    def family():
        return jsonify(
            account_modes=['family','youth','young_adult','elder_safe'],
            rules=YOUTH_RULES,
            principle='progressive_independence_with_age_appropriate_protection',
            precise_location_required=False,
            authority='human_final',
        )

    @bank_intelligence.post('/api/bank-intelligence/check')
    def check():
        d=request.get_json(silent=True) or {}
        action=str(d.get('action','')).strip().lower()[:80]
        regulated={'open_account','accept_deposit','transfer_money','issue_card','lend','exchange_currency','hold_client_funds','connect_open_banking_account'}
        if action in regulated and not _enabled('OAP_BANKING_AUTHORISED'):
            return jsonify(ok=False,action=action,status='blocked_pending_authorisation',execution=False,authority='human_final'),403
        if not action:
            return jsonify(error='action_required'),400
        return jsonify(ok=True,action=action,status='advisory_only',execution=False,authority='human_final')

    @bank_intelligence.post('/api/bank-intelligence/plan')
    def plan():
        d=request.get_json(silent=True) or {}
        monthly_income=d.get('monthly_income')
        if not isinstance(monthly_income,(int,float)) or monthly_income < 0:
            return jsonify(error='valid_monthly_income_required'),400
        goals=d.get('goals') if isinstance(d.get('goals'),list) else []
        return jsonify(
            mode='simulation_only',
            monthly_income=monthly_income,
            goals=goals[:20],
            suggested_buckets=['bills','food','transport','emergency','savings','goals','spending'],
            execution=False,
            disclaimer='Planning guidance only. No money is moved or held.',
            authority='human_final',
        )

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
