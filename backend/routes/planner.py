from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import db
from models import StudyPlan, StudyTask, Subject
from services.study_planner_service import (
    calculate_plan_completion, generate_smart_study_schedule
)
from services.scheduler_service import get_kolkata_now

planner_bp = Blueprint('planner', __name__)

@planner_bp.route('/plans', methods=['GET'])
@jwt_required()
def get_user_plans():
    """Retrieve all study plans for the authenticated student."""
    user_id = int(get_jwt_identity())
    plans = StudyPlan.query.filter_by(user_id=user_id).order_by(StudyPlan.start_date.desc()).all()
    return jsonify({
        'success': True,
        'plans': [p.to_dict() for p in plans]
    }), 200

@planner_bp.route('/plans', methods=['POST'])
@jwt_required()
def create_study_plan():
    """Create a new daily or weekly study plan."""
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}

    title = data.get('title', 'Weekly Academic Plan').strip()
    plan_type = data.get('plan_type', 'weekly')
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')
    target_hours = float(data.get('target_hours_per_day', 3.0))

    today = get_kolkata_now().date()

    if not start_date_str:
        start_date = today
    else:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()

    if not end_date_str:
        if plan_type == 'daily':
            end_date = start_date
        else:
            end_date = start_date + timedelta(days=6)
    else:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

    plan = StudyPlan(
        user_id=user_id,
        title=title,
        plan_type=plan_type,
        start_date=start_date,
        end_date=end_date,
        target_hours_per_day=target_hours,
        completion_percentage=0.0
    )
    db.session.add(plan)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Study plan created successfully.',
        'plan': plan.to_dict()
    }), 201

@planner_bp.route('/plans/<int:plan_id>/tasks', methods=['GET'])
@jwt_required()
def get_plan_tasks(plan_id):
    """Get all tasks scheduled in a specific study plan."""
    user_id = int(get_jwt_identity())
    plan = StudyPlan.query.filter_by(id=plan_id, user_id=user_id).first()
    if not plan:
        return jsonify({'success': False, 'message': 'Plan not found.'}), 404

    tasks = StudyTask.query.filter_by(plan_id=plan_id).order_by(
        StudyTask.scheduled_date.asc(), StudyTask.start_time.asc()
    ).all()

    return jsonify({
        'success': True,
        'plan': plan.to_dict(),
        'tasks': [t.to_dict() for t in tasks]
    }), 200

@planner_bp.route('/tasks', methods=['POST'])
@jwt_required()
def add_study_task():
    """Add a study task to a plan."""
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}

    plan_id = data.get('plan_id')
    subject_id = data.get('subject_id')
    title = data.get('title', '').strip()
    description = data.get('description', '')
    estimated_minutes = int(data.get('estimated_minutes', 45))
    priority = data.get('priority', 'medium').lower()
    scheduled_date_str = data.get('scheduled_date')
    start_time = data.get('start_time', '18:00:00')

    if not plan_id or not title:
        return jsonify({'success': False, 'message': 'Plan ID and task title are required.'}), 400

    plan = StudyPlan.query.filter_by(id=plan_id, user_id=user_id).first()
    if not plan:
        return jsonify({'success': False, 'message': 'Study plan not found or not owned by you.'}), 404

    if not scheduled_date_str:
        scheduled_date = plan.start_date
    else:
        scheduled_date = datetime.strptime(scheduled_date_str, '%Y-%m-%d').date()

    task = StudyTask(
        plan_id=plan_id,
        user_id=user_id,
        subject_id=subject_id,
        title=title,
        description=description,
        estimated_minutes=estimated_minutes,
        priority=priority,
        scheduled_date=scheduled_date,
        start_time=start_time,
        is_completed=False
    )
    db.session.add(task)
    db.session.commit()

    calculate_plan_completion(plan_id)

    return jsonify({
        'success': True,
        'message': 'Task added successfully.',
        'task': task.to_dict()
    }), 201

@planner_bp.route('/tasks/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_study_task(task_id):
    """Update study task properties or mark as completed."""
    user_id = int(get_jwt_identity())
    task = StudyTask.query.filter_by(id=task_id, user_id=user_id).first()
    if not task:
        return jsonify({'success': False, 'message': 'Task not found or access denied.'}), 404

    data = request.get_json() or {}
    if 'title' in data and data['title'].strip():
        task.title = data['title'].strip()
    if 'description' in data:
        task.description = data['description']
    if 'estimated_minutes' in data:
        task.estimated_minutes = int(data['estimated_minutes'])
    if 'actual_minutes' in data:
        task.actual_minutes = int(data['actual_minutes'])
    if 'priority' in data and data['priority'] in ['low', 'medium', 'high']:
        task.priority = data['priority']
    if 'scheduled_date' in data and data['scheduled_date']:
        task.scheduled_date = datetime.strptime(data['scheduled_date'], '%Y-%m-%d').date()
    if 'start_time' in data:
        task.start_time = data['start_time']
    if 'is_completed' in data:
        is_comp = bool(data['is_completed'])
        task.is_completed = is_comp
        task.completed_at = datetime.utcnow() if is_comp else None

    db.session.commit()
    pct = calculate_plan_completion(task.plan_id)

    return jsonify({
        'success': True,
        'message': 'Task updated successfully.',
        'task': task.to_dict(),
        'plan_completion_percentage': pct
    }), 200

@planner_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_study_task(task_id):
    """Delete a task from the plan."""
    user_id = int(get_jwt_identity())
    task = StudyTask.query.filter_by(id=task_id, user_id=user_id).first()
    if not task:
        return jsonify({'success': False, 'message': 'Task not found or access denied.'}), 404

    plan_id = task.plan_id
    db.session.delete(task)
    db.session.commit()
    pct = calculate_plan_completion(plan_id)

    return jsonify({
        'success': True,
        'message': 'Task deleted successfully.',
        'plan_completion_percentage': pct
    }), 200

@planner_bp.route('/generate', methods=['POST'])
@jwt_required()
def generate_schedule():
    """
    Run rule-based schedule generator considering:
    - Deadlines and upcoming exams
    - Priorities
    - Available study hours per day
    """
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    plan_id = data.get('plan_id')

    plan = StudyPlan.query.filter_by(id=plan_id, user_id=user_id).first() if plan_id else None
    if not plan:
        # Create default weekly plan if none exists
        today = get_kolkata_now().date()
        plan = StudyPlan(
            user_id=user_id,
            title='Optimized Weekly Academic Schedule',
            plan_type='weekly',
            start_date=today,
            end_date=today + timedelta(days=6),
            target_hours_per_day=float(data.get('target_hours_per_day', 3.0)),
            completion_percentage=0.0
        )
        db.session.add(plan)
        db.session.commit()

    scheduled_tasks = generate_smart_study_schedule(
        user_id=user_id,
        plan_id=plan.id,
        start_date=plan.start_date,
        end_date=plan.end_date,
        target_hours_per_day=plan.target_hours_per_day,
        include_upcoming_deadlines=data.get('include_upcoming_deadlines', True)
    )

    return jsonify({
        'success': True,
        'message': f'Smart study schedule generated with {len(scheduled_tasks)} tasks.',
        'plan': plan.to_dict(),
        'tasks': scheduled_tasks
    }), 200
