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
    
    # DigitalOcean Spaces
    DO_SPACES_NAME = os.getenv('DO_SPACES_NAME', 'vibecheck')
    DO_SPACES_REGION = os.getenv('DO_SPACES_REGION', 'sfo3')
    DO_SPACES_KEY = os.getenv('DO_SPACES_KEY', '')
    DO_SPACES_SECRET = os.getenv('DO_SPACES_SECRET', '')
    DO_SPACES_ENDPOINT = os.getenv('DO_SPACES_ENDPOINT', 'https://sfo3.digitaloceanspaces.com')
    
    # Upload settings
    AVATAR_MAX_SIZE = 5 * 1024 * 1024  # 5MB
    AVATAR_ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp']
    POST_IMAGE_MAX_SIZE = 20 * 1024 * 1024  # 20MB
    POST_IMAGE_ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
    PRESIGNED_URL_EXPIRY = 3600  # 1 hour
