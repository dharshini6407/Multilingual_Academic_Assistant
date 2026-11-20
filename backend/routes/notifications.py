from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import db
from models import Notification

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('', methods=['GET'])
@jwt_required()
def get_user_notifications():
    """List notifications with unread count and filtering."""
    user_id = int(get_jwt_identity())
    notif_type = request.args.get('type')

    query = Notification.query.filter_by(user_id=user_id)
    if notif_type:
        query = query.filter_by(notification_type=notif_type)

    notifications = query.order_by(Notification.created_at.desc()).all()
    unread_count = Notification.query.filter_by(user_id=user_id, is_read=False).count()

    return jsonify({
        'success': True,
        'unread_count': unread_count,
        'total_count': len(notifications),
        'notifications': [n.to_dict() for n in notifications]
    }), 200

@notifications_bp.route('/<int:notif_id>/read', methods=['PUT'])
@jwt_required()
def mark_notification_as_read(notif_id):
    """Mark a notification as read (user ownership enforced)."""
    user_id = int(get_jwt_identity())
    notif = Notification.query.filter_by(id=notif_id, user_id=user_id).first()
    if not notif:
        return jsonify({'success': False, 'message': 'Notification not found or access denied.'}), 404

    notif.is_read = True
    notif.read_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Marked as read.',
        'notification': notif.to_dict()
    }), 200

@notifications_bp.route('/read-all', methods=['PUT'])
@jwt_required()
def mark_all_notifications_as_read():
    """Mark all unread notifications for the user as read."""
    user_id = int(get_jwt_identity())
    now = datetime.utcnow()
    updated = Notification.query.filter_by(user_id=user_id, is_read=False).update({
        'is_read': True,
        'read_at': now
    })
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Marked {updated} notifications as read.'
    }), 200

@notifications_bp.route('/<int:notif_id>', methods=['DELETE'])
@jwt_required()
def delete_notification(notif_id):
    """Delete a notification (user ownership enforced)."""
    user_id = int(get_jwt_identity())
    notif = Notification.query.filter_by(id=notif_id, user_id=user_id).first()
    if not notif:
        return jsonify({'success': False, 'message': 'Notification not found or access denied.'}), 404

    db.session.delete(notif)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Notification deleted successfully.'
    }), 200
