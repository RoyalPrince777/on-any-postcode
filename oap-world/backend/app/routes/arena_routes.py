"""Arena Routes - Competition System"""
from flask import Blueprint, request, jsonify
from config.database import db

arena_bp = Blueprint('arena', __name__)

@arena_bp.route('/games', methods=['GET'])
def get_games():
    from app.models.arena_game import ArenaGame
    spot_id = request.args.get('spot_id')
    query = ArenaGame.query
    if spot_id:
        query = query.filter_by(spot_id=spot_id)
    games = query.all()
    return jsonify({'success': True, 'count': len(games), 'data': [{'id': g.id, 'game_name': g.game_name, 'status': g.status} for g in games]})

@arena_bp.route('/games', methods=['POST'])
def create_game():
    from app.models.arena_game import ArenaGame
    data = request.get_json()
    if not all(k in data for k in ['spot_id', 'game_name', 'game_type']):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    game = ArenaGame(**{k:v for k,v in data.items() if k in ['spot_id','game_name','game_type','game_type']})
    db.session.add(game)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Game created', 'data': {'id': game.id}}), 201
