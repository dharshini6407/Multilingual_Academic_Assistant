from datetime import datetime, timedelta
from typing import List, Dict, Any
from db import db
from models import StudyPlan, StudyTask, Assignment, Examination

def calculate_plan_completion(plan_id: int) -> float:
    """Calculate and persist current completion percentage for a study plan."""
    tasks = StudyTask.query.filter_by(plan_id=plan_id).all()
    if not tasks:
        return 0.0
    completed = sum(1 for t in tasks if t.is_completed)
    pct = round((completed / len(tasks)) * 100.0, 1)
    
    plan = StudyPlan.query.get(plan_id)
    if plan:
        plan.completion_percentage = pct
        db.session.commit()
    return pct

def generate_smart_study_schedule(
    user_id: int,
    plan_id: int,
    start_date,
    end_date,
    target_hours_per_day: float = 3.0,
    include_upcoming_deadlines: bool = True
) -> List[Dict[str, Any]]:
    """
    Generate an optimized study schedule using transparent heuristic rules:
    Rule 1: Priority weighting (High: 30, Medium: 20, Low: 10)
    Rule 2: Deadline urgency (Closer deadlines receive higher urgency score)
    Rule 3: Daily capacity constraint (Cannot exceed target_hours_per_day)
    Rule 4: Time blocking with rest intervals (Study sessions spaced in evening blocks)
    """
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

    total_days = max(1, (end_date - start_date).days + 1)
    daily_budget_minutes = int(target_hours_per_day * 60)

    # 1. Existing incomplete tasks in this plan
    existing_tasks = StudyTask.query.filter_by(plan_id=plan_id, is_completed=False).all()
    task_queue = []

    for t in existing_tasks:
        prio_weight = {'high': 30, 'medium': 20, 'low': 10}.get(t.priority.lower(), 15)
        task_queue.append({
            'id': t.id,
            'title': t.title,
            'subject_id': t.subject_id,
            'estimated_minutes': t.estimated_minutes or 45,
            'priority': t.priority,
            'score': prio_weight + 20, # Baseline priority score
            'is_auto': False
        })

    # 2. Automatically incorporate upcoming assignments and exams if requested
    if include_upcoming_deadlines:
        assignments = Assignment.query.filter_by(status='active').all()
        for a in assignments:
            dead_date = a.deadline.date() if isinstance(a.deadline, datetime) else a.deadline
            days_left = (dead_date - start_date).days
            if 0 <= days_left <= (total_days + 7):
                urgency = max(0, 50 - (days_left * 5))
                prio_weight = {'high': 30, 'medium': 20, 'low': 10}.get(a.priority.lower(), 20)
                task_queue.append({
                    'id': None,
                    'title': f"Review & Complete Assignment: {a.title}",
                    'subject_id': a.subject_id,
                    'estimated_minutes': 60,
                    'priority': a.priority,
                    'score': urgency + prio_weight,
                    'is_auto': True
                })

        exams = Examination.query.filter(Examination.status.in_(['scheduled', 'rescheduled'])).all()
        for e in exams:
            days_left = (e.exam_date - start_date).days
            if 0 <= days_left <= (total_days + 14):
                urgency = max(0, 60 - (days_left * 4))
                task_queue.append({
                    'id': None,
                    'title': f"Revision for {e.exam_type}: {e.subject.name if e.subject else e.title}",
                    'subject_id': e.subject_id,
                    'estimated_minutes': 90,
                    'priority': 'high',
                    'score': urgency + 40,
                    'is_auto': True
                })

    # Sort descending by composite urgency score
    task_queue.sort(key=lambda x: x['score'], reverse=True)

    # Distribute tasks across available calendar days
    calendar_days = [start_date + timedelta(days=i) for i in range(total_days)]
    day_allocations = {d: {'minutes': 0, 'tasks': []} for d in calendar_days}
    
    # Standard evening study time blocks
    time_slots = ['17:00:00', '18:15:00', '19:45:00', '21:00:00']

    scheduled_results = []

    for task_info in task_queue:
        dur = task_info['estimated_minutes']
        # Find earliest day with capacity
        placed = False
        for d in calendar_days:
            if day_allocations[d]['minutes'] + dur <= (daily_budget_minutes + 15):
                slot_idx = len(day_allocations[d]['tasks'])
                chosen_time = time_slots[min(slot_idx, len(time_slots) - 1)]

                # If task already exists in DB, update scheduled date and time
                if task_info['id']:
                    db_task = StudyTask.query.get(task_info['id'])
                    if db_task:
                        db_task.scheduled_date = d
                        db_task.start_time = chosen_time
                else:
                    # Create new scheduled task
                    db_task = StudyTask(
                        plan_id=plan_id,
                        user_id=user_id,
                        subject_id=task_info['subject_id'],
                        title=task_info['title'],
                        estimated_minutes=dur,
                        priority=task_info['priority'],
                        scheduled_date=d,
                        start_time=chosen_time,
                        is_completed=False
                    )
                    db.session.add(db_task)

                day_allocations[d]['minutes'] += dur
                day_allocations[d]['tasks'].append(task_info['title'])
                placed = True
                break

        if not placed:
            # Overflows to last day
            last_day = calendar_days[-1]
            if task_info['id']:
                db_task = StudyTask.query.get(task_info['id'])
                if db_task:
                    db_task.scheduled_date = last_day
                    db_task.start_time = '20:00:00'
            else:
                db_task = StudyTask(
                    plan_id=plan_id,
                    user_id=user_id,
                    subject_id=task_info['subject_id'],
                    title=task_info['title'],
                    estimated_minutes=dur,
                    priority=task_info['priority'],
                    scheduled_date=last_day,
                    start_time='20:00:00',
                    is_completed=False
                )
                db.session.add(db_task)

    db.session.commit()
    calculate_plan_completion(plan_id)
    return [t.to_dict() for t in StudyTask.query.filter_by(plan_id=plan_id).order_by(StudyTask.scheduled_date).all()]
