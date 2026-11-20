import logging
from datetime import datetime
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from config import Config
from db import db
from models import (
    User, Examination, Assignment, Notification,
    NotificationDeliveryRecord, NotificationPreference
)

logger = logging.getLogger(__name__)

# Singleton scheduler instance
_scheduler = None
_is_scheduler_running = False

def get_kolkata_now():
    """Return current localized datetime in Asia/Kolkata timezone."""
    tz = pytz.timezone(Config.TIMEZONE_STR)
    return datetime.now(tz)

def calculate_exam_countdown(exam_date, current_date=None):
    """
    Calculate calendar days countdown in Asia/Kolkata timezone and return display message:
    - 'Exam in N days' (N > 1)
    - 'Exam tomorrow' (N == 1)
    - 'Exam Day!' (N == 0)
    - 'Exam Completed' (N < 0)
    """
    if current_date is None:
        current_date = get_kolkata_now().date()
    
    if isinstance(exam_date, str):
        exam_date = datetime.strptime(exam_date, '%Y-%m-%d').date()
    elif isinstance(exam_date, datetime):
        exam_date = exam_date.date()

    days_diff = (exam_date - current_date).days

    if days_diff > 1:
        message = f"Exam in {days_diff} days"
        status_key = "upcoming"
    elif days_diff == 1:
        message = "Exam tomorrow"
        status_key = "tomorrow"
    elif days_diff == 0:
        message = "Exam Day!"
        status_key = "today"
    else:
        message = "Exam Completed"
        status_key = "completed"

    return {
        'days_remaining': days_diff,
        'countdown_message': message,
        'status_key': status_key
    }

def check_and_deliver_academic_alerts(app):
    """
    Scans examinations and assignments, delivers persistent in-app notifications:
    - Exams: 7 days, 3 days, 1 day, and 0 days (Exam Day) before
    - Exact exam-day title and message:
      Title: 'All the Best for Your Exam! 🎓'
      Message: 'Your examination is today. Stay calm, read every question carefully, manage your time, and give your best. Good luck! 💙'
    - Prevents duplicates via unique dedup_key in NotificationDeliveryRecord
    - Recovers missed reminders seamlessly after restart
    """
    with app.app_context():
        try:
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            if not inspector.has_table("examinations"):
                return

            current_kolkata = get_kolkata_now()
            current_date = current_kolkata.date()
            
            # 1. Process Examinations
            active_exams = Examination.query.filter(
                Examination.status.in_(['scheduled', 'rescheduled'])
            ).all()

            # Active students who have exam alerts enabled
            students = User.query.filter_by(role='student', is_active=True).all()

            for exam in active_exams:
                exam_date = exam.exam_date
                days_diff = (exam_date - current_date).days

                # Target alert days: 7, 3, 1, 0
                if days_diff in [7, 3, 1, 0]:
                    subject_name = exam.subject.name if exam.subject else "Academic Subject"
                    subject_code = exam.subject.code if exam.subject else "EXAM"

                    for student in students:
                        # Check user notification preference
                        pref = NotificationPreference.query.filter_by(user_id=student.id).first()
                        if pref and not pref.exam_alerts:
                            continue

                        dedup_key = f"exam_{exam.id}_user_{student.id}_day_{days_diff}"
                        existing_delivery = NotificationDeliveryRecord.query.filter_by(dedup_key=dedup_key).first()

                        if not existing_delivery:
                            # Construct Title and Message
                            if days_diff == 0:
                                title = "All the Best for Your Exam! 🎓"
                                message = "Your examination is today. Stay calm, read every question carefully, manage your time, and give your best. Good luck! 💙"
                                priority = "urgent"
                            elif days_diff == 1:
                                title = f"Final Exam Alert: {subject_name} is Tomorrow!"
                                message = f"Your {exam.exam_type} for {subject_name} ({subject_code}) is tomorrow, {exam_date.strftime('%d %b %Y')} at {exam.start_time} in {exam.hall_number}. Ensure your hall ticket and ID are ready."
                                priority = "high"
                            elif days_diff == 3:
                                title = f"Exam Reminder: 3 Days Left for {subject_code}"
                                message = f"Only 3 days left until your {exam.exam_type} for {subject_name} on {exam_date.strftime('%d %b %Y')}. Review previous year questions and syllabus notes."
                                priority = "medium"
                            elif days_diff == 7:
                                title = f"Upcoming Exam Alert: {subject_name} ({subject_code}) - 7 Days Left"
                                message = f"Your {exam.exam_type} for {subject_name} ({subject_code}) is scheduled in 7 days on {exam_date.strftime('%d %b %Y')} from {exam.start_time} to {exam.end_time} in {exam.hall_number}."
                                priority = "medium"

                            # Save Notification
                            notif = Notification(
                                user_id=student.id,
                                title=title,
                                message=message,
                                notification_type="exam",
                                priority=priority,
                                is_read=False,
                                action_link="/exams"
                            )
                            db.session.add(notif)
                            db.session.flush()

                            # Save Delivery Record for deduplication & restart recovery
                            delivery = NotificationDeliveryRecord(
                                dedup_key=dedup_key,
                                user_id=student.id,
                                notification_id=notif.id,
                                entity_type="exam",
                                entity_id=exam.id,
                                days_before=days_diff,
                                status="delivered"
                            )
                            db.session.add(delivery)

            # 2. Process Assignments
            active_assignments = Assignment.query.filter_by(status='active').all()
            for assign in active_assignments:
                deadline_date = assign.deadline.date() if isinstance(assign.deadline, datetime) else assign.deadline
                days_diff = (deadline_date - current_date).days

                # Notify 1 day before and on due date
                if days_diff in [1, 0]:
                    subject_name = assign.subject.name if assign.subject else "Course"
                    for student in students:
                        pref = NotificationPreference.query.filter_by(user_id=student.id).first()
                        if pref and not pref.assignment_alerts:
                            continue

                        dedup_key = f"assignment_{assign.id}_user_{student.id}_day_{days_diff}"
                        if not NotificationDeliveryRecord.query.filter_by(dedup_key=dedup_key).first():
                            if days_diff == 0:
                                title = f"Assignment Due Today: {assign.title}!"
                                msg = f"Your assignment '{assign.title}' for {subject_name} is due today! Ensure submission before deadline."
                                prio = "urgent"
                            else:
                                title = f"Assignment Due Tomorrow: {assign.title}"
                                msg = f"Reminder: '{assign.title}' for {subject_name} is due tomorrow ({deadline_date.strftime('%d %b %Y')})."
                                prio = "high"

                            notif = Notification(
                                user_id=student.id,
                                title=title,
                                message=msg,
                                notification_type="assignment",
                                priority=prio,
                                is_read=False,
                                action_link="/assignments"
                            )
                            db.session.add(notif)
                            db.session.flush()

                            delivery = NotificationDeliveryRecord(
                                dedup_key=dedup_key,
                                user_id=student.id,
                                notification_id=notif.id,
                                entity_type="assignment",
                                entity_id=assign.id,
                                days_before=days_diff,
                                status="delivered"
                            )
                            db.session.add(delivery)

            db.session.commit()
            logger.info("Academic alerts scan completed successfully.")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error during academic alerts delivery: {e}")

