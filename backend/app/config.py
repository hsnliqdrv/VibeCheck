import os
from datetime import timedelta


class Config:
    """Application configuration"""
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://localhost:5432/vibecheck')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = FLASK_ENV == 'development'
    
    # Email (Resend)
    RESEND_API_KEY = os.getenv('RESEND_API_KEY')
    EMAIL_FROM_ADDRESS = os.getenv('EMAIL_FROM_ADDRESS', 'noreply@vibeaura.app')
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')
