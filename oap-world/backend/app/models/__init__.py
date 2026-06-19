"""
Database Models for OAP World
Starting from The Spot and expanding to the full hierarchy
"""

from config.database import db
from datetime import datetime


class Spot(db.Model):
    """📍 Spot - Base Unit of OAP World"""
    __tablename__ = 'spots'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    postcode_prefix = db.Column(db.String(10), nullable=False)
    street_level_address = db.Column(db.Text)
    latitude = db.Column(db.Numeric(10, 8))
    longitude = db.Column(db.Numeric(11, 8))
    area_id = db.Column(db.Integer, db.ForeignKey('areas.id'))
    status = db.Column(db.String(50), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    area = db.relationship('Area', back_populates='spots')
    users = db.relationship('User', back_populates='home_spot')
    sika_pool = db.relationship('SpotSikaPool', back_populates='spot', uselist=False)
    
    def to_dict(self, include_details=False):
        data = {
            'id': self.id,
            'name': self.name,
            'postcode_prefix': self.postcode_prefix,
            'street_level_address': self.street_level_address,
            'latitude': float(self.latitude) if self.latitude else None,
            'longitude': float(self.longitude) if self.longitude else None,
            'area_id': self.area_id,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_details:
            data['sika_pool'] = self.sika_pool.to_dict() if self.sika_pool else None
            data['user_count'] = len(self.users)
        
        return data


class Area(db.Model):
    """🧭 Area - Collection of Spots (Mid Layer)"""
    __tablename__ = 'areas'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    borough_level = db.Column(db.String(255))
    district_level = db.Column(db.String(255))
    zone_id = db.Column(db.Integer, db.ForeignKey('zones.id'))
    center_latitude = db.Column(db.Numeric(10, 8))
    center_longitude = db.Column(db.Numeric(11, 8))
    status = db.Column(db.String(50), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    zone = db.relationship('Zone', back_populates='areas')
    spots = db.relationship('Spot', back_populates='area')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'borough_level': self.borough_level,
            'district_level': self.district_level,
            'zone_id': self.zone_id,
            'center_latitude': float(self.center_latitude) if self.center_latitude else None,
            'center_longitude': float(self.center_longitude) if self.center_longitude else None,
            'status': self.status,
            'spot_count': len(self.spots)
        }


class Zone(db.Model):
    """🏛 Zone - Collection of Areas (City Layer)"""
    __tablename__ = 'zones'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    city_level = db.Column(db.String(255))
    region_level = db.Column(db.String(255))
    country_code = db.Column(db.String(2), default='GB')
    center_latitude = db.Column(db.Numeric(10, 8))
    center_longitude = db.Column(db.Numeric(11, 8))
    status = db.Column(db.String(50), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    areas = db.relationship('Area', back_populates='zone')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'city_level': self.city_level,
            'region_level': self.region_level,
            'country_code': self.country_code,
            'center_latitude': float(self.center_latitude) if self.center_latitude else None,
            'center_longitude': float(self.center_longitude) if self.center_longitude else None,
            'status': self.status,
            'area_count': len(self.areas)
        }


class User(db.Model):
    """👤 User - Identity & Human State Layer"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Human State Layer
    energy_level = db.Column(db.String(20), default='medium')
    mood_state = db.Column(db.String(50), default='calm')
    stealth_mode = db.Column(db.Boolean, default=False)
    
    # Home Spot
    home_spot_id = db.Column(db.Integer, db.ForeignKey('spots.id'))
    
    # Trust & Reputation
    trust_score = db.Column(db.Numeric(5, 4), default=0.5000)
    reputation_points = db.Column(db.Integer, default=0)
    
    # Account Status
    is_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    home_spot = db.relationship('Spot', back_populates='users')
    sika_accounts = db.relationship('SikaAccount', back_populates='user')
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'energy_level': self.energy_level,
            'mood_state': self.mood_state,
            'stealth_mode': self.stealth_mode,
            'home_spot_id': self.home_spot_id,
            'trust_score': float(self.trust_score) if self.trust_score else 0.5,
            'reputation_points': self.reputation_points,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class SikaAccount(db.Model):
    """💎 SIKA Account - Value System"""
    __tablename__ = 'sika_accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    spot_id = db.Column(db.Integer, db.ForeignKey('spots.id'))
    balance = db.Column(db.Numeric(20, 8), default=0)
    earned_total = db.Column(db.Numeric(20, 8), default=0)
    spent_total = db.Column(db.Numeric(20, 8), default=0)
    last_earned_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='sika_accounts')
    spot = db.relationship('Spot', back_populates='sika_pool')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'spot_id': self.spot_id,
            'balance': float(self.balance) if self.balance else 0,
            'earned_total': float(self.earned_total) if self.earned_total else 0,
            'spent_total': float(self.spent_total) if self.spent_total else 0,
            'last_earned_at': self.last_earned_at.isoformat() if self.last_earned_at else None
        }


class SpotSikaPool(db.Model):
    """💎 Spot SIKA Pool - Local economy pool for each Spot"""
    __tablename__ = 'spot_sika_pools'
    
    id = db.Column(db.Integer, primary_key=True)
    spot_id = db.Column(db.Integer, db.ForeignKey('spots.id'))
    total_pool = db.Column(db.Numeric(20, 8), default=0)
    distributed_today = db.Column(db.Numeric(20, 8), default=0)
    last_distribution_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    spot = db.relationship('Spot', back_populates='sika_pool')
    
    def to_dict(self):
        return {
            'id': self.id,
            'spot_id': self.spot_id,
            'total_pool': float(self.total_pool) if self.total_pool else 0,
            'distributed_today': float(self.distributed_today) if self.distributed_today else 0,
            'last_distribution_date': self.last_distribution_date.isoformat() if self.last_distribution_date else None
        }


# Additional model stubs for other systems
class HRMMemory(db.Model):
    """🧠 HRM Memory - Intelligence System"""
    __tablename__ = 'hrm_memory'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    memory_type = db.Column(db.String(50), nullable=False)
    memory_key = db.Column(db.String(255), nullable=False)
    memory_value = db.Column(db.JSON)
    confidence_score = db.Column(db.Numeric(5, 4))
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'memory_type': self.memory_type,
            'memory_key': self.memory_key,
            'memory_value': self.memory_value,
            'confidence_score': float(self.confidence_score) if self.confidence_score else None
        }


class PulseEvent(db.Model):
    """📡 Pulse Event - Live Activity Stream"""
    __tablename__ = 'pulse_events'
    
    id = db.Column(db.Integer, primary_key=True)
    spot_id = db.Column(db.Integer, db.ForeignKey('spots.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    event_type = db.Column(db.String(100), nullable=False)
    event_data = db.Column(db.JSON)
    energy_level = db.Column(db.Integer, default=50)
    visibility = db.Column(db.String(20), default='public')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'spot_id': self.spot_id,
            'user_id': self.user_id,
            'event_type': self.event_type,
            'event_data': self.event_data,
            'energy_level': self.energy_level,
            'visibility': self.visibility,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class MovementActivity(db.Model):
    """🎪 Movement Activity - Real-world Participation"""
    __tablename__ = 'movement_activities'
    
    id = db.Column(db.Integer, primary_key=True)
    spot_id = db.Column(db.Integer, db.ForeignKey('spots.id'))
    activity_type = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    location_name = db.Column(db.String(255))
    latitude = db.Column(db.Numeric(10, 8))
    longitude = db.Column(db.Numeric(11, 8))
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)
    max_participants = db.Column(db.Integer)
    current_participants = db.Column(db.Integer, default=0)
    sika_reward = db.Column(db.Numeric(20, 8), default=0)
    status = db.Column(db.String(50), default='scheduled')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'spot_id': self.spot_id,
            'activity_type': self.activity_type,
            'title': self.title,
            'description': self.description,
            'location_name': self.location_name,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'current_participants': self.current_participants,
            'max_participants': self.max_participants,
            'sika_reward': float(self.sika_reward) if self.sika_reward else 0,
            'status': self.status
        }


class UserSpotActivity(db.Model):
    """Track user activity in different Spots"""
    __tablename__ = 'user_spot_activity'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    spot_id = db.Column(db.Integer, db.ForeignKey('spots.id'), nullable=False)
    first_visit = db.Column(db.Date)
    last_visit = db.Column(db.DateTime)
    visit_count = db.Column(db.Integer, default=0)
    contribution_score = db.Column(db.Numeric(10, 4), default=0)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'spot_id'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'spot_id': self.spot_id,
            'first_visit': self.first_visit.isoformat() if self.first_visit else None,
            'last_visit': self.last_visit.isoformat() if self.last_visit else None,
            'visit_count': self.visit_count,
            'contribution_score': float(self.contribution_score) if self.contribution_score else 0
        }
