from functools import wraps
from flask import jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, get_jwt_identity, get_jwt, verify_jwt_in_request
from db import db
from models import User

def hash_password(password: str) -> str:
    """Securely hash password using PBKDF2 with SHA-256."""
    return generate_password_hash(password, method='pbkdf2:sha256')

def verify_password(password: str, password_hash: str) -> bool:
    """Verify raw password against hash."""
    return check_password_hash(password_hash, password)

def generate_user_token(user: User) -> str:
    """Generate JWT access token containing user identity and role claim."""
    additional_claims = {
        'role': user.role,
        'email': user.email
    }
    return create_access_token(identity=str(user.id), additional_claims=additional_claims)

def get_current_authenticated_user():
    """Retrieve the User instance for the current JWT session."""
    verify_jwt_in_request()
    user_id = get_jwt_identity()
    if not user_id:
        return None
    return User.query.get(int(user_id))

def admin_required():
    """Decorator to protect routes so only admins can execute them."""
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            role = claims.get('role')
            if role != 'admin':
                # Double-check DB in case token is stale
                user_id = get_jwt_identity()
                user = db.session.get(User, int(user_id)) if user_id else None
                if not user or user.role != 'admin':
                    return jsonify({
                        'success': False,
                        'message': 'Administrative privileges required for this action.'
                    }), 403
            return fn(*args, **kwargs)
        return decorator
    return wrapper
