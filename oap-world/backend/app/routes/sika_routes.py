"""SIKA Routes - Value System & Economy"""
from flask import Blueprint, request, jsonify
from config.database import db
from app.models.user import User
from app.models.sika_account import SikaAccount
from app.models.spot_sika_pool import SpotSikaPool

sika_bp = Blueprint('sika', __name__)

@sika_bp.route('/account/<int:user_id>/spot/<int:spot_id>', methods=['GET'])
def get_account(user_id, spot_id):
    account = SikaAccount.query.filter_by(user_id=user_id, spot_id=spot_id).first()
    if not account:
        account = SikaAccount(user_id=user_id, spot_id=spot_id)
        db.session.add(account)
        db.session.commit()
    return jsonify({'success': True, 'data': account.to_dict()})

@sika_bp.route('/reward', methods=['POST'])
def issue_reward():
    data = request.get_json()
    required = ['user_id', 'spot_id', 'amount', 'transaction_type']
    if not all(k in data for k in required):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    user = User.query.get_or_404(data['user_id'])
    account = SikaAccount.query.filter_by(user_id=user.id, spot_id=data['spot_id']).first()
    if not account:
        account = SikaAccount(user_id=user.id, spot_id=data['spot_id'])
        db.session.add(account)
    account.balance += data['amount']
    account.earned_total += data['amount']
    db.session.commit()
    return jsonify({'success': True, 'message': 'Reward issued', 'new_balance': float(account.balance)})

@sika_bp.route('/pool/<int:spot_id>', methods=['GET'])
def get_pool(spot_id):
    pool = SpotSikaPool.query.filter_by(spot_id=spot_id).first()
    if not pool:
        pool = SpotSikaPool(spot_id=spot_id)
        db.session.add(pool)
        db.session.commit()
    return jsonify({'success': True, 'data': pool.to_dict()})
