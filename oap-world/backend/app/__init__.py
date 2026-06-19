"""
OAP World Backend - Flask Application
One World. One Front Door. Many Systems Inside.
"""

from flask import Flask, jsonify
from flask_cors import CORS
from config.database import db, migrate
from config.config import Config

# Import Blueprints
from app.routes.spot_routes import spot_bp
from app.routes.area_routes import area_bp
from app.routes.zone_routes import zone_bp
from app.routes.user_routes import user_bp
from app.routes.sika_routes import sika_bp
from app.routes.hrm_routes import hrm_bp
from app.routes.pulse_routes import pulse_bp
from app.routes.signal_routes import signal_bp
from app.routes.link_routes import link_bp
from app.routes.arena_routes import arena_bp
from app.routes.movement_routes import movement_bp
from app.routes.guardian_routes import guardian_bp
from app.routes.nature_routes import nature_bp
from app.routes.wellbeing_routes import wellbeing_bp


def create_app(config_class=Config):
    """Application factory for OAP World backend"""
    
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)
    
    # Register Blueprints - Core Systems
    app.register_blueprint(spot_bp, url_prefix='/api/v1/spots')
    app.register_blueprint(area_bp, url_prefix='/api/v1/areas')
    app.register_blueprint(zone_bp, url_prefix='/api/v1/zones')
    app.register_blueprint(user_bp, url_prefix='/api/v1/users')
    
    # Economic System
    app.register_blueprint(sika_bp, url_prefix='/api/v1/sika')
    
    # Intelligence System
    app.register_blueprint(hrm_bp, url_prefix='/api/v1/hrm')
    
    # Communication & Activity Systems
    app.register_blueprint(pulse_bp, url_prefix='/api/v1/pulse')
    app.register_blueprint(signal_bp, url_prefix='/api/v1/signal')
    app.register_blueprint(link_bp, url_prefix='/api/v1/link')
    
    # Action & Competition Systems
    app.register_blueprint(arena_bp, url_prefix='/api/v1/arena')
    app.register_blueprint(movement_bp, url_prefix='/api/v1/movement')
    
    # Safety & Wellbeing Systems
    app.register_blueprint(guardian_bp, url_prefix='/api/v1/guardian')
    app.register_blueprint(nature_bp, url_prefix='/api/v1/nature')
    app.register_blueprint(wellbeing_bp, url_prefix='/api/v1/wellbeing')
    
    # Health Check Endpoint
    @app.route('/api/v1/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'system': 'OAP World',
            'version': '1.0.0',
            'principle': 'One World. One Front Door. Many Systems Inside.'
        })
    
    # Root Endpoint - The Front Door
    @app.route('/')
    def front_door():
        return jsonify({
            'message': 'Welcome to OAP World',
            'tagline': 'One World. One Front Door. Many Systems Inside.',
            'structure': {
                'hierarchy': 'Spot → Area → Zone → World',
                'core_systems': [
                    'Pulse (Feed)',
                    'Signal (News)',
                    'Link (Communication)',
                    'Arena (Competition)',
                    'Movement (Action)',
                    'SIKA (Value)',
                    'HRM (Intelligence)',
                    'Guardian (Safety)'
                ],
                'human_state': ['Energy', 'Mood', 'Stealth'],
                'wellbeing': ['Nature', 'Mental Health', 'Exercise', 'Nutrition', 'Sleep', 'Mindfulness']
            },
            'endpoints': {
                'spots': '/api/v1/spots',
                'areas': '/api/v1/areas',
                'zones': '/api/v1/zones',
                'users': '/api/v1/users',
                'sika': '/api/v1/sika',
                'hrm': '/api/v1/hrm',
                'pulse': '/api/v1/pulse',
                'signal': '/api/v1/signal',
                'link': '/api/v1/link',
                'arena': '/api/v1/arena',
                'movement': '/api/v1/movement',
                'guardian': '/api/v1/guardian',
                'nature': '/api/v1/nature',
                'wellbeing': '/api/v1/wellbeing',
                'health': '/api/v1/health'
            }
        })
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
