"""Wellbeing Routes - Mental & Physical Health Layer"""
from flask import Blueprint, request, jsonify
from config.database import db
from datetime import date

wellbeing_bp = Blueprint('wellbeing', __name__)

@wellbeing_bp.route('/user/<int:user_id>', methods=['GET'])
def get_wellbeing(user_id):
    from app.models.user_wellbeing import UserWellbeing
    today = date.today()
    wellbeing = UserWellbeing.query.filter_by(user_id=user_id, recorded_date=today).first()
    if not wellbeing:
        wellbeing = UserWellbeing(user_id=user_id, recorded_date=today)
        db.session.add(wellbeing)
        db.session.commit()
    return jsonify({'success': True, 'data': {'mental_health': wellbeing.mental_health_score, 'exercise': wellbeing.exercise_minutes_today, 'sleep': wellbeing.sleep_hours_last_night}})

@wellbeing_bp.route('/user', methods=['POST'])
def update_wellbeing():
    from app.models.user_wellbeing import UserWellbeing
    data = request.get_json()
    if 'user_id' not in data:
        return jsonify({'success': False, 'error': 'Missing user_id'}), 400
    today = date.today()
    wellbeing = UserWellbeing.query.filter_by(user_id=data['user_id'], recorded_date=today).first()
    if not wellbeing:
        wellbeing = UserWellbeing(user_id=data['user_id'], recorded_date=today)
        db.session.add(wellbeing)
    for k, v in data.items():
        if k != 'user_id' and hasattr(wellbeing, k):
            setattr(wellbeing, k, v)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Wellbeing updated'})
