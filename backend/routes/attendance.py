from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import db
from models import AttendanceRecord, Subject, User
from services.attendance_service import calculate_attendance_metrics
from services.auth_service import admin_required

attendance_bp = Blueprint('attendance', __name__)

@attendance_bp.route('', methods=['GET'])
@jwt_required()
def get_attendance_records():
    """Get subject-wise attendance with calculated formulas, targets, and warnings."""
    user_id = int(get_jwt_identity())
    records = AttendanceRecord.query.filter_by(user_id=user_id).all()

    total_conducted = 0
    total_attended = 0
    subject_details = []

    for r in records:
        metrics = calculate_attendance_metrics(
            conducted=r.conducted_classes,
            attended=r.attended_classes,
            target_percentage=float(r.target_percentage)
        )
        total_conducted += r.conducted_classes
        total_attended += r.attended_classes

        rec_dict = r.to_dict()
        rec_dict['metrics'] = metrics
        subject_details.append(rec_dict)

    overall_metrics = calculate_attendance_metrics(
        conducted=total_conducted,
        attended=total_attended,
        target_percentage=75.0
    )

    return jsonify({
        'success': True,
        'overall': overall_metrics,
        'records': subject_details
    }), 200

@attendance_bp.route('/target', methods=['PUT'])
@jwt_required()
def set_attendance_target():
    """Allow student to set or update personal attendance target for a subject."""
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}

    subject_id = data.get('subject_id')
    target_percentage = data.get('target_percentage')

    if not subject_id or target_percentage is None:
        return jsonify({'success': False, 'message': 'Subject ID and target percentage are required.'}), 400

    try:
        target_percentage = float(target_percentage)
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid target percentage.'}), 400

    if target_percentage <= 0 or target_percentage > 100:
        return jsonify({'success': False, 'message': 'Target percentage must be between 1 and 100.'}), 400

    record = AttendanceRecord.query.filter_by(user_id=user_id, subject_id=subject_id).first()
    if not record:
        record = AttendanceRecord(
            user_id=user_id,
            subject_id=subject_id,
            conducted_classes=0,
            attended_classes=0,
            target_percentage=target_percentage
        )
        db.session.add(record)
    else:
        record.target_percentage = target_percentage

    db.session.commit()

    updated_metrics = calculate_attendance_metrics(
        conducted=record.conducted_classes,
        attended=record.attended_classes,
        target_percentage=record.target_percentage
    )

    return jsonify({
        'success': True,
        'message': f'Attendance target set to {target_percentage}%.',
        'record': record.to_dict(),
        'metrics': updated_metrics
    }), 200

@attendance_bp.route('/record', methods=['POST'])
@jwt_required()
def save_or_update_attendance_record():
    """Add or update conducted and attended counts for a student."""
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    data = request.get_json() or {}

    target_user_id = data.get('user_id', user_id)
    # Only admin can edit other users' attendance
    if int(target_user_id) != user_id and user.role != 'admin':
        return jsonify({'success': False, 'message': 'Access forbidden.'}), 403

    subject_id = data.get('subject_id')
    conducted = data.get('conducted_classes')
    attended = data.get('attended_classes')
    target = data.get('target_percentage', 75.0)

    if not subject_id or conducted is None or attended is None:
        return jsonify({'success': False, 'message': 'subject_id, conducted_classes, and attended_classes are required.'}), 400

    try:
        conducted = int(conducted)
        attended = int(attended)
        target = float(target)
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid numeric values.'}), 400

    if conducted < 0 or attended < 0:
        return jsonify({'success': False, 'message': 'Class counts cannot be negative.'}), 400

    if attended > conducted:
        return jsonify({'success': False, 'message': 'Attended classes cannot exceed conducted classes.'}), 400

    record = AttendanceRecord.query.filter_by(user_id=target_user_id, subject_id=subject_id).first()
    if not record:
        record = AttendanceRecord(
            user_id=target_user_id,
            subject_id=subject_id,
            conducted_classes=conducted,
            attended_classes=attended,
            target_percentage=target
        )
        db.session.add(record)
    else:
        record.conducted_classes = conducted
        record.attended_classes = attended
        if target:
            record.target_percentage = target

    db.session.commit()

    metrics = calculate_attendance_metrics(
        conducted=record.conducted_classes,
        attended=record.attended_classes,
        target_percentage=record.target_percentage
    )

    return jsonify({
        'success': True,
        'message': 'Attendance record updated successfully.',
        'record': record.to_dict(),
        'metrics': metrics
    }), 200

@attendance_bp.route('/simulate', methods=['POST'])
@jwt_required()
def simulate_future_attendance():
    """
    Simulate what attendance percentage will be if student attends
    or misses next N classes.
    """
    data = request.get_json() or {}
    conducted = int(data.get('conducted', 0))
    attended = int(data.get('attended', 0))
    target = float(data.get('target', 75.0))
    future_classes_attend = int(data.get('future_classes_attend', 0))
    future_classes_miss = int(data.get('future_classes_miss', 0))

    sim_conducted = conducted + future_classes_attend + future_classes_miss
    sim_attended = attended + future_classes_attend

    current_metrics = calculate_attendance_metrics(conducted, attended, target)
    simulated_metrics = calculate_attendance_metrics(sim_conducted, sim_attended, target)

    pct_diff = round(simulated_metrics['percentage'] - current_metrics['percentage'], 2)

    return jsonify({
        'success': True,
        'current': current_metrics,
        'simulated': simulated_metrics,
        'percentage_difference': pct_diff,
        'summary': f"If you attend {future_classes_attend} and miss {future_classes_miss} classes, your attendance will become {simulated_metrics['percentage']}% ({'+' if pct_diff >= 0 else ''}{pct_diff}%)."
    }), 200
