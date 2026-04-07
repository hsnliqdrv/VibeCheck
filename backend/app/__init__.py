from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flasgger import Swagger
from app.config import Config
from app.database import init_db, close_db

jwt = JWTManager()


def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    CORS(app)
    jwt.init_app(app)
    
    # JWT error handlers - ensure proper 401 responses
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Missing or invalid authentication token'
        }), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Invalid authentication token'
        }), 401
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_data):
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Token has expired'
        }), 401
    
    # Initialize Swagger - generates docs from actual implementation
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": 'apispec',
                "route": '/apispec.json',
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/docs"
    }
    
    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "VibeCheck Backend API - Live Documentation",
            "description": "Auto-generated API documentation from actual backend implementation. This reflects what the backend actually does, allowing comparison with openapi-mvp.yaml specification.",
            "version": "0.1.0",
            "contact": {
                "name": "VibeCheck Support"
            }
        },
        "host": "localhost:3000",
        "basePath": "/api/v1",
        "schemes": ["http"],
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "JWT Authorization header using the Bearer scheme. Example: 'Authorization: Bearer {token}'"
            }
        }
    }
    
    Swagger(app, config=swagger_config, template=swagger_template)
    
    # Initialize database
    init_db(app)
    app.teardown_appcontext(close_db)
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.content import content_bp
    from app.routes.user_profile import user_profile_bp
    from app.routes.aura import aura_bp
    from app.routes.search import search_bp
    from app.routes.social import social_bp
    from app.routes.moderation import moderation_bp
    from app.routes.discovery import discovery_bp
    from app.routes.upload import upload_bp
    
    # from app.routes.badges import badges_bp, curator_bp
    from app.routes.gamification import gamification_bp

    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(content_bp, url_prefix='/api/v1/content')
    app.register_blueprint(user_profile_bp, url_prefix='/api/v1/users')
    app.register_blueprint(aura_bp, url_prefix='/api/v1/aura')
    app.register_blueprint(search_bp, url_prefix='/api/v1/search')
    app.register_blueprint(social_bp, url_prefix='/api/v1/social')
    app.register_blueprint(moderation_bp, url_prefix='/api/v1/moderation')
    app.register_blueprint(discovery_bp, url_prefix='/api/v1/discovery')
    app.register_blueprint(upload_bp, url_prefix='/api/v1/upload')
    app.register_blueprint(gamification_bp, url_prefix='/api/v1')
    
    return app
