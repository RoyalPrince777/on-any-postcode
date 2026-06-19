"""Configuration package for OAP World backend"""
from config.config import Config, DevelopmentConfig, ProductionConfig, TestingConfig
from config.database import db, migrate
