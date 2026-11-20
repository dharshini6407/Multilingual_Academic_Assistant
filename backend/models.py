from datetime import datetime
from db import db
from sqlalchemy.dialects.mysql import MEDIUMTEXT

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(191), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student', index=True) # 'student' or 'admin'
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    profile = db.relationship('UserProfile', backref='user', uselist=False, cascade="all, delete-orphan")
    preferences = db.relationship('NotificationPreference', backref='user', uselist=False, cascade="all, delete-orphan")
    attendance_records = db.relationship('AttendanceRecord', backref='user', cascade="all, delete-orphan")
    notifications = db.relationship('Notification', backref='user', cascade="all, delete-orphan")
    study_plans = db.relationship('StudyPlan', backref='user', cascade="all, delete-orphan")
    study_tasks = db.relationship('StudyTask', backref='user', cascade="all, delete-orphan")
    focus_sessions = db.relationship('FocusSession', backref='user', cascade="all, delete-orphan")
    conversations = db.relationship('ChatbotConversation', backref='user', cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'profile': self.profile.to_dict() if self.profile else None
        }

class UserProfile(db.Model):
    __tablename__ = 'user_profiles'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    full_name = db.Column(db.String(150), nullable=False)
    register_number = db.Column(db.String(50), nullable=True)
    department = db.Column(db.String(100), nullable=False, default='Computer Science and Engineering')
    year_of_study = db.Column(db.Integer, nullable=False, default=3)
    semester = db.Column(db.Integer, nullable=False, default=5)
    preferred_language = db.Column(db.String(20), nullable=False, default='en') # 'en', 'ta', 'tanglish'
    avatar_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'full_name': self.full_name,
            'register_number': self.register_number,
            'department': self.department,
            'year_of_study': self.year_of_study,
            'semester': self.semester,
            'preferred_language': self.preferred_language,
            'avatar_url': self.avatar_url
        }

class NotificationPreference(db.Model):
    __tablename__ = 'notification_preferences'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    exam_alerts = db.Column(db.Boolean, nullable=False, default=True)
    assignment_alerts = db.Column(db.Boolean, nullable=False, default=True)
    activity_alerts = db.Column(db.Boolean, nullable=False, default=True)
    low_attendance_warning = db.Column(db.Boolean, nullable=False, default=True)
    study_plan_reminders = db.Column(db.Boolean, nullable=False, default=True)
    preferred_channel = db.Column(db.String(20), nullable=False, default='in_app')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'exam_alerts': self.exam_alerts,
            'assignment_alerts': self.assignment_alerts,
            'activity_alerts': self.activity_alerts,
            'low_attendance_warning': self.low_attendance_warning,
            'study_plan_reminders': self.study_plan_reminders,
            'preferred_channel': self.preferred_channel
        }

