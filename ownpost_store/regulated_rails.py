from flask import Blueprint, jsonify, request
import os

regulated = Blueprint('oap_regulated_rails', __name__)

RAILS = {
    'ride_commercial': {'env':'OAP_RIDE_COMMERCIAL_AUTHORISED','requirements':['transport_licensing','driver_checks','insurance','payment_provider','local_law_compliance']},
    'sika_payments': {'env':'OAP_SIKA_REGULATED_ENABLED','requirements':['legal_authorisation','regulated_payment_provider','kyc_aml_where_required','audit']},
    'banking': {'env':'OAP_BANKING_AUTHORISED','requirements':['banking_or_partner_authorisation','regulated_provider','consumer_protection','audit']},
    'open_banking': {'env':'OAP_OPEN_BANKING_AUTHORISED','requirements':['open_banking_authorisation_or_regulated_partner','consent','secure_tokens','audit']},
}


def _on(name):
    return os.environ.get(name,'').strip().lower() in {'1','true','yes','enabled','authorised','authorized'}


def register_regulated_rails(app):
    @regulated.get('/api/regulated')
    def overview():
        rows=[]
        for name,meta in RAILS.items():
            enabled=_on(meta['env'])
            rows.append({'name':name,'enabled':enabled,'status':'authorised_enabled' if enabled else 'blocked_pending_authorisation','requirements':meta['requirements'],'required_env':meta['env']})
        return jsonify(ok=True,rails=rows,default='fail_closed',human_final=True,no_fake_green=True)

    @regulated.post('/api/regulated/<name>/execute')
    def execute(name):
        meta=RAILS.get(name)
        if not meta:return jsonify(error='rail_not_found'),404
        if not _on(meta['env']):
            return jsonify(error='regulated_execution_blocked',rail=name,execution=False,requirements=meta['requirements'],authority='human_final'),403
        # Authorisation flag alone is not a payment/bank provider. This endpoint is only a guard contract.
        d=request.get_json(silent=True) or {}
        return jsonify(ok=True,rail=name,guard_passed=True,provider_execution=False,provider_required=True,requested_action=str(d.get('action',''))[:80],authority='human_final'),202

    app.register_blueprint(regulated)
