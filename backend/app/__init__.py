from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flasgger import Swagger
from app.config import Config
from app.database import init_db

jwt = JWTManager()


def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    CORS(app)
    jwt.init_app(app)
    
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
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.content import content_bp
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(content_bp, url_prefix='/api/v1/content')
    
    return app
