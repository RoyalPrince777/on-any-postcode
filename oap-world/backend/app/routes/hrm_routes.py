"""HRM Routes - Intelligence & Memory System"""
from flask import Blueprint, request, jsonify
from config.database import db
from app.models.hrm_memory import HRMMemory
from app.models.user import User

hrm_bp = Blueprint('hrm', __name__)

@hrm_bp.route('/memory/<int:user_id>', methods=['GET'])
def get_memory(user_id):
    memories = HRMMemory.query.filter_by(user_id=user_id).all()
    return jsonify({'success': True, 'count': len(memories), 'data': [m.to_dict() for m in memories]})

@hrm_bp.route('/memory', methods=['POST'])
def store_memory():
    data = request.get_json()
    required = ['user_id', 'memory_type', 'memory_key', 'memory_value']
    if not all(k in data for k in required):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    memory = HRMMemory(
        user_id=data['user_id'],
        memory_type=data['memory_type'],
        memory_key=data['memory_key'],
        memory_value=data['memory_value'],
        confidence_score=data.get('confidence_score')
    )
    db.session.add(memory)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Memory stored', 'data': memory.to_dict()}), 201
