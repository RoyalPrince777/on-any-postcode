"""Nature Routes - Nature & Environmental Layer"""
from flask import Blueprint, request, jsonify
from config.database import db

nature_bp = Blueprint('nature', __name__)

@nature_bp.route('/data/<int:spot_id>', methods=['GET'])
def get_nature_data(spot_id):
    from app.models.nature_data import NatureData
    data = NatureData.query.filter_by(spot_id=spot_id).first()
    if not data:
        data = NatureData(spot_id=spot_id)
        db.session.add(data)
        db.session.commit()
    return jsonify({'success': True, 'data': {'spot_id': data.spot_id, 'weather': data.weather_condition, 'air_quality': data.air_quality_index}})

@nature_bp.route('/data', methods=['POST'])
def update_nature_data():
    from app.models.nature_data import NatureData
    data = request.get_json()
    if 'spot_id' not in data:
        return jsonify({'success': False, 'error': 'Missing spot_id'}), 400
    nature = NatureData.query.filter_by(spot_id=data['spot_id']).first()
    if not nature:
        nature = NatureData(spot_id=data['spot_id'])
        db.session.add(nature)
    for k, v in data.items():
        if k != 'spot_id' and hasattr(nature, k):
            setattr(nature, k, v)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Nature data updated'})
