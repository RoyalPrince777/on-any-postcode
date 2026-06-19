"""Pulse Routes - Live Activity Stream"""
from flask import Blueprint, request, jsonify
from config.database import db
from app.models.pulse_event import PulseEvent

pulse_bp = Blueprint('pulse', __name__)

@pulse_bp.route('/spot/<int:spot_id>', methods=['GET'])
def get_spot_pulse(spot_id):
    limit = request.args.get('limit', 20, type=int)
    events = PulseEvent.query.filter_by(spot_id=spot_id).order_by(PulseEvent.created_at.desc()).limit(limit).all()
    return jsonify({'success': True, 'count': len(events), 'data': [e.to_dict() for e in events]})

@pulse_bp.route('/', methods=['POST'])
def create_event():
    data = request.get_json()
    required = ['spot_id', 'event_type']
    if not all(k in data for k in required):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    event = PulseEvent(
        spot_id=data['spot_id'],
        user_id=data.get('user_id'),
        event_type=data['event_type'],
        event_data=data.get('event_data'),
        energy_level=data.get('energy_level', 50),
        visibility=data.get('visibility', 'public')
    )
    db.session.add(event)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Event created', 'data': event.to_dict()}), 201
