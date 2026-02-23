# Models package
from app.models.user import User
from app.models.content import Movie, Album, Game, Book, Location, MovieType, GameDifficulty
from app.models.share import Share
# from app.models.badge import Badge, UserBadge, CuratorLevel
# __all__ = ['User', 'Movie', 'Album', 'Game', 'Book', 'Location', 'MovieType', 'GameDifficulty', 'Share', 'Badge', 'UserBadge', 'CuratorLevel']

from app.models.gamification import Badge, UserBadge, CuratorLevel, UserCuratorStats
__all__ = ['User', 'Movie', 'Album', 'Game', 'Book', 'Location', 'MovieType', 'GameDifficulty', 'Share', 'Badge', 'UserBadge', 'CuratorLevel', '`UserCuratorStats`']
