"""Configuration settings for OAP World backend"""
import os


class Config:
    """Base configuration class"""
    
    # Secret key for security
    SECRET_KEY = os.environ.get('SECRET_KEY', 'oap-world-secret-key-change-in-production')
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 
        'postgresql://localhost:5432/oap_world'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # API Configuration
    API_VERSION = 'v1'
    API_TITLE = 'OAP World API'
    
    # CORS Configuration
    CORS_ORIGINS = ['*']  # Configure appropriately for production
    
    # SIKA Economy Settings
    SIKA_DEFAULT_RATES = {
        'arena_participation': 10.0,
        'movement_activity': 15.0,
        'signal_contribution': 5.0,
        'link_engagement': 2.0,
        'spot_activity': 3.0
    }
    
    # Trust Thresholds
    TRUST_THRESHOLDS = {
        'minimum_for_transfer': 0.6000,
        'high_trust': 0.8000,
        'verified_user': 0.7000
    }
    
    # HRM Memory Settings
    HRM_MEMORY_EXPIRY_DAYS = 90
    HRM_PATTERN_CONFIDENCE_THRESHOLD = 0.75
    
    # Guardian Safety Settings
    GUARDIAN_AUTO_MODERATE = True
    GUARDIAN_RISK_THRESHOLD = 0.80
    
    # Pagination
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_ECHO = False
    
    # Override with production secrets
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
