from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, declarative_base
from flask import current_app, g

Base = declarative_base()
engine = None
session_factory = None


def init_db(app):
    """Initialize database connection"""
    global engine, session_factory
    
    engine = create_engine(
        app.config['SQLALCHEMY_DATABASE_URI'],
        echo=app.config['DEBUG']
    )
    session_factory = sessionmaker(bind=engine)
    
    # Import all models to ensure they're registered
    from app.models import user, content
    
    # Create all tables
    Base.metadata.create_all(engine)


def get_db():
    """Get database session for current request context"""
    if 'db' not in g:
        if session_factory is None:
            raise RuntimeError("Database not initialized. Call init_db first.")
        g.db = scoped_session(session_factory)
    return g.db


def close_db(e=None):
    """Close database session"""
    db = g.pop('db', None)
    if db is not None:
        db.remove()
