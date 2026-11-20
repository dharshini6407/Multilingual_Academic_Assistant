import pytest

def test_student_registration_success(client):
    payload = {
        'email': 'new_student@college.edu',
        'password': 'SecurePassword@123',
        'full_name': 'Kavitha M',
        'role': 'student',
        'department': 'Information Technology',
        'year_of_study': 2,
        'semester': 3,
        'preferred_language': 'ta'
    }
    res = client.post('/api/auth/register', json=payload)
    assert res.status_code == 201
    data = res.get_json()
    assert data['success'] is True
    assert 'access_token' in data
    assert data['user']['email'] == 'new_student@college.edu'
    assert data['user']['role'] == 'student'

def test_registration_validation_failures(client):
    # Invalid email
    res1 = client.post('/api/auth/register', json={'email': 'not-an-email', 'password': '12345678', 'full_name': 'Name'})
    assert res1.status_code == 400

    # Too short password
    res2 = client.post('/api/auth/register', json={'email': 'valid@college.edu', 'password': '123', 'full_name': 'Name'})
    assert res2.status_code == 400

    # Missing full name
    res3 = client.post('/api/auth/register', json={'email': 'valid@college.edu', 'password': 'Password@123', 'full_name': ''})
    assert res3.status_code == 400

def test_duplicate_registration_conflict(client):
    payload = {
        'email': 'student_test@college.edu', # Already seeded in conftest
        'password': 'SomePassword123',
        'full_name': 'Duplicate User'
    }
    res = client.post('/api/auth/register', json=payload)
    assert res.status_code == 409
    assert res.get_json()['success'] is False

def test_login_success(client):
    payload = {
        'email': 'student_test@college.edu',
        'password': 'StudentPass@123'
    }
    res = client.post('/api/auth/login', json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert 'access_token' in data

def test_login_invalid_password(client):
    payload = {
        'email': 'student_test@college.edu',
        'password': 'WrongPassword!'
    }
    res = client.post('/api/auth/login', json=payload)
    assert res.status_code == 401
    assert res.get_json()['success'] is False

def test_role_permissions_admin_required(client, student_headers, admin_headers):
    # Student attempting to access admin-only endpoint: /api/admin/users
    res_student = client.get('/api/admin/users', headers=student_headers)
    assert res_student.status_code == 403
    assert res_student.get_json()['success'] is False

    # Admin accessing the same endpoint
    res_admin = client.get('/api/admin/users', headers=admin_headers)
    assert res_admin.status_code == 200
    assert res_admin.get_json()['success'] is True
    assert len(res_admin.get_json()['users']) >= 2
