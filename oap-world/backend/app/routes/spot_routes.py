"""
Spot Routes - Base Unit of OAP World
📍 Spot: Street level, Postcode cluster, Local community space
"""

from flask import Blueprint, request, jsonify
from config.database import db
from app.models.spot import Spot
from app.models.area import Area

spot_bp = Blueprint('spots', __name__)


@spot_bp.route('/', methods=['GET'])
def get_spots():
    """Get all spots with optional filtering"""
    area_id = request.args.get('area_id')
    status = request.args.get('status', 'active')
    
    query = Spot.query
    
    if area_id:
        query = query.filter_by(area_id=area_id)
    
    if status:
        query = query.filter_by(status=status)
    
    spots = query.all()
    return jsonify({
        'success': True,
        'count': len(spots),
        'data': [spot.to_dict() for spot in spots]
    })


@spot_bp.route('/<int:spot_id>', methods=['GET'])
def get_spot(spot_id):
    """Get a specific spot by ID"""
    spot = Spot.query.get_or_404(spot_id)
    return jsonify({
        'success': True,
        'data': spot.to_dict(include_details=True)
    })


@spot_bp.route('/', methods=['POST'])
def create_spot():
    """Create a new spot"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['name', 'postcode_prefix']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'success': False,
                'error': f'Missing required field: {field}'
            }), 400
    
    # Check if area exists if provided
    if data.get('area_id'):
        area = Area.query.get(data['area_id'])
        if not area:
            return jsonify({
                'success': False,
                'error': 'Area not found'
            }), 404
    
    try:
        spot = Spot(
            name=data['name'],
            postcode_prefix=data['postcode_prefix'],
            street_level_address=data.get('street_level_address'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            area_id=data.get('area_id'),
            status=data.get('status', 'active')
        )
        
        db.session.add(spot)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Spot created successfully',
            'data': spot.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@spot_bp.route('/<int:spot_id>', methods=['PUT'])
def update_spot(spot_id):
    """Update an existing spot"""
    spot = Spot.query.get_or_404(spot_id)
    data = request.get_json()
    
    try:
        # Update allowed fields
        allowed_fields = [
            'name', 'postcode_prefix', 'street_level_address',
            'latitude', 'longitude', 'area_id', 'status'
        ]
        
        for field in allowed_fields:
            if field in data:
                setattr(spot, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Spot updated successfully',
            'data': spot.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@spot_bp.route('/<int:spot_id>', methods=['DELETE'])
def delete_spot(spot_id):
    """Delete a spot (soft delete by setting status to archived)"""
    spot = Spot.query.get_or_404(spot_id)
    
    try:
        # Soft delete
        spot.status = 'archived'
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Spot archived successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@spot_bp.route('/<int:spot_id>/activity', methods=['GET'])
def get_spot_activity(spot_id):
    """Get activity summary for a spot"""
    from app.models.user_spot_activity import UserSpotActivity
    from app.models.pulse_event import PulseEvent
    from app.models.movement_activity import MovementActivity
    
    spot = Spot.query.get_or_404(spot_id)
    
    # Get recent pulse events
    recent_events = PulseEvent.query.filter_by(spot_id=spot_id)\
        .order_by(PulseEvent.created_at.desc())\
        .limit(10).all()
    
    # Get active movements
    active_movements = MovementActivity.query.filter_by(
        spot_id=spot_id, 
        status='active'
    ).all()
    
    # Get user count
    active_users = UserSpotActivity.query.filter_by(spot_id=spot_id)\
        .filter(UserSpotActivity.visit_count > 0)\
        .count()
    
    return jsonify({
        'success': True,
        'data': {
            'spot': spot.to_dict(),
            'active_users': active_users,
            'recent_events': [e.to_dict() for e in recent_events],
            'active_movements': [m.to_dict() for m in active_movements]
        }
    })


@spot_bp.route('/<int:spot_id>/sika-pool', methods=['GET'])
def get_spot_sika_pool(spot_id):
    """Get SIKA pool information for a spot"""
    from app.models.spot_sika_pool import SpotSikaPool
    
    spot = Spot.query.get_or_404(spot_id)
    pool = SpotSikaPool.query.filter_by(spot_id=spot_id).first()
    
    if not pool:
        # Create default pool if it doesn't exist
        pool = SpotSikaPool(spot_id=spot_id)
        db.session.add(pool)
        db.session.commit()
    
    return jsonify({
        'success': True,
        'data': pool.to_dict()
    })
