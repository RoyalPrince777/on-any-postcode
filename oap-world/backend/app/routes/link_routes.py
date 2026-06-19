"""Link Routes - Communication System"""
from flask import Blueprint, request, jsonify
from config.database import db

link_bp = Blueprint('link', __name__)

@link_bp.route('/messages/<int:user_id>', methods=['GET'])
def get_messages(user_id):
    from app.models.link_message import LinkMessage
    messages = LinkMessage.query.filter_by(recipient_id=user_id).order_by(LinkMessage.created_at.desc()).limit(50).all()
    return jsonify({'success': True, 'count': len(messages), 'data': [{'id': m.id, 'sender_id': m.sender_id, 'content': m.content} for m in messages]})

@link_bp.route('/messages', methods=['POST'])
def send_message():
    from app.models.link_message import LinkMessage
    data = request.get_json()
    if not all(k in data for k in ['sender_id', 'recipient_id', 'content']):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    msg = LinkMessage(**{k:v for k,v in data.items() if k in ['sender_id','recipient_id','content','message_type']})
    db.session.add(msg)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Message sent', 'data': {'id': msg.id}}), 201
