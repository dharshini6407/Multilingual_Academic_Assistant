import re
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import db
from models import User, UserProfile, NotificationPreference
from services.auth_service import hash_password, verify_password, generate_user_token

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new student or admin account with validation."""
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    full_name = data.get('full_name', '').strip()
    role = data.get('role', 'student').strip().lower()
    department = data.get('department', 'Computer Science and Engineering')
    year_of_study = int(data.get('year_of_study', 3))
    semester = int(data.get('semester', 5))
    preferred_language = data.get('preferred_language', 'en')

    # Input validations
    if not email or not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return jsonify({'success': False, 'message': 'A valid email address is required.'}), 400

    if not password or len(password) < 6:
        return jsonify({'success': False, 'message': 'Password must be at least 6 characters.'}), 400

    if not full_name:
        return jsonify({'success': False, 'message': 'Full name is required.'}), 400

    if role not in ['student', 'admin']:
        role = 'student'

    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': 'An account with this email already exists.'}), 409

    try:
        # Create user
        user = User(
            email=email,
            password_hash=hash_password(password),
            role=role,
            is_active=True
        )
        db.session.add(user)
        db.session.flush()

        # Create profile
        profile = UserProfile(
            user_id=user.id,
            full_name=full_name,
            department=department,
            year_of_study=year_of_study,
            semester=semester,
            preferred_language=preferred_language
        )
        db.session.add(profile)

        # Create default notification preferences
        pref = NotificationPreference(
            user_id=user.id,
            exam_alerts=True,
            assignment_alerts=True,
            activity_alerts=True,
            low_attendance_warning=True,
            study_plan_reminders=True,
            preferred_channel='in_app'
        )
        db.session.add(pref)

        db.session.commit()

        token = generate_user_token(user)
        return jsonify({
            'success': True,
            'message': 'Registration successful.',
            'access_token': token,
            'user': user.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Registration failed: {str(e)}'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate student or admin and return JWT access token."""
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'success': False, 'message': 'Email and password are required.'}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not verify_password(password, user.password_hash):
        return jsonify({'success': False, 'message': 'Invalid email or password.'}), 401

    if not user.is_active:
        return jsonify({'success': False, 'message': 'Account is inactive. Please contact administration.'}), 403

    token = generate_user_token(user)
    return jsonify({
        'success': True,
        'message': 'Login successful.',
        'access_token': token,
        'user': user.to_dict()
    }), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_profile():
    """Get authenticated user profile and notification preferences."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found.'}), 404

    return jsonify({
        'success': True,
        'user': user.to_dict(),
        'preferences': user.preferences.to_dict() if user.preferences else {}
    }), 200

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update profile details (name, language, semester, department)."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found.'}), 404

    data = request.get_json() or {}
    profile = user.profile
    if not profile:
        profile = UserProfile(user_id=user.id, full_name='Student')
        db.session.add(profile)

    if 'full_name' in data and data['full_name'].strip():
        profile.full_name = data['full_name'].strip()
    if 'department' in data:
        profile.department = data['department'].strip()
    if 'year_of_study' in data:
        profile.year_of_study = int(data['year_of_study'])
    if 'semester' in data:
        profile.semester = int(data['semester'])
    if 'preferred_language' in data and data['preferred_language'] in ['en', 'ta', 'tanglish']:
        profile.preferred_language = data['preferred_language']

    db.session.commit()
    return jsonify({
        'success': True,
        'message': 'Profile updated successfully.',
        'user': user.to_dict()
    }), 200

@auth_bp.route('/preferences', methods=['PUT'])
@jwt_required()
def update_preferences():
    """Update notification preferences."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found.'}), 404

    data = request.get_json() or {}
    pref = user.preferences
    if not pref:
        pref = NotificationPreference(user_id=user.id)
        db.session.add(pref)

    for field in ['exam_alerts', 'assignment_alerts', 'activity_alerts', 'low_attendance_warning', 'study_plan_reminders']:
        if field in data:
            setattr(pref, field, bool(data[field]))

    if 'preferred_channel' in data and data['preferred_channel'] in ['in_app', 'email', 'both']:
        pref.preferred_channel = data['preferred_channel']

    db.session.commit()
    return jsonify({
        'success': True,
        'message': 'Notification preferences updated successfully.',
        'preferences': pref.to_dict()
    }), 200