class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    department = db.Column(db.String(100), nullable=False, default='Computer Science and Engineering')
    semester = db.Column(db.Integer, nullable=False, default=5)
    credits = db.Column(db.Integer, nullable=False, default=3)
    faculty_name = db.Column(db.String(150), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    examinations = db.relationship('Examination', backref='subject', cascade="all, delete-orphan")
    assignments = db.relationship('Assignment', backref='subject', cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'department': self.department,
            'semester': self.semester,
            'credits': self.credits,
            'faculty_name': self.faculty_name
        }

class AttendanceRecord(db.Model):
    __tablename__ = 'attendance_records'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False)
    conducted_classes = db.Column(db.Integer, nullable=False, default=0)
    attended_classes = db.Column(db.Integer, nullable=False, default=0)
    target_percentage = db.Column(db.Float, nullable=False, default=75.0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    subject = db.relationship('Subject')

    __table_args__ = (
        db.UniqueConstraint('user_id', 'subject_id', name='uk_user_subject_attendance'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'subject_id': self.subject_id,
            'subject_code': self.subject.code if self.subject else None,
            'subject_name': self.subject.name if self.subject else None,
            'conducted_classes': self.conducted_classes,
            'attended_classes': self.attended_classes,
            'target_percentage': self.target_percentage,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Examination(db.Model):
    __tablename__ = 'examinations'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    exam_type = db.Column(db.String(50), nullable=False, default='Semester End Exam')
    exam_date = db.Column(db.Date, nullable=False, index=True)
    start_time = db.Column(db.String(10), nullable=False, default='10:00:00')
    end_time = db.Column(db.String(10), nullable=False, default='13:00:00')
    hall_number = db.Column(db.String(50), default='Main Block Hall 302')
    max_marks = db.Column(db.Integer, nullable=False, default=100)
    status = db.Column(db.String(20), nullable=False, default='scheduled', index=True) # scheduled, rescheduled, completed, cancelled
    remarks = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'subject_id': self.subject_id,
            'subject_code': self.subject.code if self.subject else None,
            'subject_name': self.subject.name if self.subject else None,
            'title': self.title,
            'exam_type': self.exam_type,
            'exam_date': self.exam_date.strftime('%Y-%m-%d') if self.exam_date else None,
            'start_time': str(self.start_time),
            'end_time': str(self.end_time),
            'hall_number': self.hall_number,
            'max_marks': self.max_marks,
            'status': self.status,
            'remarks': self.remarks
        }

class Assignment(db.Model):
    __tablename__ = 'assignments'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(191), nullable=False)
    description = db.Column(db.Text, nullable=True)
    deadline = db.Column(db.DateTime, nullable=False, index=True)
    priority = db.Column(db.String(20), nullable=False, default='medium', index=True) # low, medium, high
    max_score = db.Column(db.Integer, nullable=False, default=20)
    status = db.Column(db.String(20), nullable=False, default='active') # active, completed, cancelled
    created_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'subject_id': self.subject_id,
            'subject_code': self.subject.code if self.subject else None,
            'subject_name': self.subject.name if self.subject else None,
            'title': self.title,
            'description': self.description,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'priority': self.priority,
            'max_score': self.max_score,
            'status': self.status
        }

class StudentAssignmentStatus(db.Model):
    __tablename__ = 'student_assignment_status'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignments.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending') # pending, in_progress, submitted, completed
    submitted_at = db.Column(db.DateTime, nullable=True)
    student_notes = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    assignment = db.relationship('Assignment')

    __table_args__ = (
        db.UniqueConstraint('user_id', 'assignment_id', name='uk_user_assignment'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'assignment_id': self.assignment_id,
            'status': self.status,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'student_notes': self.student_notes
        }

class AcademicActivity(db.Model):
    __tablename__ = 'academic_activities'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(191), nullable=False)
    activity_type = db.Column(db.String(50), nullable=False, default='workshop')
    description = db.Column(db.Text, nullable=True)
    activity_date = db.Column(db.DateTime, nullable=False, index=True)
    venue = db.Column(db.String(150), nullable=False, default='Auditorium / Online')
    organizer = db.Column(db.String(150), default='Department of CSE')
    priority = db.Column(db.String(20), nullable=False, default='medium')
    status = db.Column(db.String(20), nullable=False, default='scheduled')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'activity_type': self.activity_type,
            'description': self.description,
            'activity_date': self.activity_date.isoformat() if self.activity_date else None,
            'venue': self.venue,
            'organizer': self.organizer,
            'priority': self.priority,
            'status': self.status
        }

