from flask import Blueprint, jsonify
import os

providers = Blueprint('oap_provider_contracts', __name__)

CONTRACTS = {
    'geography': {'env':'OAP_GEO_PROVIDER','purpose':'postcode borough county region country continent resolution'},
    'routing': {'env':'OAP_ROUTING_PROVIDER','purpose':'OSM OSRM compatible route and ETA data'},
    'weather': {'env':'OAP_WEATHER_PROVIDER','purpose':'weather and environmental signals'},
    'transport': {'env':'OAP_TRANSPORT_PROVIDER','purpose':'real-time public transport and disruption data'},
    'education': {'env':'OAP_EDUCATION_PROVIDER','purpose':'verified education training apprenticeship provider data'},
    'observability': {'env':'OAP_OBSERVABILITY_PROVIDER','purpose':'metrics logs traces and alerting'},
}


def register_provider_contracts(app):
    @providers.get('/api/providers')
    def provider_overview():
        rows=[]
        for name,meta in CONTRACTS.items():
            raw=os.environ.get(meta['env'],'').strip()
            rows.append({
                'name':name,
                'purpose':meta['purpose'],
                'configured':bool(raw),
                'status':'configured_unverified' if raw else 'not_connected',
                'live_claim':False,
                'required_env':meta['env'],
            })
        return jsonify(ok=True,providers=rows,no_fake_live=True,authority='human_final')

    @providers.get('/api/providers/<name>/health')
    def provider_health(name):
        meta=CONTRACTS.get(name)
        if not meta:return jsonify(error='provider_not_found'),404
        raw=os.environ.get(meta['env'],'').strip()
        return jsonify(
            ok=bool(raw),
            name=name,
            configured=bool(raw),
            status='configured_unverified' if raw else 'not_connected',
            live_claim=False,
            probe_required=True,
            requirement=meta['purpose'],
            authority='human_final'
        ), (200 if raw else 503)

    app.register_blueprint(providers)
