from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import db
from models import AcademicActivity
from services.auth_service import admin_required

activities_bp = Blueprint('activities', __name__)

@activities_bp.route('', methods=['GET'])
@jwt_required()
def get_activities():
    """List academic activities, workshops, seminars, and hackathons."""
    activities = AcademicActivity.query.order_by(AcademicActivity.activity_date.asc()).all()
    return jsonify({
        'success': True,
        'activities': [act.to_dict() for act in activities]
    }), 200

@activities_bp.route('', methods=['POST'])
@jwt_required()
@admin_required()
def create_activity():
    """Admin creates a new academic activity."""
    data = request.get_json() or {}
    user_id = int(get_jwt_identity())

    title = data.get('title', '').strip()
    activity_type = data.get('activity_type', 'workshop')
    description = data.get('description', '')
    activity_date_str = data.get('activity_date')
    venue = data.get('venue', 'Auditorium / Online')
    organizer = data.get('organizer', 'Department of CSE')
    priority = data.get('priority', 'medium').lower()

    if not title or not activity_date_str:
        return jsonify({'success': False, 'message': 'Title and activity date are required.'}), 400

    try:
        activity_date = datetime.fromisoformat(activity_date_str.replace('Z', '+00:00'))
    except Exception:
        try:
            activity_date = datetime.strptime(activity_date_str, '%Y-%m-%d %H:%M:%S')
        except Exception:
            try:
                activity_date = datetime.strptime(activity_date_str, '%Y-%m-%d')
            except Exception:
                return jsonify({'success': False, 'message': 'Invalid date format.'}), 400

    activity = AcademicActivity(
        title=title,
        activity_type=activity_type,
        description=description,
        activity_date=activity_date,
        venue=venue,
        organizer=organizer,
        priority=priority,
        status='scheduled',
        created_by=user_id
    )
    db.session.add(activity)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Academic activity created successfully.',
        'activity': activity.to_dict()
    }), 201

@activities_bp.route('/<int:activity_id>', methods=['PUT'])
@jwt_required()
@admin_required()
def update_activity(activity_id):
    """Admin updates an activity."""
    activity = AcademicActivity.query.get(activity_id)
    if not activity:
        return jsonify({'success': False, 'message': 'Activity not found.'}), 404

    data = request.get_json() or {}
    for field in ['title', 'activity_type', 'description', 'venue', 'organizer', 'priority', 'status']:
        if field in data and data[field]:
            setattr(activity, field, data[field])

    if 'activity_date' in data and data['activity_date']:
        try:
            activity.activity_date = datetime.fromisoformat(data['activity_date'].replace('Z', '+00:00'))
        except Exception:
            pass

    db.session.commit()
    return jsonify({
        'success': True,
        'message': 'Activity updated successfully.',
        'activity': activity.to_dict()
    }), 200

@activities_bp.route('/<int:activity_id>', methods=['DELETE'])
@jwt_required()
@admin_required()
def delete_activity(activity_id):
    """Admin deletes an activity."""
    activity = AcademicActivity.query.get(activity_id)
    if not activity:
        return jsonify({'success': False, 'message': 'Activity not found.'}), 404

    db.session.delete(activity)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Activity deleted successfully.'}), 200
