"""Movement Routes - Real-world Action System"""
from flask import Blueprint, request, jsonify
from config.database import db
from app.models.movement_activity import MovementActivity

movement_bp = Blueprint('movement', __name__)

@movement_bp.route('/activities', methods=['GET'])
def get_activities():
    spot_id = request.args.get('spot_id')
    status = request.args.get('status', 'active')
    query = MovementActivity.query
    if spot_id:
        query = query.filter_by(spot_id=spot_id)
    if status:
        query = query.filter_by(status=status)
    activities = query.all()
    return jsonify({'success': True, 'count': len(activities), 'data': [a.to_dict() for a in activities]})

@movement_bp.route('/activities', methods=['POST'])
def create_activity():
    data = request.get_json()
    required = ['spot_id', 'activity_type', 'title', 'start_time']
    if not all(k in data for k in required):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    activity = MovementActivity(**data)
    db.session.add(activity)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Activity created', 'data': activity.to_dict()}), 201
