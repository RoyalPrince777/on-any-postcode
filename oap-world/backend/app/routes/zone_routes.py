"""Zone Routes - City Layer Collection of Areas"""
from flask import Blueprint, request, jsonify
from config.database import db
from app.models.zone import Zone

zone_bp = Blueprint('zones', __name__)

@zone_bp.route('/', methods=['GET'])
def get_zones():
    zones = Zone.query.all()
    return jsonify({'success': True, 'count': len(zones), 'data': [z.to_dict() for z in zones]})

@zone_bp.route('/<int:zone_id>', methods=['GET'])
def get_zone(zone_id):
    zone = Zone.query.get_or_404(zone_id)
    return jsonify({'success': True, 'data': zone.to_dict()})

@zone_bp.route('/', methods=['POST'])
def create_zone():
    data = request.get_json()
    if 'name' not in data:
        return jsonify({'success': False, 'error': 'Missing required field: name'}), 400
    zone = Zone(**{k: v for k, v in data.items() if k in ['name', 'city_level', 'region_level', 'country_code']})
    db.session.add(zone)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Zone created', 'data': zone.to_dict()}), 201
