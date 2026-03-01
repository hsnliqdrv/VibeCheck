# backend/app/routes/__init__.py
# Routes package - регистрируем все Blueprints здесь

from app.routes.auth import auth_bp
from app.routes.content import content_bp
from app.routes.search import search_bp
from app.routes.user_profile import user_profile_bp
from app.routes.aura import aura_bp
from app.routes.community import community_bp  # <-- добавлено

__all__ = [
    'auth_bp',
    'content_bp',
    'search_bp',
    'user_profile_bp',
    'aura_bp',
    'community_bp',  # <-- экспортируем
]
