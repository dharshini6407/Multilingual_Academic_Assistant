import os
import sys
import pytest

# Add backend directory to sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app import create_app
from config import Config
from db import db
from models import (
    User, UserProfile, NotificationPreference, Subject,
    AttendanceRecord, Examination, Assignment, Notification,
    AcademicDocument, DocumentChunk, StudyPlan, StudyTask
)
from services.auth_service import hash_password, generate_user_token

class TestConfig(Config):
    TESTING = True
    DB_TYPE = 'sqlite'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    AI_PROVIDER = 'none'
    AI_API_KEY = ''

@pytest.fixture
def app():
    os.environ['TESTING'] = 'True'
    app = create_app(TestConfig)
    
    with app.app_context():
        db.create_all()
        
        # Seed test admin
        admin = User(
            email='admin_test@college.edu',
            password_hash=hash_password('AdminPass@123'),
            role='admin',
            is_active=True
        )
        db.session.add(admin)
        db.session.flush()

        admin_prof = UserProfile(
            user_id=admin.id,
            full_name='Dr. Test Admin',
            department='CSE'
        )
        db.session.add(admin_prof)

        # Seed test student
        student = User(
            email='student_test@college.edu',
            password_hash=hash_password('StudentPass@123'),
            role='student',
            is_active=True
        )
        db.session.add(student)
        db.session.flush()

        student_prof = UserProfile(
            user_id=student.id,
            full_name='Test Student',
            department='CSE',
            year_of_study=3,
            semester=5,
            preferred_language='tanglish'
        )
        db.session.add(student_prof)

        student_pref = NotificationPreference(
            user_id=student.id,
            exam_alerts=True,
            assignment_alerts=True
        )
        db.session.add(student_pref)

        # Seed Subject
        sub = Subject(
            code='CS9999',
            name='Test Autonomous Computing',
            department='CSE',
            semester=5,
            credits=3
        )
        db.session.add(sub)

        db.session.commit()
        yield app

        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def admin_token(app):
    with app.app_context():
        admin = User.query.filter_by(role='admin').first()
        return generate_user_token(admin)

@pytest.fixture
def student_token(app):
    with app.app_context():
        student = User.query.filter_by(role='student').first()
        return generate_user_token(student)

@pytest.fixture
def admin_headers(admin_token):
    return {'Authorization': f'Bearer {admin_token}'}

@pytest.fixture
def student_headers(student_token):
    return {'Authorization': f'Bearer {student_token}'}
