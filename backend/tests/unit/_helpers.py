def register_user(client, email='test@example.com', username='testuser', password='Test1234'):
    """Register a user and return the response."""
    return client.post('/api/v1/auth/register', json={
        'email': email,
        'username': username,
        'password': password,
    })


def get_verification_token(app, email):
    """Get a raw verification token for a user, using a proper request context."""
    from app.models.user import User

    with app.test_request_context():
        from app.database import get_db, close_db

        db = get_db()
        user = db.query(User).filter_by(email=email).first()
        if user is not None and not bool(user.email_verified):
            raw_token = user.generate_verification_token()
            db.commit()
            close_db()
            return raw_token
        close_db()
    return None


def get_reset_token(app, email):
    """Get a raw reset token for a user."""
    from app.models.user import User

    with app.test_request_context():
        from app.database import get_db, close_db

        db = get_db()
        user = db.query(User).filter_by(email=email).first()
        assert user is not None
        raw_token = user.generate_reset_token()
        db.commit()
        close_db()
        return raw_token


def register_and_verify(client, app, email, username, password='Test1234'):
    """Register and verify a user. Returns JWT token."""
    register_user(client, email, username, password)
    raw_token = get_verification_token(app, email)
    if raw_token:
        client.get(f'/api/v1/auth/verify-email?token={raw_token}')

    resp = client.post('/api/v1/auth/login', json={
        'email': email,
        'password': password,
    })
    return resp.get_json().get('token')


def get_first_room_id(app):
    """Return the first seeded room id for tests."""
    from app.models.room import AestheticRoom

    with app.test_request_context():
        from app.database import get_db, close_db

        db = get_db()
        room = db.query(AestheticRoom).order_by(AestheticRoom.created_at.asc()).first()
        room_id = room.id if room else None
        close_db()
        return room_id
