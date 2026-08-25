from flask import Blueprint, jsonify
import os

movement_hub = Blueprint('oap_movement_hub', __name__)

MODES = ['road','rail','air','sea','public_transport','ride','taxi_private_hire','delivery','freight','cross_border','walking','cycling','accessible']
HIERARCHY = ['postcode','borough','county_region','country','continent','global']


def _configured(name):
    return bool(os.environ.get(name,'').strip())


def register_movement_hub(app, db, uid):
    @movement_hub.get('/api/movement/health')
    def health():
        return jsonify(ok=True,service='oap-movement',ride_mounted='oap_ride' in app.blueprints,authority='human_final')

    @movement_hub.get('/api/movement')
    def overview():
        return jsonify(
            name='OAP Movement',
            parent='OAP World',
            hierarchy=HIERARCHY,
            modes=MODES,
            organs=['oap_ride','maps_routing','oap_captain','transport_realtime','delivery','freight'],
            connections=['the_spot','oap_intelligence','sika','market','link_up','guardian','hrm','258'],
            routing_provider={'configured':_configured('OAP_ROUTING_PROVIDER'),'live_claim':False},
            realtime_transport_provider={'configured':_configured('OAP_TRANSPORT_PROVIDER'),'live_claim':False},
            local_first=True,
            autonomous_real_world_execution=False,
            authority='human_final'
        )

    @movement_hub.get('/api/movement/safety')
    def safety():
        return jsonify(
            route_evidence_required=True,
            certified_commercial_drivers_required=True,
            insurance_required_for_commercial_ride=True,
            licensing_required_for_commercial_ride=True,
            youth_safe_mode=True,
            accessibility_mode=True,
            precise_location_public=False,
            trip_data_for_ads=False,
            human_final=True
        )

    app.register_blueprint(movement_hub)
