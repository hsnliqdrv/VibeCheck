# Routes package
from app.routes.auth import auth_bp
from app.routes.badges import badges_bp, curator_bp

__all__ = ['auth_bp', 'badges_bp', 'curator_bp']
