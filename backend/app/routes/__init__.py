# Routes package
from app.routes.auth import auth_bp
from app.routes.content import content_bp
from app.routes.search import search_bp
from app.routes.user_profile import user_profile_bp
from app.routes.aura import aura_bp
from app.routes.social import social_bp
# from app.routes.badges import badges_bp, curator_bp
# __all__= [...'badges_bp', 'curator_bp'...]
# __all__ = ['auth_bp', 'content_bp', 'search_bp', 'user_profile_bp', 'aura_bp', 'social_bp', 'badges_bp', 'curator_bp']

from app.routes.gamification import gamification_bp
__all__ = ['auth_bp', 'content_bp', 'search_bp', 'user_profile_bp', 'aura_bp', 'social_bp', 'gamification_bp']
