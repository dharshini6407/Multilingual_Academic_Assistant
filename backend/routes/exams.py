from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import db
from models import Examination, Subject
from services.auth_service import admin_required
from services.scheduler_service import (
    calculate_exam_countdown, get_kolkata_now, notify_exam_status_change
)

exams_bp = Blueprint('exams', __name__)

@exams_bp.route('', methods=['GET'])
@jwt_required()
def get_examinations():
    """List all examinations with live Asia/Kolkata countdown calculation."""
    current_date = get_kolkata_now().date()
    exams = Examination.query.order_by(Examination.exam_date.asc()).all()

    result = []
    for ex in exams:
        item = ex.to_dict()
        item['countdown'] = calculate_exam_countdown(ex.exam_date, current_date)
        result.append(item)

    return jsonify({
        'success': True,
        'current_date': current_date.strftime('%Y-%m-%d'),
        'timezone': 'Asia/Kolkata',
        'examinations': result
    }), 200

@exams_bp.route('', methods=['POST'])
@jwt_required()
@admin_required()
def create_examination():
    """Admin creates a new examination schedule."""
    data = request.get_json() or {}
    user_id = int(get_jwt_identity())

    subject_id = data.get('subject_id')
    title = data.get('title', '').strip()
    exam_type = data.get('exam_type', 'Semester End Exam')
    exam_date_str = data.get('exam_date')
    start_time = data.get('start_time', '10:00:00')
    end_time = data.get('end_time', '13:00:00')
    hall_number = data.get('hall_number', 'Main Block Hall 302')
    max_marks = int(data.get('max_marks', 100))
    remarks = data.get('remarks')

    if not subject_id or not exam_date_str:
        return jsonify({'success': False, 'message': 'Subject ID and exam date are required.'}), 400

    try:
        exam_date = datetime.strptime(exam_date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid exam date format. Use YYYY-MM-DD.'}), 400

    subject = db.session.get(Subject, subject_id)
    if not subject:
        return jsonify({'success': False, 'message': 'Subject not found.'}), 404

    if not title:
        title = f"{subject.name} ({exam_type})"

    exam = Examination(
        subject_id=subject_id,
        title=title,
        exam_type=exam_type,
        exam_date=exam_date,
        start_time=start_time,
        end_time=end_time,
        hall_number=hall_number,
        max_marks=max_marks,
        status='scheduled',
        remarks=remarks,
        created_by=user_id
    )
    db.session.add(exam)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Examination scheduled successfully.',
        'examination': exam.to_dict()
    }), 201

@exams_bp.route('/<int:exam_id>', methods=['PUT'])
@jwt_required()
@admin_required()
def update_or_reschedule_examination(exam_id):
    """Admin updates or reschedules an examination, notifying enrolled students."""
    exam = db.session.get(Examination, exam_id)
    if not exam:
        return jsonify({'success': False, 'message': 'Examination not found.'}), 404

    data = request.get_json() or {}
    prev_status = exam.status
    prev_date = exam.exam_date

    is_rescheduled = False
    if 'exam_date' in data and data['exam_date']:
        try:
            new_date = datetime.strptime(data['exam_date'], '%Y-%m-%d').date()
            if new_date != prev_date:
                exam.exam_date = new_date
                exam.status = 'rescheduled'
                is_rescheduled = True
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid exam date format. Use YYYY-MM-DD.'}), 400

    if 'start_time' in data:
        exam.start_time = data['start_time']
    if 'end_time' in data:
        exam.end_time = data['end_time']
    if 'hall_number' in data:
        exam.hall_number = data['hall_number']
    if 'max_marks' in data:
        exam.max_marks = int(data['max_marks'])
    if 'remarks' in data:
        exam.remarks = data['remarks']
    if 'status' in data and data['status'] in ['scheduled', 'rescheduled', 'completed', 'cancelled']:
        exam.status = data['status']

    db.session.commit()

    # Trigger alerts if rescheduled
    if is_rescheduled:
        notify_exam_status_change(current_app._get_current_object(), exam.id, prev_status, 'rescheduled')

    return jsonify({
        'success': True,
        'message': 'Examination updated successfully.',
        'examination': exam.to_dict()
    }), 200

@exams_bp.route('/<int:exam_id>/cancel', methods=['POST'])
@jwt_required()
@admin_required()
def cancel_examination(exam_id):
    """Admin cancels an examination and automatically broadcasts urgent alerts."""
    exam = db.session.get(Examination, exam_id)
    if not exam:
        return jsonify({'success': False, 'message': 'Examination not found.'}), 404

    prev_status = exam.status
    exam.status = 'cancelled'
    db.session.commit()

    notify_exam_status_change(current_app._get_current_object(), exam.id, prev_status, 'cancelled')

    return jsonify({
        'success': True,
        'message': f'Examination for {exam.title} has been cancelled.',
        'examination': exam.to_dict()
    }), 200

@exams_bp.route('/<int:exam_id>', methods=['DELETE'])
@jwt_required()
@admin_required()
def delete_examination(exam_id):
    """Admin deletes an examination record."""
    exam = db.session.get(Examination, exam_id)
    if not exam:
        return jsonify({'success': False, 'message': 'Examination not found.'}), 404

    db.session.delete(exam)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Examination deleted successfully.'}), 200
