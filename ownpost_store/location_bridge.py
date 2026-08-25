from flask import Blueprint, jsonify, request

location_bridge = Blueprint('oap_location_bridge', __name__)

HIERARCHY = ['postcode','borough','county_region','country','continent','global','universe']


def register_location_bridge(app):
    @location_bridge.get('/api/location-bridge/health')
    def health():
        with app.test_client() as c:
            adapters=c.get('/api/adapters/health')
            movement=c.get('/api/movement/health')
            ride=c.get('/api/ride/health')
        return jsonify(
            ok=adapters.status_code==200 and movement.status_code==200 and ride.status_code==200,
            service='location-bridge',
            connects=['The Spot','Movement','OAP Ride','OAP Captain','provider-adapters'],
            hierarchy=HIERARCHY,
            provider_state=adapters.get_json(silent=True),
            movement_ok=movement.status_code==200,
            ride_ok=ride.status_code==200,
            local_first=True,
            no_fake_live=True,
            authority='human_final'
        )

    @location_bridge.get('/api/location-bridge/context')
    def context():
        postcode=str(request.args.get('postcode','')).strip().upper()[:20]
        if not postcode:return jsonify(error='postcode_required'),400
        with app.test_client() as c:
            geo=c.get('/api/adapters/geography?postcode='+postcode)
            movement=c.get('/api/movement')
            ride=c.get('/api/ride')
        return jsonify(
            ok=geo.status_code==200,
            postcode=postcode,
            hierarchy=HIERARCHY,
            geography=geo.get_json(silent=True),
            movement=movement.get_json(silent=True),
            ride=ride.get_json(silent=True),
            source='shared_oap_location_contract',
            local_first=True,
            public_precise_location=False,
            authority='human_final'
        )

    @location_bridge.post('/api/location-bridge/route')
    def route():
        d=request.get_json(silent=True) or {}
        origin=str(d.get('origin','')).strip()[:200]
        destination=str(d.get('destination','')).strip()[:200]
        if not origin or not destination:return jsonify(error='origin_destination_required'),400
        with app.test_client() as c:
            r=c.post('/api/adapters/route',json={'origin':origin,'destination':destination})
        data=r.get_json(silent=True) or {}
        return jsonify(
            ok=r.status_code==200,
            origin=origin,
            destination=destination,
            route_contract=data,
            consumers=['Movement','OAP Ride','The Spot','OAP Captain'],
            planning_only=bool(data.get('planning_only',True)),
            provider_connected=bool(data.get('provider_connected',False)),
            execution=False,
            authority='human_final'
        ), r.status_code

    app.register_blueprint(location_bridge)