class AcademicDocument(db.Model):
    __tablename__ = 'academic_documents'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(50), nullable=False, default='curriculum')
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size_bytes = db.Column(db.BigInteger, nullable=False, default=0)
    mime_type = db.Column(db.String(100), nullable=False, default='application/pdf')
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    total_pages = db.Column(db.Integer, nullable=False, default=1)
    total_chunks = db.Column(db.Integer, nullable=False, default=0)
    language = db.Column(db.String(20), nullable=False, default='en')
    description = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    chunks = db.relationship('DocumentChunk', backref='document', cascade="all, delete-orphan")
    versions = db.relationship('DocumentVersion', backref='document', cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'category': self.category,
            'file_name': self.file_name,
            'file_size_bytes': self.file_size_bytes,
            'is_active': self.is_active,
            'total_pages': self.total_pages,
            'total_chunks': self.total_chunks,
            'language': self.language,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class DocumentVersion(db.Model):
    __tablename__ = 'document_versions'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    document_id = db.Column(db.Integer, db.ForeignKey('academic_documents.id', ondelete='CASCADE'), nullable=False)
    version_number = db.Column(db.Integer, nullable=False, default=1)
    change_summary = db.Column(db.String(255), default='Initial upload')
    file_path = db.Column(db.String(500), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class DocumentChunk(db.Model):
    __tablename__ = 'document_chunks'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    document_id = db.Column(db.Integer, db.ForeignKey('academic_documents.id', ondelete='CASCADE'), nullable=False, index=True)
    chunk_index = db.Column(db.Integer, nullable=False)
    page_number = db.Column(db.Integer, nullable=False, default=1)
    section_title = db.Column(db.String(255), nullable=True)
    content = db.Column(db.Text, nullable=False)
    content_length = db.Column(db.Integer, nullable=False, default=0)
    embedding_json = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'document_id': self.document_id,
            'chunk_index': self.chunk_index,
            'page_number': self.page_number,
            'section_title': self.section_title,
            'content': self.content
        }

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(30), nullable=False, default='system')
    priority = db.Column(db.String(20), nullable=False, default='medium')
    is_read = db.Column(db.Boolean, nullable=False, default=False, index=True)
    read_at = db.Column(db.DateTime, nullable=True)
    action_link = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'message': self.message,
            'notification_type': self.notification_type,
            'priority': self.priority,
            'is_read': self.is_read,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'action_link': self.action_link,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class NotificationDeliveryRecord(db.Model):
    __tablename__ = 'notification_delivery_records'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    dedup_key = db.Column(db.String(191), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    notification_id = db.Column(db.Integer, db.ForeignKey('notifications.id', ondelete='SET NULL'), nullable=True)
    entity_type = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.Integer, nullable=False)
    days_before = db.Column(db.Integer, nullable=False)
    delivered_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='delivered')

