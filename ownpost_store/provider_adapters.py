from flask import Blueprint, jsonify, request
import os

provider_adapters = Blueprint('oap_provider_adapters', __name__)


def _configured(env_name):
    return bool(os.environ.get(env_name,'').strip())


def register_provider_adapters(app):
    @provider_adapters.get('/api/adapters/health')
    def health():
        return jsonify(
            ok=True,
            service='provider-adapters',
            adapters={
                'geography':{'configured':_configured('OAP_GEO_PROVIDER'),'mode':'provider' if _configured('OAP_GEO_PROVIDER') else 'local_structure_only'},
                'routing':{'configured':_configured('OAP_ROUTING_PROVIDER'),'mode':'provider' if _configured('OAP_ROUTING_PROVIDER') else 'planning_only'},
                'weather':{'configured':_configured('OAP_WEATHER_PROVIDER'),'mode':'provider' if _configured('OAP_WEATHER_PROVIDER') else 'unavailable'},
                'transport':{'configured':_configured('OAP_TRANSPORT_PROVIDER'),'mode':'provider' if _configured('OAP_TRANSPORT_PROVIDER') else 'unavailable'},
            },
            no_fake_live=True,
            authority='human_final'
        )

    @provider_adapters.get('/api/adapters/geography')
    def geography():
        postcode=str(request.args.get('postcode','')).strip().upper()[:20]
        if not postcode:return jsonify(error='postcode_required'),400
        if not _configured('OAP_GEO_PROVIDER'):
            return jsonify(
                ok=True,postcode=postcode,source='local_structure_only',live_provider=False,
                hierarchy=['postcode','borough','county_region','country','continent','global','universe'],
                resolved=False,reason='geography_provider_not_connected'
            )
        return jsonify(ok=True,postcode=postcode,source=os.environ.get('OAP_GEO_PROVIDER'),live_provider=False,resolved=False,reason='provider_adapter_configured_but_external_call_not_enabled')

    @provider_adapters.post('/api/adapters/route')
    def route():
        d=request.get_json(silent=True) or {}
        origin=str(d.get('origin','')).strip()[:200]; destination=str(d.get('destination','')).strip()[:200]
        if not origin or not destination:return jsonify(error='origin_destination_required'),400
        if not _configured('OAP_ROUTING_PROVIDER'):
            return jsonify(ok=True,planning_only=True,provider_connected=False,route=None,reason='routing_provider_not_connected',captain='OAP Captain')
        return jsonify(ok=True,planning_only=True,provider_connected=True,route=None,reason='provider_adapter_configured_external_execution_not_enabled',captain='OAP Captain')

    @provider_adapters.get('/api/adapters/weather')
    def weather():
        place=str(request.args.get('place','')).strip()[:200]
        if not place:return jsonify(error='place_required'),400
        if not _configured('OAP_WEATHER_PROVIDER'):
            return jsonify(ok=True,place=place,available=False,provider_connected=False,reason='weather_provider_not_connected')
        return jsonify(ok=True,place=place,available=False,provider_connected=True,reason='provider_adapter_configured_external_execution_not_enabled')

    @provider_adapters.get('/api/adapters/transport')
    def transport():
        place=str(request.args.get('place','')).strip()[:200]
        if not place:return jsonify(error='place_required'),400
        if not _configured('OAP_TRANSPORT_PROVIDER'):
            return jsonify(ok=True,place=place,realtime=False,provider_connected=False,reason='transport_provider_not_connected')
        return jsonify(ok=True,place=place,realtime=False,provider_connected=True,reason='provider_adapter_configured_external_execution_not_enabled')

    app.register_blueprint(provider_adapters)
