"""Signal Routes - News & Information System"""
from flask import Blueprint, request, jsonify
from config.database import db

signal_bp = Blueprint('signal', __name__)

@signal_bp.route('/posts', methods=['GET'])
def get_posts():
    from app.models.signal_post import SignalPost
    spot_id = request.args.get('spot_id')
    query = SignalPost.query
    if spot_id:
        query = query.filter_by(spot_id=spot_id)
    posts = query.order_by(SignalPost.created_at.desc()).limit(20).all()
    return jsonify({'success': True, 'count': len(posts), 'data': [{'id': p.id, 'title': p.title} for p in posts]})

@signal_bp.route('/posts', methods=['POST'])
def create_post():
    from app.models.signal_post import SignalPost
    data = request.get_json()
    if not all(k in data for k in ['spot_id', 'post_type', 'title', 'content']):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    post = SignalPost(**{k:v for k,v in data.items() if k in ['spot_id','post_type','title','content','author_id']})
    db.session.add(post)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Post created', 'data': {'id': post.id}}), 201
