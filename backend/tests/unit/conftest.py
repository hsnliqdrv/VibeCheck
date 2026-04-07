import os
import sys
from pathlib import Path

import pytest

backend_root = Path(os.getenv("BACKEND_PATH", Path.cwd())).resolve()
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.config import Config

Config.SQLALCHEMY_DATABASE_URI = 'sqlite:///test_unit_vibecheck.db'

os.environ.setdefault('FLASK_ENV', 'development')
os.environ.setdefault('JWT_SECRET_KEY', 'test-secret-key')

from app import create_app


@pytest.fixture(scope='module')
def app():
    """Create Flask app for unit tests."""
    application = create_app()
    application.config['TESTING'] = True
    application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_unit_vibecheck.db'
    yield application

    db_path = Path.cwd() / 'test_unit_vibecheck.db'
    if db_path.exists():
        try:
            db_path.unlink()
        except OSError:
            pass


@pytest.fixture(scope='module')
def client(app):
    """Create test client."""
    return app.test_client()
