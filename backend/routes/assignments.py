from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import db
from models import Assignment, StudentAssignmentStatus, Subject, User
from services.auth_service import admin_required
from services.scheduler_service import get_kolkata_now

assignments_bp = Blueprint('assignments', __name__)

@assignments_bp.route('', methods=['GET'])
@jwt_required()
def get_assignments():
    """List assignments with personalized student tracking status."""
    user_id = int(get_jwt_identity())
    current_time = get_kolkata_now().replace(tzinfo=None)

    assignments = Assignment.query.order_by(Assignment.deadline.asc()).all()
    results = []

    for a in assignments:
        a_dict = a.to_dict()
        student_status_rec = StudentAssignmentStatus.query.filter_by(
            user_id=user_id, assignment_id=a.id
        ).first()

        a_dict['student_status'] = student_status_rec.status if student_status_rec else 'pending'
        a_dict['submitted_at'] = student_status_rec.submitted_at.isoformat() if student_status_rec and student_status_rec.submitted_at else None
        a_dict['student_notes'] = student_status_rec.student_notes if student_status_rec else ''

        deadline_dt = a.deadline if isinstance(a.deadline, datetime) else datetime.combine(a.deadline, datetime.min.time())
        a_dict['is_overdue'] = deadline_dt < current_time and a_dict['student_status'] not in ['submitted', 'completed']
        results.append(a_dict)

    return jsonify({
        'success': True,
        'assignments': results
    }), 200

@assignments_bp.route('', methods=['POST'])
@jwt_required()
@admin_required()
def create_assignment():
    """Admin creates a new assignment."""
    data = request.get_json() or {}
    user_id = int(get_jwt_identity())

    subject_id = data.get('subject_id')
    title = data.get('title', '').strip()
    description = data.get('description', '')
    deadline_str = data.get('deadline')
    priority = data.get('priority', 'medium').lower()
    max_score = int(data.get('max_score', 20))

    if not subject_id or not title or not deadline_str:
        return jsonify({'success': False, 'message': 'Subject, title, and deadline are required.'}), 400

    try:
        deadline = datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))
    except Exception:
        try:
            deadline = datetime.strptime(deadline_str, '%Y-%m-%d %H:%M:%S')
        except Exception:
            try:
                deadline = datetime.strptime(deadline_str, '%Y-%m-%d')
            except Exception:
                return jsonify({'success': False, 'message': 'Invalid deadline format. Use ISO format or YYYY-MM-DD.'}), 400

    if priority not in ['low', 'medium', 'high']:
        priority = 'medium'

    assignment = Assignment(
        subject_id=subject_id,
        title=title,
        description=description,
        deadline=deadline,
        priority=priority,
        max_score=max_score,
        status='active',
        created_by=user_id
    )
    db.session.add(assignment)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Assignment created successfully.',
        'assignment': assignment.to_dict()
    }), 201

@assignments_bp.route('/<int:assignment_id>', methods=['PUT'])
@jwt_required()
@admin_required()
def update_assignment(assignment_id):
    """Admin updates assignment details."""
    assignment = Assignment.query.get(assignment_id)
    if not assignment:
        return jsonify({'success': False, 'message': 'Assignment not found.'}), 404

    data = request.get_json() or {}
    if 'title' in data and data['title'].strip():
        assignment.title = data['title'].strip()
    if 'description' in data:
        assignment.description = data['description']
    if 'priority' in data and data['priority'] in ['low', 'medium', 'high']:
        assignment.priority = data['priority']
    if 'max_score' in data:
        assignment.max_score = int(data['max_score'])
    if 'status' in data and data['status'] in ['active', 'completed', 'cancelled']:
        assignment.status = data['status']
    if 'deadline' in data and data['deadline']:
        try:
            assignment.deadline = datetime.fromisoformat(data['deadline'].replace('Z', '+00:00'))
        except Exception:
            pass

    db.session.commit()
    return jsonify({
        'success': True,
        'message': 'Assignment updated successfully.',
        'assignment': assignment.to_dict()
    }), 200

@assignments_bp.route('/<int:assignment_id>/status', methods=['POST'])
@jwt_required()
def update_student_assignment_status(assignment_id):
    """Student updates their personal assignment submission/progress status."""
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    status = data.get('status', 'in_progress').lower()
    notes = data.get('notes', '')

    if status not in ['pending', 'in_progress', 'submitted', 'completed']:
        return jsonify({'success': False, 'message': 'Invalid status.'}), 400

    rec = StudentAssignmentStatus.query.filter_by(user_id=user_id, assignment_id=assignment_id).first()
    if not rec:
        rec = StudentAssignmentStatus(
            user_id=user_id,
            assignment_id=assignment_id,
            status=status,
            student_notes=notes,
            submitted_at=datetime.utcnow() if status in ['submitted', 'completed'] else None
        )
        db.session.add(rec)
    else:
        rec.status = status
        rec.student_notes = notes
        if status in ['submitted', 'completed'] and not rec.submitted_at:
            rec.submitted_at = datetime.utcnow()

    db.session.commit()
    return jsonify({
        'success': True,
        'message': f'Assignment status updated to {status}.',
        'status': rec.to_dict()
    }), 200

@assignments_bp.route('/<int:assignment_id>', methods=['DELETE'])
@jwt_required()
@admin_required()
def delete_assignment(assignment_id):
    """Admin deletes an assignment."""
    assignment = Assignment.query.get(assignment_id)
    if not assignment:
        return jsonify({'success': False, 'message': 'Assignment not found.'}), 404

    db.session.delete(assignment)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Assignment deleted successfully.'}), 200
