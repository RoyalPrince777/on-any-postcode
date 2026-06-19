"""User Routes - Identity & Human State Layer"""
from flask import Blueprint, request, jsonify
from config.database import db
from app.models.user import User

user_bp = Blueprint('users', __name__)

@user_bp.route('/', methods=['GET'])
def get_users():
    users = User.query.filter_by(is_active=True).all()
    return jsonify({'success': True, 'count': len(users), 'data': [u.to_dict() for u in users]})

@user_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({'success': True, 'data': user.to_dict()})

@user_bp.route('/', methods=['POST'])
def create_user():
    data = request.get_json()
    required = ['username', 'email', 'password_hash']
    if not all(k in data for k in required):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    user = User(
        username=data['username'],
        email=data['email'],
        password_hash=data['password_hash'],
        home_spot_id=data.get('home_spot_id'),
        energy_level=data.get('energy_level', 'medium'),
        mood_state=data.get('mood_state', 'calm')
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({'success': True, 'message': 'User created', 'data': user.to_dict()}), 201

@user_bp.route('/<int:user_id>/state', methods=['PUT'])
def update_user_state(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    for field in ['energy_level', 'mood_state', 'stealth_mode']:
        if field in data:
            setattr(user, field, data[field])
    db.session.commit()
    return jsonify({'success': True, 'data': user.to_dict()})
