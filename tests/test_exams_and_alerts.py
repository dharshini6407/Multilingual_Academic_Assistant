import pytest
from datetime import datetime, date, timedelta
import pytz
from services.scheduler_service import (
    calculate_exam_countdown, get_kolkata_now,
    check_and_deliver_academic_alerts
)
from models import Examination, Notification, NotificationDeliveryRecord, Subject, User
from db import db

def test_exam_countdown_messages():
    today = date(2026, 11, 10)

    # Exam in 5 days
    cd5 = calculate_exam_countdown(date(2026, 11, 15), current_date=today)
    assert cd5['days_remaining'] == 5
    assert cd5['countdown_message'] == "Exam in 5 days"

    # Exam tomorrow
    cd1 = calculate_exam_countdown(date(2026, 11, 11), current_date=today)
    assert cd1['days_remaining'] == 1
    assert cd1['countdown_message'] == "Exam tomorrow"

    # Exam Day!
    cd0 = calculate_exam_countdown(date(2026, 11, 10), current_date=today)
    assert cd0['days_remaining'] == 0
    assert cd0['countdown_message'] == "Exam Day!"

    # Exam completed
    cd_past = calculate_exam_countdown(date(2026, 11, 8), current_date=today)
    assert cd_past['days_remaining'] == -2
    assert cd_past['countdown_message'] == "Exam Completed"

def test_exact_exam_day_notification_and_deduplication(app):
    with app.app_context():
        today_kolkata = get_kolkata_now().date()
        sub = Subject.query.first()
        admin = User.query.filter_by(role='admin').first()
        student = User.query.filter_by(role='student').first()

        # Schedule exam on Exam Day (today)
        exam_today = Examination(
            subject_id=sub.id,
            title='Realtime Operating Systems Exam',
            exam_type='Semester End Exam',
            exam_date=today_kolkata,
            start_time='10:00:00',
            end_time='13:00:00',
            hall_number='Exam Hall 101',
            status='scheduled',
            created_by=admin.id
        )
        db.session.add(exam_today)
        db.session.commit()

        # Run alert delivery
        check_and_deliver_academic_alerts(app)

        # Check delivered notification
        notif = Notification.query.filter_by(user_id=student.id, notification_type='exam').first()
        assert notif is not None

        # Verify exact required exam-day Title and Message
        assert notif.title == "All the Best for Your Exam! 🎓"
        assert notif.message == "Your examination is today. Stay calm, read every question carefully, manage your time, and give your best. Good luck! 💙"

        # Verify deduplication record exists
        dedup_key = f"exam_{exam_today.id}_user_{student.id}_day_0"
        delivery_rec = NotificationDeliveryRecord.query.filter_by(dedup_key=dedup_key).first()
        assert delivery_rec is not None
        assert delivery_rec.status == "delivered"

        # Count total notifications
        initial_count = Notification.query.filter_by(user_id=student.id).count()

        # Re-run alert delivery (simulating hourly scheduler or server restart)
        check_and_deliver_academic_alerts(app)

        # Verify NO duplicate notification was created
        final_count = Notification.query.filter_by(user_id=student.id).count()
        assert final_count == initial_count, "Duplicate notification was created!"

def test_exam_rescheduling_and_cancellation(client, admin_headers, app):
    with app.app_context():
        sub = Subject.query.first()
        student = User.query.filter_by(role='student').first()
        today = get_kolkata_now().date()

        # Create exam
        create_res = client.post('/api/exams', json={
            'subject_id': sub.id,
            'title': 'Computer Networks Exam',
            'exam_date': (today + timedelta(days=10)).strftime('%Y-%m-%d'),
            'exam_type': 'Semester End Exam'
        }, headers=admin_headers)
        assert create_res.status_code == 201
        exam_id = create_res.get_json()['examination']['id']

        # 1. Reschedule exam
        resched_date = (today + timedelta(days=15)).strftime('%Y-%m-%d')
        res_resched = client.put(f'/api/exams/{exam_id}', json={
            'exam_date': resched_date
        }, headers=admin_headers)
        assert res_resched.status_code == 200
        assert res_resched.get_json()['examination']['status'] == 'rescheduled'

        # Verify reschedule notification dispatched
        notif_resched = Notification.query.filter_by(user_id=student.id).filter(
            Notification.title.like('%RESCHEDULED%')
        ).first()
        assert notif_resched is not None

        # 2. Cancel exam
        res_cancel = client.post(f'/api/exams/{exam_id}/cancel', headers=admin_headers)
        assert res_cancel.status_code == 200
        assert res_cancel.get_json()['examination']['status'] == 'cancelled'

        # Verify cancellation notification dispatched
        notif_cancel = Notification.query.filter_by(user_id=student.id).filter(
            Notification.title.like('%CANCELLED%')
        ).first()
        assert notif_cancel is not None
        assert notif_cancel.priority == 'urgent'
