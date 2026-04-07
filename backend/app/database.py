from sqlalchemy import create_engine
from sqlalchemy.schema import DropTable
from sqlalchemy.orm import scoped_session, sessionmaker, declarative_base
from flask import g

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
    # NOTE: badge.py is legacy – gamification.py already defines the Badge table
    from app.models import user, content, share, post, gamification, room
    
    # In development mode, drop all tables and recreate them
    if app.config.get('FLASK_ENV', 'development') == 'development':
        _drop_all_tables(engine)
        print("Development mode: Dropped all tables")
    
    # Create all tables
    Base.metadata.create_all(engine)

    # Seed default aesthetic rooms if missing
    from app.seed_rooms import seed_rooms
    from app.seed_sample_users import seed_sample_users
    from app.seed_content import seed_startup_content
    db = session_factory()
    try:
        seed_rooms(db)
        seed_sample_users(db)
        seed_startup_content(db, items_per_category=5)
    finally:
        db.close()


def _drop_all_tables(db_engine):
    """Drop all tables, using CASCADE on PostgreSQL so dependent objects are removed too."""
    if db_engine.dialect.name == 'postgresql':
        with db_engine.begin() as connection:
            for table in reversed(Base.metadata.sorted_tables):
                connection.execute(DropTable(table, if_exists=True, cascade=True))
    else:
        Base.metadata.drop_all(db_engine)


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
