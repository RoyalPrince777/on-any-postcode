"""Area Routes - Mid Layer Collection of Spots"""
from flask import Blueprint, request, jsonify
from config.database import db
from app.models.spot import Spot
from app.models.area import Area

area_bp = Blueprint('areas', __name__)

@area_bp.route('/', methods=['GET'])
def get_areas():
    zone_id = request.args.get('zone_id')
    query = Area.query
    if zone_id:
        query = query.filter_by(zone_id=zone_id)
    areas = query.all()
    return jsonify({'success': True, 'count': len(areas), 'data': [a.to_dict() for a in areas]})

@area_bp.route('/<int:area_id>', methods=['GET'])
def get_area(area_id):
    area = Area.query.get_or_404(area_id)
    return jsonify({'success': True, 'data': area.to_dict()})

@area_bp.route('/', methods=['POST'])
def create_area():
    data = request.get_json()
    if not all(k in data for k in ['name']):
        return jsonify({'success': False, 'error': 'Missing required field: name'}), 400
    area = Area(**{k: v for k, v in data.items() if k in ['name', 'borough_level', 'district_level', 'zone_id']})
    db.session.add(area)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Area created', 'data': area.to_dict()}), 201
