import pytest
from datetime import datetime, timedelta
from models import User, Notification, StudyPlan, StudyTask
from services.auth_service import hash_password, generate_user_token
from db import db

def test_notification_ownership(app, client, student_headers):
    with app.app_context():
        # Create a second student
        student2 = User(
            email='student2@college.edu',
            password_hash=hash_password('Password@123'),
            role='student',
            is_active=True
        )
        db.session.add(student2)
        db.session.flush()

        # Notification belonging to student2
        notif2 = Notification(
            user_id=student2.id,
            title='Confidential Alert for Student 2',
            message='Personal Message',
            notification_type='system'
        )
        db.session.add(notif2)
        db.session.commit()
        notif2_id = notif2.id

    # Student 1 attempting to mark Student 2's notification as read
    res_read = client.put(f'/api/notifications/{notif2_id}/read', headers=student_headers)
    assert res_read.status_code == 404
    assert res_read.get_json()['success'] is False

    # Student 1 attempting to delete Student 2's notification
    res_del = client.delete(f'/api/notifications/{notif2_id}', headers=student_headers)
    assert res_del.status_code == 404
    assert res_del.get_json()['success'] is False

def test_study_task_ownership(app, client, student_headers):
    with app.app_context():
        student2 = User.query.filter_by(email='student2@college.edu').first()
        if not student2:
            student2 = User(
                email='student2@college.edu',
                password_hash=hash_password('Password@123'),
                role='student',
                is_active=True
            )
            db.session.add(student2)
            db.session.flush()

        plan2 = StudyPlan(
            user_id=student2.id,
            title='Student 2 Plan',
            start_date=datetime.utcnow().date(),
            end_date=(datetime.utcnow() + timedelta(days=5)).date()
        )
        db.session.add(plan2)
        db.session.flush()

        task2 = StudyTask(
            plan_id=plan2.id,
            user_id=student2.id,
            title='Student 2 Private Task',
            scheduled_date=datetime.utcnow().date()
        )
        db.session.add(task2)
        db.session.commit()
        task2_id = task2.id

    # Student 1 attempting to update Student 2's task
    res_update = client.put(f'/api/planner/tasks/{task2_id}', json={'is_completed': True}, headers=student_headers)
    assert res_update.status_code == 404
    assert res_update.get_json()['success'] is False

    # Student 1 attempting to delete Student 2's task
    res_del = client.delete(f'/api/planner/tasks/{task2_id}', headers=student_headers)
    assert res_del.status_code == 404
    assert res_del.get_json()['success'] is False

def test_invalid_attendance_inputs(client, student_headers):
    # Attended > Conducted
    res1 = client.post('/api/attendance/record', json={
        'subject_id': 1,
        'conducted_classes': 10,
        'attended_classes': 15
    }, headers=student_headers)
    assert res1.status_code == 400
    assert 'cannot exceed' in res1.get_json()['message']

    # Negative conducted count
    res2 = client.post('/api/attendance/record', json={
        'subject_id': 1,
        'conducted_classes': -5,
        'attended_classes': 0
    }, headers=student_headers)
    assert res2.status_code == 400
    assert 'cannot be negative' in res2.get_json()['message']
