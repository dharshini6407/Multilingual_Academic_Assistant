from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import db
from models import FocusSession, Subject, StudyTask
from services.scheduler_service import get_kolkata_now

timer_bp = Blueprint('timer', __name__)

@timer_bp.route('/sessions', methods=['POST'])
@jwt_required()
def record_focus_session():
    """
    Persist completed focus study session in MySQL.
    Ensures paused time is excluded: actual_focused_seconds tracks true active focus.
    """
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}

    subject_id = data.get('subject_id')
    task_id = data.get('task_id')
    duration_minutes = int(data.get('duration_minutes', 25))
    break_minutes = int(data.get('break_minutes', 5))
    actual_focused_seconds = int(data.get('actual_focused_seconds', duration_minutes * 60))
    session_status = data.get('session_status', 'completed')
    notes = data.get('notes', '')

    started_at_str = data.get('started_at')
    ended_at_str = data.get('ended_at')

    now = datetime.utcnow()
    started_at = datetime.fromisoformat(started_at_str.replace('Z', '+00:00')) if started_at_str else (now - timedelta(seconds=actual_focused_seconds))
    ended_at = datetime.fromisoformat(ended_at_str.replace('Z', '+00:00')) if ended_at_str else now

    session = FocusSession(
        user_id=user_id,
        subject_id=subject_id,
        task_id=task_id,
        duration_minutes=duration_minutes,
        break_minutes=break_minutes,
        actual_focused_seconds=actual_focused_seconds,
        session_status=session_status,
        started_at=started_at,
        ended_at=ended_at,
        notes=notes
    )
    db.session.add(session)

    # If linked to a study task, increment actual_minutes
    if task_id:
        task = StudyTask.query.filter_by(id=task_id, user_id=user_id).first()
        if task:
            task.actual_minutes += int(actual_focused_seconds / 60)

    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Focus session recorded successfully.',
        'session': session.to_dict()
    }), 201

@timer_bp.route('/history', methods=['GET'])
@jwt_required()
def get_focus_history():
    """Retrieve focus sessions history and total study stats."""
    user_id = int(get_jwt_identity())
    today_date = get_kolkata_now().date()

    sessions = FocusSession.query.filter_by(user_id=user_id).order_by(
        FocusSession.started_at.desc()
    ).all()

    total_seconds = sum(s.actual_focused_seconds for s in sessions)
    total_minutes = round(total_seconds / 60.0, 1)

    today_sessions = [s for s in sessions if s.started_at.date() == today_date]
    today_seconds = sum(s.actual_focused_seconds for s in today_sessions)
    today_minutes = round(today_seconds / 60.0, 1)

    # Subject-wise focus breakdown
    subject_stats = {}
    for s in sessions:
        sub_name = s.subject.name if s.subject else 'General Study'
        subject_stats[sub_name] = subject_stats.get(sub_name, 0) + round(s.actual_focused_seconds / 60.0, 1)

    return jsonify({
        'success': True,
        'stats': {
            'total_focused_minutes': total_minutes,
            'total_focused_hours': round(total_minutes / 60.0, 1),
            'total_sessions_count': len(sessions),
            'today_focused_minutes': today_minutes,
            'today_sessions_count': len(today_sessions),
            'subject_breakdown': subject_stats
        },
        'sessions': [s.to_dict() for s in sessions[:30]]
    }), 200
