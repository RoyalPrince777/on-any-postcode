"""Guardian Routes - Safety System"""
from flask import Blueprint, request, jsonify
from config.database import db

guardian_bp = Blueprint('guardian', __name__)

@guardian_bp.route('/reports', methods=['POST'])
def create_report():
    from app.models.guardian_report import GuardianReport
    data = request.get_json()
    required = ['reporter_id', 'reported_user_id', 'report_reason']
    if not all(k in data for k in required):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    report = GuardianReport(**{k:v for k,v in data.items() if k in ['reporter_id','reported_user_id','report_reason','severity_level']})
    db.session.add(report)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Report created', 'data': {'id': report.id}}), 201

@guardian_bp.route('/risk/check', methods=['POST'])
def check_risk():
    from app.models.guardian_risk_log import GuardianRiskLog
    data = request.get_json()
    risk_score = data.get('risk_score', 0.5)
    action = 'flagged' if risk_score > 0.8 else 'approved'
    log = GuardianRiskLog(
        user_id=data.get('user_id'),
        spot_id=data.get('spot_id'),
        risk_type=data.get('risk_type', 'general'),
        risk_score=risk_score,
        action_taken=action
    )
    db.session.add(log)
    db.session.commit()
    return jsonify({'success': True, 'action': action, 'risk_score': risk_score})
