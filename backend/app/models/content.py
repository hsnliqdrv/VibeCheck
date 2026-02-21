from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Text, Enum, DateTime
import enum
from app.database import Base


class MovieType(str, enum.Enum):
    """Movie type enumeration"""
    MOVIE = "movie"
    TV = "tv"


class GameDifficulty(str, enum.Enum):
    """Game difficulty enumeration"""
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"


class Movie(Base):
    """Movie model matching the OpenAPI Movie schema"""
    __tablename__ = 'movies'
    
    id = Column(String, primary_key=True)
    title = Column(String(500), nullable=False, index=True)
    year = Column(Integer, nullable=False)
    director = Column(String(255), nullable=False)
    poster = Column(Text, nullable=True)
    season = Column(Integer, nullable=True)
    episode = Column(Integer, nullable=True)
    type = Column(Enum(MovieType), nullable=False, default=MovieType.MOVIE)
    url = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """Convert movie to dictionary matching OpenAPI schema"""
        result = {
            'id': self.id,
            'title': self.title,
            'year': self.year,
            'director': self.director,
            'type': self.type.value if isinstance(self.type, MovieType) else self.type,
            'url': self.url
        }
        if self.poster is not None:
            result['poster'] = self.poster
        if self.season is not None:
            result['season'] = self.season
        if self.episode is not None:
            result['episode'] = self.episode
        return result
    
    def __repr__(self):
        return f'<Movie {self.title} ({self.year})>'


class Album(Base):
    """Album model matching the OpenAPI Album schema"""
    __tablename__ = 'albums'
    
    id = Column(String, primary_key=True)
    title = Column(String(500), nullable=False, index=True)
    artist = Column(String(255), nullable=False, index=True)
    cover = Column(Text, nullable=True)
    duration = Column(Integer, nullable=True)  # Duration in seconds
    url = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """Convert album to dictionary matching OpenAPI schema"""
        result = {
            'id': self.id,
            'title': self.title,
            'artist': self.artist,
            'url': self.url
        }
        if self.cover is not None:
            result['cover'] = self.cover
        if self.duration is not None:
            result['duration'] = self.duration  # type: ignore
        return result
    
    def __repr__(self):
        return f'<Album {self.title} by {self.artist}>'


class Game(Base):
    """Game model matching the OpenAPI Game schema"""
    __tablename__ = 'games'
    
    id = Column(String, primary_key=True)
    title = Column(String(500), nullable=False, index=True)
    platform = Column(String(255), nullable=False)
    cover = Column(Text, nullable=True)
    difficulty = Column(Enum(GameDifficulty), nullable=True)
    url = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """Convert game to dictionary matching OpenAPI schema"""
        result = {
            'id': self.id,
            'title': self.title,
            'platform': self.platform,
            'url': self.url
        }
        if self.cover is not None:
            result['cover'] = self.cover
        if self.difficulty is not None:
            result['difficulty'] = self.difficulty.value if isinstance(self.difficulty, GameDifficulty) else self.difficulty
        return result
    
    def __repr__(self):
        return f'<Game {self.title} ({self.platform})>'


class Book(Base):
    """Book model matching the OpenAPI Book schema"""
    __tablename__ = 'books'
    
    id = Column(String, primary_key=True)
    title = Column(String(500), nullable=False, index=True)
    author = Column(String(255), nullable=False, index=True)
    cover = Column(Text, nullable=True)
    total_pages = Column(Integer, nullable=True)
    url = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """Convert book to dictionary matching OpenAPI schema"""
        result = {
            'id': self.id,
            'title': self.title,
            'author': self.author,
            'url': self.url
        }
        if self.cover is not None:
            result['cover'] = self.cover
        if self.total_pages is not None:
            result['totalPages'] = self.total_pages  # type: ignore
        return result
    
    def __repr__(self):
        return f'<Book {self.title} by {self.author}>'


class Location(Base):
    """Location model matching the OpenAPI Location schema"""
    __tablename__ = 'locations'
    
    id = Column(String, primary_key=True)
    name = Column(String(500), nullable=False, index=True)
    city = Column(String(255), nullable=False, index=True)
    country = Column(String(255), nullable=False, index=True)
    image = Column(Text, nullable=True)
    weather = Column(String(100), nullable=True)
    temperature = Column(Float, nullable=True)
    timezone = Column(String(100), nullable=True)
    url = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """Convert location to dictionary matching OpenAPI schema"""
        result = {
            'id': self.id,
            'name': self.name,
            'city': self.city,
            'country': self.country,
            'url': self.url
        }
        if self.image is not None:
            result['image'] = self.image
        if self.weather is not None:
            result['weather'] = self.weather
        if self.temperature is not None:
            result['temperature'] = self.temperature
        if self.timezone is not None:
            result['timezone'] = self.timezone
        return result
    
    def __repr__(self):
        return f'<Location {self.name}, {self.country}>'