def notify_exam_status_change(app, exam_id, previous_status, new_status, new_date=None):
    """Notify students when an examination is rescheduled or cancelled."""
    with app.app_context():
        try:
            exam = db.session.get(Examination, exam_id)
            if not exam:
                return

            students = User.query.filter_by(role='student', is_active=True).all()
            subject_name = exam.subject.name if exam.subject else "Exam"
            subject_code = exam.subject.code if exam.subject else ""

            if new_status == 'cancelled':
                title = f"CANCELLED: {subject_code} {exam.exam_type}"
                msg = f"The {exam.exam_type} for {subject_name} ({subject_code}) originally set for {exam.exam_date} has been CANCELLED by the administration."
                priority = 'urgent'
            elif new_status == 'rescheduled':
                title = f"RESCHEDULED: {subject_code} {exam.exam_type}"
                msg = f"The {exam.exam_type} for {subject_name} ({subject_code}) has been RESCHEDULED to {exam.exam_date.strftime('%d %b %Y')} from {exam.start_time} to {exam.end_time} in {exam.hall_number}."
                priority = 'high'
            else:
                return

            for student in students:
                notif = Notification(
                    user_id=student.id,
                    title=title,
                    message=msg,
                    notification_type="exam",
                    priority=priority,
                    action_link="/exams"
                )
                db.session.add(notif)
            
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error notifying exam status change: {e}")

def init_scheduler(app):
    """
    Initialize APScheduler singleton with Asia/Kolkata timezone.
    Guarantees no duplicate schedulers.
    Runs an immediate alert scan on startup for restart recovery,
    then schedules recurring checks every hour.
    """
    global _scheduler, _is_scheduler_running
    if _is_scheduler_running and _scheduler is not None:
        logger.info("APScheduler already initialized and active.")
        return _scheduler

    tz = pytz.timezone(Config.TIMEZONE_STR)
    _scheduler = BackgroundScheduler(timezone=tz)

    # 1. Schedule periodic check every hour
    _scheduler.add_job(
        func=check_and_deliver_academic_alerts,
        args=[app],
        trigger='interval',
        hours=1,
        id='academic_alerts_job',
        replace_existing=True
    )

    _scheduler.start()
    _is_scheduler_running = True
    logger.info("APScheduler started successfully with Asia/Kolkata timezone.")

    # 2. Run immediate scan on backend startup for recovery of missed reminders
    check_and_deliver_academic_alerts(app)
    return _scheduler
