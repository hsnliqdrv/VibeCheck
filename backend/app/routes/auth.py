from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token
from sqlalchemy.exc import IntegrityError
from email_validator import validate_email, EmailNotValidError
from datetime import datetime
import random
import re
from app.database import get_db
from app.models.user import User
from app.services.email_service import send_verification_email, send_password_reset_email

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
            user:
              type: object
      400:
        description: Bad request - missing or invalid fields
      401:
        description: Invalid credentials
      403:
        description: Email not verified
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
        
        # Check email verification
        if not user.email_verified:
            return jsonify({
                'error': 'Forbidden',
                'message': 'Email not verified. Please verify your email before logging in.'
            }), 403
        
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
              example: Password123
            username:
              type: string
              minLength: 3
              maxLength: 20
              example: aesthetic_anna
    responses:
      201:
        description: Registration successful. Verification email sent.
        schema:
          type: object
          properties:
            message:
              type: string
            user:
              type: object
            emailVerificationRequired:
              type: boolean
      400:
        description: Bad request - validation error
      409:
        description: Email or username already exists
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
        
        avatar_index = random.randint(1, 27)
        avatar_url = f"https://cdn.jsdelivr.net/gh/alohe/avatars/png/vibrent_{avatar_index}.png"

        # Create new user (unverified)
        new_user = User(
            email=email,
            username=username,
            avatar=avatar_url,
            email_verified=False
        )
        new_user.set_password(password)
        
        # Generate email verification token
        raw_token = new_user.generate_verification_token()
        
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
        
        # Send verification email via Resend
        try:
            send_verification_email(email, username, raw_token)
        except Exception as mail_err:
            current_app.logger.error(f"Failed to send verification email to {email}: {mail_err}")
        
        # Do NOT issue JWT at registration — user must verify email first
        return jsonify({
            'message': 'Registration successful. Please check your email to verify your account.',
            'user': new_user.to_dict(),
            'emailVerificationRequired': True
        }), 201
    
    except Exception as e:
        if db is not None:
            db.rollback()
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e)
        }), 500


@auth_bp.route('/verify-email', methods=['GET'])
def verify_email():
    """
    Verify user email
    ---
    tags:
      - Auth
    parameters:
      - name: token
        in: query
        type: string
        required: true
        description: Email verification token
    responses:
      200:
        description: Email verified successfully
        schema:
          type: object
          properties:
            message:
              type: string
            token:
              type: string
              description: JWT authentication token
            user:
              type: object
      400:
        description: Invalid or expired verification token
      404:
        description: Token not found
    """
    db = None
    try:
        raw_token = request.args.get('token')
        
        if not raw_token:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Verification token is required'
            }), 400
        
        # Hash the incoming token to compare with stored hash
        hashed_token = User.hash_token(raw_token)
        
        db = get_db()
        
        # Find user by hashed verification token
        user = db.query(User).filter_by(verification_token=hashed_token).first()
        
        if not user:
            return jsonify({
                'error': 'Not Found',
                'message': 'Invalid verification token'
            }), 404
        
        # Check token expiry
        if user.verification_token_expiry and user.verification_token_expiry < datetime.utcnow():
            return jsonify({
                'error': 'Bad Request',
                'message': 'Verification token has expired'
            }), 400
        
        # Mark email as verified and clear token
        user.email_verified = True
        user.verification_token = None
        user.verification_token_expiry = None
        
        db.commit()
        db.refresh(user)
        
        # Issue JWT now that email is verified
        access_token = create_access_token(identity=user.user_id)
        
        return jsonify({
            'message': 'Email verified successfully.',
            'token': access_token,
            'user': user.to_dict()
        }), 200
    
    except Exception as e:
        if db is not None:
            db.rollback()
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e)
        }), 500


@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """
    Request password reset
    ---
    tags:
      - Auth
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - email
          properties:
            email:
              type: string
              format: email
              example: user@example.com
    responses:
      200:
        description: Password reset email sent (always returns 200 for security)
        schema:
          type: object
          properties:
            message:
              type: string
      400:
        description: Bad request
    """
    db = None
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Request body is required'
            }), 400
        
        email = data.get('email')
        
        if not email:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Email is required'
            }), 400
        
        # Validate email format
        try:
            validate_email(email, check_deliverability=False)
        except EmailNotValidError:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Invalid email format'
            }), 400
        
        db = get_db()
        
        # Always return success message for security (don't leak user existence)
        success_message = 'If an account exists with this email, a password reset link has been sent.'
        
        user = db.query(User).filter_by(email=email).first()
        
        if user and user.email_verified:
            raw_token = user.generate_reset_token()
            db.commit()
            
            try:
                send_password_reset_email(email, user.username, raw_token)
            except Exception as mail_err:
                current_app.logger.error(f"Failed to send password reset email to {email}: {mail_err}")
        
        return jsonify({
            'message': success_message
        }), 200
    
    except Exception as e:
        if db is not None:
            db.rollback()
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e)
        }), 500


@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """
    Reset user password
    ---
    tags:
      - Auth
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - token
            - newPassword
          properties:
            token:
              type: string
              description: Password reset token
            newPassword:
              type: string
              format: password
              description: New password
    responses:
      200:
        description: Password reset successfully
        schema:
          type: object
          properties:
            message:
              type: string
      400:
        description: Invalid or expired reset token
      404:
        description: Token not found
    """
    db = None
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Request body is required'
            }), 400
        
        raw_token = data.get('token')
        new_password = data.get('newPassword')
        
        if not raw_token or not new_password:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Token and new password are required'
            }), 400
        
        # Validate new password strength
        is_valid, message = validate_password_strength(new_password)
        if not is_valid:
            return jsonify({
                'error': 'Bad Request',
                'message': message
            }), 400
        
        # Hash the incoming token to compare with stored hash
        hashed_token = User.hash_token(raw_token)
        
        db = get_db()
        
        # Find user by hashed reset token that hasn't been used
        user = db.query(User).filter_by(
            reset_token=hashed_token,
            reset_token_used=False
        ).first()
        
        if not user:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Invalid or expired reset token'
            }), 400
        
        # Check token expiry
        if user.reset_token_expiry and user.reset_token_expiry < datetime.utcnow():
            return jsonify({
                'error': 'Bad Request',
                'message': 'Reset token has expired'
            }), 400
        
        # Update password and invalidate token
        user.set_password(new_password)
        user.reset_token_used = True
        user.reset_token = None
        user.reset_token_expiry = None
        
        db.commit()
        
        return jsonify({
            'message': 'Password has been reset successfully.'
        }), 200
    
    except Exception as e:
        if db is not None:
            db.rollback()
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e)
        }), 500
