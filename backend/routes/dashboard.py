from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from db import db
from models import (
    User, AttendanceRecord, Examination, Assignment,
    StudentAssignmentStatus, AcademicActivity, StudyPlan, Notification
)
from services.scheduler_service import calculate_exam_countdown, get_kolkata_now

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/summary', methods=['GET'])
@jwt_required()
def get_dashboard_summary():
    """
    Retrieve real-time consolidated academic metrics from MySQL:
    - Overall attendance percentage (total attended / total conducted * 100)
    - Upcoming exams with Asia/Kolkata countdown
    - Pending assignments
    - Upcoming academic activities
    - Active study plan progress
    - Recent unread notifications
    - Quick links
    """
    user_id = int(get_jwt_identity())
    current_date = get_kolkata_now().date()
    current_time = get_kolkata_now()

    # 1. Real Attendance Aggregation
    att_records = AttendanceRecord.query.filter_by(user_id=user_id).all()
    total_conducted = sum(r.conducted_classes for r in att_records)
    total_attended = sum(r.attended_classes for r in att_records)

    if total_conducted > 0:
        overall_attendance_pct = round((total_attended / total_conducted) * 100.0, 1)
    else:
        overall_attendance_pct = 100.0 if not att_records else 0.0

    # 2. Upcoming Examinations
    exams = Examination.query.filter(
        Examination.status.in_(['scheduled', 'rescheduled']),
        Examination.exam_date >= current_date
    ).order_by(Examination.exam_date.asc()).limit(5).all()

    upcoming_exams_data = []
    for ex in exams:
        countdown = calculate_exam_countdown(ex.exam_date, current_date)
        ex_dict = ex.to_dict()
        ex_dict['countdown'] = countdown
        upcoming_exams_data.append(ex_dict)

    # 3. Pending Assignments
    all_active_assignments = Assignment.query.filter_by(status='active').order_by(Assignment.deadline.asc()).all()
    pending_assignments_data = []

    for a in all_active_assignments:
        status_rec = StudentAssignmentStatus.query.filter_by(user_id=user_id, assignment_id=a.id).first()
        is_completed = status_rec and status_rec.status in ['submitted', 'completed']
        if not is_completed:
            a_dict = a.to_dict()
            a_dict['student_status'] = status_rec.status if status_rec else 'pending'
            deadline_dt = a.deadline if isinstance(a.deadline, datetime) else datetime.combine(a.deadline, datetime.min.time())
            a_dict['is_overdue'] = deadline_dt < current_time.replace(tzinfo=None)
            pending_assignments_data.append(a_dict)

    # 4. Upcoming Academic Activities
    activities = AcademicActivity.query.filter(
        AcademicActivity.status.in_(['scheduled', 'rescheduled']),
        AcademicActivity.activity_date >= current_time.replace(tzinfo=None)
    ).order_by(AcademicActivity.activity_date.asc()).limit(4).all()

    # 5. Study Plan Progress
    latest_plan = StudyPlan.query.filter_by(user_id=user_id).order_by(StudyPlan.created_at.desc()).first()
    plan_progress = {
        'plan_id': latest_plan.id if latest_plan else None,
        'title': latest_plan.title if latest_plan else 'No active study plan',
        'completion_percentage': latest_plan.completion_percentage if latest_plan else 0.0,
        'has_active_plan': latest_plan is not None
    }

    # 6. Recent Notifications
    recent_notifications = Notification.query.filter_by(user_id=user_id).order_by(
        Notification.created_at.desc()
    ).limit(6).all()
    unread_count = Notification.query.filter_by(user_id=user_id, is_read=False).count()

    # 7. Quick Navigation Links
    quick_links = [
        {'title': 'Academic Chatbot', 'path': '/chat', 'icon': 'MessageSquare', 'badge': 'AI RAG'},
        {'title': 'Attendance Tracker', 'path': '/attendance', 'icon': 'Percent', 'badge': f"{overall_attendance_pct}%"},
        {'title': 'Exam Calendar', 'path': '/exams', 'icon': 'Calendar', 'badge': f"{len(upcoming_exams_data)} exams"},
        {'title': 'Assignments', 'path': '/assignments', 'icon': 'FileText', 'badge': f"{len(pending_assignments_data)} pending"},
        {'title': 'Study Planner', 'path': '/planner', 'icon': 'CheckSquare', 'badge': f"{plan_progress['completion_percentage']}%"},
        {'title': 'Focus Timer', 'path': '/timer', 'icon': 'Timer', 'badge': 'Pomodoro'}
    ]

    return jsonify({
        'success': True,
        'timestamp': current_time.isoformat(),
        'metrics': {
            'attendance_percentage': overall_attendance_pct,
            'total_conducted_classes': total_conducted,
            'total_attended_classes': total_attended,
            'subjects_tracked_count': len(att_records),
            'upcoming_exams_count': len(upcoming_exams_data),
            'pending_assignments_count': len(pending_assignments_data),
            'upcoming_activities_count': len(activities),
            'unread_notifications_count': unread_count
        },
        'upcoming_exams': upcoming_exams_data,
        'pending_assignments': pending_assignments_data[:5],
        'upcoming_activities': [act.to_dict() for act in activities],
        'study_plan': plan_progress,
        'recent_notifications': [n.to_dict() for n in recent_notifications],
        'quick_links': quick_links
    }), 200