class StudyPlan(db.Model):
    __tablename__ = 'study_plans'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(150), nullable=False, default='My Weekly Academic Plan')
    plan_type = db.Column(db.String(20), nullable=False, default='weekly')
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    target_hours_per_day = db.Column(db.Float, nullable=False, default=3.0)
    completion_percentage = db.Column(db.Float, nullable=False, default=0.0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    tasks = db.relationship('StudyTask', backref='plan', cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'plan_type': self.plan_type,
            'start_date': self.start_date.strftime('%Y-%m-%d') if self.start_date else None,
            'end_date': self.end_date.strftime('%Y-%m-%d') if self.end_date else None,
            'target_hours_per_day': self.target_hours_per_day,
            'completion_percentage': round(self.completion_percentage, 1),
            'tasks_count': len(self.tasks)
        }

class StudyTask(db.Model):
    __tablename__ = 'study_tasks'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('study_plans.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id', ondelete='SET NULL'), nullable=True)
    title = db.Column(db.String(191), nullable=False)
    description = db.Column(db.Text, nullable=True)
    estimated_minutes = db.Column(db.Integer, nullable=False, default=45)
    actual_minutes = db.Column(db.Integer, nullable=False, default=0)
    priority = db.Column(db.String(20), nullable=False, default='medium')
    scheduled_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.String(10), default='09:00:00')
    is_completed = db.Column(db.Boolean, nullable=False, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    subject = db.relationship('Subject')

    def to_dict(self):
        return {
            'id': self.id,
            'plan_id': self.plan_id,
            'user_id': self.user_id,
            'subject_id': self.subject_id,
            'subject_name': self.subject.name if self.subject else None,
            'subject_code': self.subject.code if self.subject else None,
            'title': self.title,
            'description': self.description,
            'estimated_minutes': self.estimated_minutes,
            'actual_minutes': self.actual_minutes,
            'priority': self.priority,
            'scheduled_date': self.scheduled_date.strftime('%Y-%m-%d') if self.scheduled_date else None,
            'start_time': str(self.start_time),
            'is_completed': self.is_completed,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

class FocusSession(db.Model):
    __tablename__ = 'focus_sessions'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id', ondelete='SET NULL'), nullable=True)
    task_id = db.Column(db.Integer, db.ForeignKey('study_tasks.id', ondelete='SET NULL'), nullable=True)
    duration_minutes = db.Column(db.Integer, nullable=False, default=25)
    break_minutes = db.Column(db.Integer, nullable=False, default=5)
    actual_focused_seconds = db.Column(db.Integer, nullable=False, default=1500)
    session_status = db.Column(db.String(20), nullable=False, default='completed') # completed, abandoned, interrupted
    started_at = db.Column(db.DateTime, nullable=False)
    ended_at = db.Column(db.DateTime, nullable=False)
    notes = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    subject = db.relationship('Subject')
    task = db.relationship('StudyTask')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'subject_id': self.subject_id,
            'subject_name': self.subject.name if self.subject else None,
            'task_id': self.task_id,
            'task_title': self.task.title if self.task else None,
            'duration_minutes': self.duration_minutes,
            'break_minutes': self.break_minutes,
            'actual_focused_seconds': self.actual_focused_seconds,
            'actual_focused_minutes': round(self.actual_focused_seconds / 60.0, 1),
            'session_status': self.session_status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'notes': self.notes
        }

class ChatbotConversation(db.Model):
    __tablename__ = 'chatbot_conversations'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    session_title = db.Column(db.String(191), nullable=False, default='Academic Inquiries')
    language = db.Column(db.String(20), nullable=False, default='en') # en, ta, tanglish
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = db.relationship('ChatbotMessage', backref='conversation', cascade="all, delete-orphan", order_by="ChatbotMessage.created_at")

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'session_title': self.session_title,
            'language': self.language,
            'messages_count': len(self.messages),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ChatbotMessage(db.Model):
    __tablename__ = 'chatbot_messages'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('chatbot_conversations.id', ondelete='CASCADE'), nullable=False, index=True)
    sender = db.Column(db.String(20), nullable=False) # user or assistant
    message = db.Column(db.Text, nullable=False)
    detected_language = db.Column(db.String(20), nullable=False, default='en')
    retrieved_sources = db.Column(db.JSON, nullable=True) # list of {document_name, page_number, excerpt}
    is_fallback = db.Column(db.Boolean, nullable=False, default=False)
    is_supported_by_docs = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    feedbacks = db.relationship('ChatbotFeedback', backref='message', cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'sender': self.sender,
            'message': self.message,
            'detected_language': self.detected_language,
            'retrieved_sources': self.retrieved_sources,
            'is_fallback': self.is_fallback,
            'is_supported_by_docs': self.is_supported_by_docs,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class ChatbotFeedback(db.Model):
    __tablename__ = 'chatbot_feedback'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    message_id = db.Column(db.Integer, db.ForeignKey('chatbot_messages.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    rating = db.Column(db.String(20), nullable=False) # helpful, unhelpful
    comments = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'message_id': self.message_id,
            'user_id': self.user_id,
            'rating': self.rating,
            'comments': self.comments,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class UnansweredQuestion(db.Model):
    __tablename__ = 'unanswered_questions'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    detected_language = db.Column(db.String(20), nullable=False, default='en')
    context_attempted = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(30), nullable=False, default='pending_review') # pending_review, resolved, ignored
    admin_reply = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'question': self.question,
            'detected_language': self.detected_language,
            'status': self.status,
            'admin_reply': self.admin_reply,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ApplicationSetting(db.Model):
    __tablename__ = 'application_settings'
    setting_key = db.Column(db.String(100), primary_key=True)
    setting_value = db.Column(db.Text, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'setting_key': self.setting_key,
            'setting_value': self.setting_value,
            'description': self.description
        }
