from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import db
from models import (
    User, UserProfile, Subject, UnansweredQuestion,
    ChatbotFeedback, NotificationDeliveryRecord, AcademicDocument,
    DocumentChunk, Examination, Assignment, Notification
)
from services.auth_service import admin_required

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/stats', methods=['GET'])
@jwt_required()
@admin_required()
def get_admin_overview():
    """Retrieve system overview metrics for the administrator."""
    total_students = User.query.filter_by(role='student').count()
    total_admins = User.query.filter_by(role='admin').count()
    total_docs = AcademicDocument.query.count()
    total_chunks = DocumentChunk.query.count()
    total_exams = Examination.query.count()
    total_assignments = Assignment.query.count()
    unanswered_count = UnansweredQuestion.query.filter_by(status='pending_review').count()
    total_deliveries = NotificationDeliveryRecord.query.count()

    return jsonify({
        'success': True,
        'stats': {
            'total_students': total_students,
            'total_admins': total_admins,
            'total_documents': total_docs,
            'total_indexed_chunks': total_chunks,
            'total_examinations': total_exams,
            'total_assignments': total_assignments,
            'pending_unanswered_questions': unanswered_count,
            'total_smart_alerts_delivered': total_deliveries
        }
    }), 200

# ----------------- User Management -----------------
@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@admin_required()
def list_users():
    """List all user accounts."""
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify({
        'success': True,
        'users': [u.to_dict() for u in users]
    }), 200

@admin_bp.route('/users/<int:target_user_id>/role', methods=['PUT'])
@jwt_required()
@admin_required()
def update_user_role(target_user_id):
    """Promote or demote a user role."""
    data = request.get_json() or {}
    new_role = data.get('role', 'student').lower()

    if new_role not in ['student', 'admin']:
        return jsonify({'success': False, 'message': 'Role must be student or admin.'}), 400

    user = User.query.get(target_user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found.'}), 404

    user.role = new_role
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Role updated to {new_role}.',
        'user': user.to_dict()
    }), 200

@admin_bp.route('/users/<int:target_user_id>/status', methods=['PUT'])
@jwt_required()
@admin_required()
def toggle_user_status(target_user_id):
    """Activate or deactivate user account."""
    user = User.query.get(target_user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found.'}), 404

    user.is_active = not user.is_active
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'User account is now {"active" if user.is_active else "inactive"}.',
        'user': user.to_dict()
    }), 200

# ----------------- Subject Management -----------------
@admin_bp.route('/subjects', methods=['GET'])
@jwt_required()
def list_subjects():
    """List all academic subjects."""
    subjects = Subject.query.order_by(Subject.code.asc()).all()
    return jsonify({
        'success': True,
        'subjects': [s.to_dict() for s in subjects]
    }), 200

@admin_bp.route('/subjects', methods=['POST'])
@jwt_required()
@admin_required()
def create_subject():
    """Admin adds a new subject to course catalog."""
    data = request.get_json() or {}
    code = data.get('code', '').strip().upper()
    name = data.get('name', '').strip()
    dept = data.get('department', 'Computer Science and Engineering')
    sem = int(data.get('semester', 5))
    credits = int(data.get('credits', 3))
    faculty = data.get('faculty_name', '')

    if not code or not name:
        return jsonify({'success': False, 'message': 'Subject code and name are required.'}), 400

    if Subject.query.filter_by(code=code).first():
        return jsonify({'success': False, 'message': f'Subject with code {code} already exists.'}), 409

    subject = Subject(
        code=code,
        name=name,
        department=dept,
        semester=sem,
        credits=credits,
        faculty_name=faculty
    )
    db.session.add(subject)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Subject added successfully.',
        'subject': subject.to_dict()
    }), 201

@admin_bp.route('/subjects/<int:sub_id>', methods=['DELETE'])
@jwt_required()
@admin_required()
def delete_subject(sub_id):
    """Admin deletes a subject."""
    subject = Subject.query.get(sub_id)
    if not subject:
        return jsonify({'success': False, 'message': 'Subject not found.'}), 404

    db.session.delete(subject)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Subject deleted successfully.'
    }), 200

# ----------------- Unanswered Queries & Feedback -----------------
@admin_bp.route('/unanswered', methods=['GET'])
@jwt_required()
@admin_required()
def list_unanswered_questions():
    """Admin reviews chatbot queries where official documents had no answers."""
    questions = UnansweredQuestion.query.order_by(UnansweredQuestion.created_at.desc()).all()
    return jsonify({
        'success': True,
        'questions': [q.to_dict() for q in questions]
    }), 200

@admin_bp.route('/unanswered/<int:q_id>/reply', methods=['POST'])
@jwt_required()
@admin_required()
def reply_to_unanswered(q_id):
    """Admin writes an official reply to an unanswered question and notifies student."""
    q = UnansweredQuestion.query.get(q_id)
    if not q:
        return jsonify({'success': False, 'message': 'Question not found.'}), 404

    data = request.get_json() or {}
    reply = data.get('reply', '').strip()
    if not reply:
        return jsonify({'success': False, 'message': 'Reply content cannot be empty.'}), 400

    q.admin_reply = reply
    q.status = 'resolved'

    # Notify student
    notif = Notification(
        user_id=q.user_id,
        title="Official Reply to Your Academic Query",
        message=f"Regarding your question '{q.question[:60]}...': {reply}",
        notification_type="system",
        priority="medium",
        action_link="/chat"
    )
    db.session.add(notif)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Official reply recorded and student notified.',
        'question': q.to_dict()
    }), 200

@admin_bp.route('/feedback', methods=['GET'])
@jwt_required()
@admin_required()
def list_chatbot_feedback():
    """Admin reviews student ratings and comments on chatbot answers."""
    feedbacks = ChatbotFeedback.query.order_by(ChatbotFeedback.created_at.desc()).all()
    return jsonify({
        'success': True,
        'feedbacks': [f.to_dict() for f in feedbacks]
    }), 200

# ----------------- Smart Alert Delivery Log -----------------
@admin_bp.route('/delivery-logs', methods=['GET'])
@jwt_required()
@admin_required()
def list_delivery_logs():
    """Admin inspects smart academic alert delivery records (deduplication verification)."""
    logs = NotificationDeliveryRecord.query.order_by(NotificationDeliveryRecord.delivered_at.desc()).limit(100).all()
    return jsonify({
        'success': True,
        'total_logged': len(logs),
        'logs': [
            {
                'id': l.id,
                'dedup_key': l.dedup_key,
                'user_id': l.user_id,
                'entity_type': l.entity_type,
                'entity_id': l.entity_id,
                'days_before': l.days_before,
                'delivered_at': l.delivered_at.isoformat(),
                'status': l.status
            }
            for l in logs
        ]
    }), 200
