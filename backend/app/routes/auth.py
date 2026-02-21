from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from sqlalchemy.exc import IntegrityError
from email_validator import validate_email, EmailNotValidError
import re
from app.database import get_db
from app.models.user import User

auth_bp = Blueprint('auth', __name__)


def validate_password_strength(password):
    """
    Validate password strength.
    Requirements:
    - At least 8 characters
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one digit
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    return True, "Password is strong"


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    User login endpoint
    ---
    tags:
      - Auth
    parameters:
      - in: body
        name: body
        description: User login credentials
        required: true
        schema:
          type: object
          required:
            - email
            - password
          properties:
            email:
              type: string
              format: email
              example: user@example.com
            password:
              type: string
              format: password
              example: password123
    responses:
      200:
        description: Login successful
        schema:
          type: object
          properties:
            token:
              type: string
              description: JWT access token
              example: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9
            user:
              type: object
              properties:
                userId:
                  type: string
                  example: u_123abc456def
                email:
                  type: string
                  example: user@example.com
                username:
                  type: string
                  example: aesthetic_anna
                avatar:
                  type: string
                  nullable: true
                bio:
                  type: string
                  nullable: true
                createdAt:
                  type: string
                  format: date-time
                updatedAt:
                  type: string
                  format: date-time
      400:
        description: Bad request - missing or invalid fields
        schema:
          type: object
          properties:
            error:
              type: string
              example: Bad Request
            message:
              type: string
              example: Email and password are required
      401:
        description: Invalid credentials
        schema:
          type: object
          properties:
            error:
              type: string
              example: Unauthorized
            message:
              type: string
              example: Invalid email or password
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Request body is required'
            }), 400
        
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Email and password are required'
            }), 400
        
        # Validate email format
        try:
            validate_email(email, check_deliverability=False)
        except EmailNotValidError:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Invalid email format'
            }), 400
        
        # Get database session
        db = get_db()
        
        # Find user by email
        user = db.query(User).filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Invalid email or password'
            }), 401
        
        # Create JWT token
        access_token = create_access_token(identity=user.user_id)
        
        return jsonify({
            'token': access_token,
            'user': user.to_dict()
        }), 200
    
    except Exception as e:
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e)
        }), 500


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    User registration endpoint
    ---
    tags:
      - Auth
    parameters:
      - in: body
        name: body
        description: User registration data
        required: true
        schema:
          type: object
          required:
            - email
            - password
            - username
          properties:
            email:
              type: string
              format: email
              example: user@example.com
            password:
              type: string
              format: password
              minLength: 1
              example: password123
            username:
              type: string
              minLength: 3
              maxLength: 20
              example: aesthetic_anna
    responses:
      201:
        description: Registration successful
        schema:
          type: object
          properties:
            token:
              type: string
              description: JWT access token
              example: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9
            user:
              type: object
              properties:
                userId:
                  type: string
                  example: u_123abc456def
                email:
                  type: string
                  example: user@example.com
                username:
                  type: string
                  example: aesthetic_anna
                avatar:
                  type: string
                  nullable: true
                bio:
                  type: string
                  nullable: true
                createdAt:
                  type: string
                  format: date-time
                updatedAt:
                  type: string
                  format: date-time
      400:
        description: Bad request - validation error
        schema:
          type: object
          properties:
            error:
              type: string
              example: Bad Request
            message:
              type: string
              example: Username must be between 3 and 20 characters
      409:
        description: Email or username already exists
        schema:
          type: object
          properties:
            error:
              type: string
              example: Conflict
            message:
              type: string
              example: Email already exists
    """
    db = None
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Request body is required'
            }), 400
        
        email = data.get('email')
        password = data.get('password')
        username = data.get('username')
        
        if not email or not password or not username:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Email, password, and username are required'
            }), 400
        
        # Validate email format
        try:
            validate_email(email, check_deliverability=False)
        except EmailNotValidError:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Invalid email format'
            }), 400
        
        # Validate username length
        if len(username) < 3 or len(username) > 20:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Username must be between 3 and 20 characters'
            }), 400
        
        # Validate password strength
        is_valid, message = validate_password_strength(password)
        if not is_valid:
            return jsonify({
                'error': 'Bad Request',
                'message': message
            }), 400
        
        # Get database session
        db = get_db()
        
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.email == email) | (User.username == username)
        ).first()
        
        if existing_user:
            if existing_user.email == email:
                return jsonify({
                    'error': 'Conflict',
                    'message': 'Email already exists'
                }), 409
            else:
                return jsonify({
                    'error': 'Conflict',
                    'message': 'Username already exists'
                }), 409
        
        # Create new user
        new_user = User(
            email=email,
            username=username
        )
        new_user.set_password(password)
        
        try:
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
        except IntegrityError:
            db.rollback()
            return jsonify({
                'error': 'Conflict',
                'message': 'Email or username already exists'
            }), 409
        
        # Create JWT token
        access_token = create_access_token(identity=new_user.user_id)
        
        return jsonify({
            'token': access_token,
            'user': new_user.to_dict()
        }), 201
    
    except Exception as e:
        if db is not None:
            db.rollback()
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e)
        }), 500
