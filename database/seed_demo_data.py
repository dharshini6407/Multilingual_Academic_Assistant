import os
import sys

os.environ['SEEDING'] = '1'
os.environ['DB_TYPE'] = os.environ.get('DB_TYPE', 'auto')
from datetime import datetime, timedelta

# Ensure backend directory is in path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app import create_app
from db import db
from models import (
    User, UserProfile, NotificationPreference, Subject,
    AttendanceRecord, Examination, Assignment, StudentAssignmentStatus,
    AcademicActivity, AcademicDocument, DocumentVersion, DocumentChunk,
    StudyPlan, StudyTask, FocusSession, ChatbotConversation,
    ChatbotMessage, Notification, NotificationDeliveryRecord, ApplicationSetting
)
from services.auth_service import hash_password
from services.scheduler_service import get_kolkata_now

def generate_sample_pdf(file_path: str, title: str, pages_text: list):
    """
    Generate a simple, valid standard PDF file containing text pages.
    Uses pypdf or creates minimal valid PDF syntax if no heavy libraries.
    """
    try:
        from pypdf import PdfWriter
        from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject, ArrayObject, NumberObject
        # If reportlab or fpdf isn't installed, minimal PDF byte construction:
    except Exception:
        pass

    # Clean standard PDF 1.4 byte builder:
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # We will write a valid 3-page PDF with clear plain ASCII/Latin1 streams
    objects = []
    
    # Obj 1: Catalog
    objects.append("1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    
    # Obj 2: Pages
    kid_refs = " ".join([f"{3 + i*2} 0 R" for i in range(len(pages_text))])
    objects.append(f"2 0 obj\n<< /Type /Pages /Kids [{kid_refs}] /Count {len(pages_text)} >>\nendobj\n")
    
    curr_obj = 3
    page_objs = []
    stream_objs = []
    
    for idx, page_content in enumerate(pages_text):
        p_obj_id = curr_obj
        c_obj_id = curr_obj + 1
        curr_obj += 2
        
        # Escape parenthesis in text
        safe_lines = page_content.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)').split('\n')
        stream_lines = ["BT", "/F1 12 Tf", "50 750 Td", "14 TL"]
        for line in safe_lines:
            stream_lines.append(f"({line[:80]}) Tj")
            stream_lines.append("T*")
        stream_lines.append("ET")
        stream_data = "\n".join(stream_lines)
        
        page_obj = f"{p_obj_id} 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents {c_obj_id} 0 R /Resources << /Font << /F1 {curr_obj + len(pages_text)*2} 0 R >> >> >>\nendobj\n"
        stream_obj = f"{c_obj_id} 0 obj\n<< /Length {len(stream_data)} >>\nstream\n{stream_data}\nendstream\nendobj\n"
        
        objects.append(page_obj)
        objects.append(stream_obj)

    # Font object
    font_id = curr_obj + len(pages_text)*2
    objects.append(f"{font_id} 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n")
    
    # Write PDF file
    with open(file_path, "wb") as f:
        f.write(b"%PDF-1.4\n")
        offsets = [0]
        pos = len(b"%PDF-1.4\n")
        
        for obj in objects:
            offsets.append(pos)
            b = obj.encode('latin1')
            f.write(b)
            pos += len(b)
            
        xref_pos = pos
        f.write(f"xref\n0 {len(objects) + 1}\n".encode('ascii'))
        f.write(b"0000000000 65535 f \n")
        for off in offsets[1:]:
            f.write(f"{off:010d} 00000 n \n".encode('ascii'))
            
        trailer = f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n"
        f.write(trailer.encode('ascii'))

def seed_database():
    app = create_app()
    with app.app_context():
        print("Initializing database schema...")
        db.create_all()

        # 1. Check or Create Users
        admin = User.query.filter_by(email='admin@college.edu').first()
        if not admin:
            admin = User(
                email='admin@college.edu',
                password_hash=hash_password('Admin@123'),
                role='admin',
                is_active=True
            )
            db.session.add(admin)
            db.session.flush()

            admin_prof = UserProfile(
                user_id=admin.id,
                full_name='Dr. K. Ramanathan',
                register_number='FAC-CSE-001',
                department='Computer Science and Engineering',
                year_of_study=0,
                semester=0,
                preferred_language='en'
            )
            db.session.add(admin_prof)

            admin_pref = NotificationPreference(user_id=admin.id)
            db.session.add(admin_pref)

        student = User.query.filter_by(email='student@college.edu').first()
        if not student:
            student = User(
                email='student@college.edu',
                password_hash=hash_password('Student@123'),
                role='student',
                is_active=True
            )
            db.session.add(student)
            db.session.flush()

            student_prof = UserProfile(
                user_id=student.id,
                full_name='Aravindhan Sundaram',
                register_number='917721CSE045',
                department='Computer Science and Engineering',
                year_of_study=3,
                semester=5,
                preferred_language='tanglish'
            )
            db.session.add(student_prof)

            student_pref = NotificationPreference(
                user_id=student.id,
                exam_alerts=True,
                assignment_alerts=True,
                activity_alerts=True,
                low_attendance_warning=True,
                study_plan_reminders=True
            )
            db.session.add(student_pref)

        db.session.commit()
        print(f"Users verified: Admin (ID {admin.id}), Student (ID {student.id})")

        # 2. Subjects
        subjects_data = [
            {'code': 'CS8501', 'name': 'Theory of Computation', 'credits': 3, 'faculty': 'Dr. S. Meenakshi'},
            {'code': 'CS8591', 'name': 'Computer Networks', 'credits': 3, 'faculty': 'Prof. R. Balaji'},
            {'code': 'CS8592', 'name': 'Object Oriented Analysis and Design', 'credits': 3, 'faculty': 'Dr. V. Priya'},
            {'code': 'EC8681', 'name': 'Microprocessors and Microcontrollers', 'credits': 3, 'faculty': 'Prof. S. Karthik'},
            {'code': 'CS8581', 'name': 'Professional Ethics in Engineering', 'credits': 2, 'faculty': 'Dr. T. Lakshmi'},
            {'code': 'CS8511', 'name': 'Networks Laboratory', 'credits': 2, 'faculty': 'Prof. R. Balaji'}
        ]

        created_subjects = {}
        for s in subjects_data:
            subj = Subject.query.filter_by(code=s['code']).first()
            if not subj:
                subj = Subject(
                    code=s['code'],
                    name=s['name'],
                    department='Computer Science and Engineering',
                    semester=5,
                    credits=s['credits'],
                    faculty_name=s['faculty']
                )
                db.session.add(subj)
                db.session.flush()
            created_subjects[s['code']] = subj

        db.session.commit()
        print(f"Subjects created: {len(created_subjects)}")

        # 3. Attendance Records (Real Numbers, Edge Cases, and Warnings)
        attendance_seed = [
            {'code': 'CS8501', 'conducted': 42, 'attended': 36, 'target': 75.0}, # 85.7% (Safe)
            {'code': 'CS8591', 'conducted': 40, 'attended': 27, 'target': 75.0}, # 67.5% (Shortage Warning)
            {'code': 'CS8592', 'conducted': 38, 'attended': 32, 'target': 80.0}, # 84.2% (Target 80 met)
            {'code': 'EC8681', 'conducted': 44, 'attended': 31, 'target': 75.0}, # 70.4% (Below target)
            {'code': 'CS8581', 'conducted': 28, 'attended': 26, 'target': 75.0}, # 92.8% (Excellent)
            {'code': 'CS8511', 'conducted': 14, 'attended': 14, 'target': 75.0}  # 100% (Lab)
        ]

        for att in attendance_seed:
            subj = created_subjects[att['code']]
            rec = AttendanceRecord.query.filter_by(user_id=student.id, subject_id=subj.id).first()
            if not rec:
                rec = AttendanceRecord(
                    user_id=student.id,
                    subject_id=subj.id,
                    conducted_classes=att['conducted'],
                    attended_classes=att['attended'],
                    target_percentage=att['target']
                )
                db.session.add(rec)
            else:
                rec.conducted_classes = att['conducted']
                rec.attended_classes = att['attended']
                rec.target_percentage = att['target']

        db.session.commit()
        print("Attendance records configured.")

        # 4. Examinations (Current Asia/Kolkata countdown items)
        today = get_kolkata_now().date()
        exam_seed = [
            {
                'code': 'CS8501',
                'title': 'Theory of Computation End-Semester Exam',
                'type': 'Semester End Exam',
                'date': today + timedelta(days=7),
                'start': '10:00:00',
                'end': '13:00:00',
                'hall': 'Exam Hall 301, Academic Block'
            },
            {
                'code': 'CS8591',
                'title': 'Computer Networks Model Exam',
                'type': 'Model Exam',
                'date': today + timedelta(days=3),
                'start': '10:00:00',
                'end': '13:00:00',
                'hall': 'Exam Hall 302, Academic Block'
            },
            {
                'code': 'CS8592',
                'title': 'OOAD Internal Assessment 2',
                'type': 'Internal Assessment 2',
                'date': today + timedelta(days=1), # Exam Tomorrow!
                'start': '09:30:00',
                'end': '11:00:00',
                'hall': 'Hall 204, CSE Department'
            },
            {
                'code': 'EC8681',
                'title': 'Microprocessors Lab Viva & Practical Exam',
                'type': 'Lab Exam',
                'date': today, # Exam Day!
                'start': '14:00:00',
                'end': '17:00:00',
                'hall': 'Microprocessors Embedded Lab 1'
            }
        ]

        for ex in exam_seed:
            subj = created_subjects[ex['code']]
            existing_exam = Examination.query.filter_by(subject_id=subj.id, title=ex['title']).first()
            if not existing_exam:
                exam_obj = Examination(
                    subject_id=subj.id,
                    title=ex['title'],
                    exam_type=ex['type'],
                    exam_date=ex['date'],
                    start_time=ex['start'],
                    end_time=ex['end'],
                    hall_number=ex['hall'],
                    status='scheduled',
                    created_by=admin.id
                )
                db.session.add(exam_obj)

        db.session.commit()
        print("Examinations seeded with active countdown dates.")

        # 5. Assignments
        assignment_seed = [
            {
                'code': 'CS8501',
                'title': 'Turing Machine State Diagram & Reducibility Proof',
                'desc': 'Design a two-tape Turing machine deciding language L = {a^n b^n c^n | n >= 1} and formal proof.',
                'deadline': datetime.combine(today + timedelta(days=2), datetime.min.time().replace(hour=23, minute=59)),
                'priority': 'high',
                'status': 'active'
            },
            {
                'code': 'CS8591',
                'title': 'Subnetting and Distance Vector Routing Protocol Simulation',
                'desc': 'Configure a 4-router topology with Bellman-Ford routing in Cisco Packet Tracer.',
                'deadline': datetime.combine(today + timedelta(days=5), datetime.min.time().replace(hour=18, minute=0)),
                'priority': 'medium',
                'status': 'active'
            },
            {
                'code': 'CS8592',
                'title': 'UML Class Diagram & Use Case Analysis for Smart Hospital',
                'desc': 'Construct detailed class diagram with design patterns (Factory, Observer).',
                'deadline': datetime.combine(today + timedelta(days=8), datetime.min.time().replace(hour=23, minute=59)),
                'priority': 'low',
                'status': 'active'
            }
        ]

        for a in assignment_seed:
            subj = created_subjects[a['code']]
            existing_a = Assignment.query.filter_by(subject_id=subj.id, title=a['title']).first()
            if not existing_a:
                assign_obj = Assignment(
                    subject_id=subj.id,
                    title=a['title'],
                    description=a['desc'],
                    deadline=a['deadline'],
                    priority=a['priority'],
                    status=a['status'],
                    created_by=admin.id
                )
                db.session.add(assign_obj)
                db.session.flush()

                # Add initial student tracking status
                stat = StudentAssignmentStatus(
                    user_id=student.id,
                    assignment_id=assign_obj.id,
                    status='in_progress',
                    student_notes='Working on formal state transitions.'
                )
                db.session.add(stat)

        db.session.commit()
        print("Assignments and student progress seeded.")

        # 6. Academic Activities
        activities_seed = [
            {
                'title': 'State-Level AI & Deep Learning Hands-on Workshop',
                'type': 'workshop',
                'desc': 'Intensive 2-day hands-on workshop covering PyTorch, Transformers, and GenAI architecture.',
                'date': datetime.combine(today + timedelta(days=4), datetime.min.time().replace(hour=9, minute=30)),
                'venue': 'Auditorium - Main Block',
                'priority': 'high'
            },
            {
                'title': 'Industrial Guest Lecture: Cloud Native Architectures',
                'type': 'guest_lecture',
                'desc': 'Delivered by Principal Architect from Amazon Web Services on Kubernetes and microservices.',
                'date': datetime.combine(today + timedelta(days=9), datetime.min.time().replace(hour=14, minute=0)),
                'venue': 'CSE Seminar Hall 1',
                'priority': 'medium'
            },
            {
                'title': 'Annual Inter-College Hackathon "HackVortex 2026"',
                'type': 'hackathon',
                'desc': '36-hour hackathon on Sustainable Tech, EdTech, and Healthcare AI solutions with cash prizes.',
                'date': datetime.combine(today + timedelta(days=12), datetime.min.time().replace(hour=8, minute=0)),
                'venue': 'Innovation & Incubation Centre',
                'priority': 'high'
            }
        ]

        for act in activities_seed:
            if not AcademicActivity.query.filter_by(title=act['title']).first():
                act_obj = AcademicActivity(
                    title=act['title'],
                    activity_type=act['type'],
                    description=act['desc'],
                    activity_date=act['date'],
                    venue=act['venue'],
                    priority=act['priority'],
                    status='scheduled',
                    created_by=admin.id
                )
                db.session.add(act_obj)

        db.session.commit()
        print("Academic activities seeded.")

        # 7. Generate Sample Official PDF Documents & Index RAG Chunks
        uploads_dir = os.path.join(backend_path, 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)

        doc1_filename = 'academic_regulations_2026.pdf'
        doc1_path = os.path.join(uploads_dir, doc1_filename)

        doc1_pages = [
            """COLLEGE OF ENGINEERING - OFFICIAL ACADEMIC REGULATIONS 2026
SECTION 1: ATTENDANCE REQUIREMENTS AND RULES
1.1 Minimum Attendance: Every student must secure a minimum of 75% attendance in aggregate across all registered courses in each semester to become eligible to appear for the Semester End Examinations.
1.2 Condonation for Shortage: A student whose attendance falls between 65% and 74.9% may apply for condonation on genuine medical grounds or sanctioned institutional representation. Such application must be accompanied by a valid government medical certificate, endorsed by the Head of Department, approved by the Dean of Academic Affairs, and subject to payment of the prescribed condonation fee of Rs. 1000 per subject.
1.3 Debarment: Students having less than 65% attendance under any circumstances will NOT be permitted to write the semester examinations. They will be declared 'Debarred due to Attendance Shortage' and must re-register and repeat the semester courses when offered next.""",

            """SECTION 2: EXAMINATION, ASSESSMENT, AND GRADING SYSTEM
2.1 Continuous Internal Assessment (CIA): 40% total weightage. Comprises two cycle tests of 100 marks each (converted to 20 marks), two assignments (10 marks), and seminar/quiz participation (10 marks).
2.2 Semester End Examinations (SEE): 60% total weightage. The duration of each theory examination is 3 hours. Minimum passing mark in SEE is 45%, and overall composite passing mark (CIA + SEE) is 50%.
2.3 Letter Grading Scale:
- Grade O (Outstanding): 91 to 100 marks (Grade Point 10)
- Grade A+ (Excellent): 81 to 90 marks (Grade Point 9)
- Grade A (Very Good): 71 to 80 marks (Grade Point 8)
- Grade B+ (Good): 61 to 70 marks (Grade Point 7)
- Grade B (Above Average): 50 to 60 marks (Grade Point 6)
- Grade RA (Re-appearance / Arrear): Less than 50 marks (Grade Point 0). Students obtaining RA must register and appear for the arrear examination in subsequent semesters.""",

            """SECTION 3: REVALUATION, ARREAR EXAMS, AND DISCIPLINARY CODE
3.1 Revaluation & Photocopy of Answer Scripts: Students can apply for transparency / photocopy of evaluated answer scripts within 10 working days from the date of result publication with a fee of Rs. 300 per paper. Revaluation application can be submitted within 7 days of receiving the photocopy with a fee of Rs. 500 per paper to the Controller of Examinations (COE).
3.2 Malpractice Regulations: Any student found possessing unauthorized electronic gadgets, handwritten notes, or communicating during examination will be booked for malpractice. Penalties range from cancellation of all examination papers in the current session to debarment for one academic year.
3.3 Official Inquiries: For official clarification regarding regulations, contact Dean of Academic Affairs at academics@college.edu (Phone: 044-2251-8000) or Controller of Examinations at coe@college.edu (Phone: 044-2251-8001)."""
        ]

        generate_sample_pdf(doc1_path, "Academic Regulations 2026", doc1_pages)

        doc2_filename = 'campus_calendar_and_fees_2026.pdf'
        doc2_path = os.path.join(uploads_dir, doc2_filename)

        doc2_pages = [
            """COLLEGE OF ENGINEERING - ACADEMIC CALENDAR & FEE SCHEDULE 2026-2027
SECTION 1: TUITION FEE PAYMENT AND SCHOLARSHIPS
1.1 Semester Fee Due Dates: Odd semester tuition fees must be remitted without fine on or before August 15th. Payments made between August 16th and August 31st incur a late fine of Rs. 500. After August 31st, student portal registration will be suspended.
1.2 First Graduate & Government Scholarships: Eligible candidates must upload their First Graduate Certificate and Income Certificate before September 10th to the Student Welfare Cell.
1.3 Hostel Fee: Hostel room rent and mess fee for each semester must be paid in full before hostel check-in.""",

            """SECTION 2: HOSTEL REGULATIONS AND TIMINGS
2.1 Hostel Curfew: All residential students must return to the hostel premises before 8:30 PM. Daily biometric attendance check takes place strictly at 9:00 PM in the hostel warden office.
2.2 Outing & Gate Pass: Weekend outings or home visits require an e-gate pass requested via the student mobile portal at least 24 hours in advance with parent SMS confirmation.
2.3 Academic Grievance Cell: Contact the Dean of Student Affairs at studentaffairs@college.edu for residential or scholarship inquiries."""
        ]

        generate_sample_pdf(doc2_path, "Campus Calendar and Fees 2026", doc2_pages)

        # Index Document 1 in DB
        doc1 = AcademicDocument.query.filter_by(file_name=doc1_filename).first()
        if not doc1:
            doc1 = AcademicDocument(
                title="Official Academic Regulations & Examination Rules 2026",
                category="curriculum",
                file_name=doc1_filename,
                file_path=doc1_path,
                file_size_bytes=os.path.getsize(doc1_path),
                is_active=True,
                total_pages=len(doc1_pages),
                total_chunks=len(doc1_pages),
                language="en",
                description="Comprehensive Anna University and Autonomous College Academic Regulations including attendance, grading, condonation, and exam revaluation.",
                created_by=admin.id
            )
            db.session.add(doc1)
            db.session.flush()

            for idx, content in enumerate(doc1_pages):
                sec_match = content.split('\n')[1] if '\n' in content else f"Page {idx+1}"
                chunk = DocumentChunk(
                    document_id=doc1.id,
                    chunk_index=idx,
                    page_number=idx + 1,
                    section_title=sec_match,
                    content=content,
                    content_length=len(content)
                )
                db.session.add(chunk)

        # Index Document 2 in DB
        doc2 = AcademicDocument.query.filter_by(file_name=doc2_filename).first()
        if not doc2:
            doc2 = AcademicDocument(
                title="Campus Calendar, Hostel Rules & Fee Schedule 2026-2027",
                category="academic_calendar",
                file_name=doc2_filename,
                file_path=doc2_path,
                file_size_bytes=os.path.getsize(doc2_path),
                is_active=True,
                total_pages=len(doc2_pages),
                total_chunks=len(doc2_pages),
                language="en",
                description="Campus rules, fee deadlines, late payment fines, scholarship procedures, and hostel curfew guidelines.",
                created_by=admin.id
            )
            db.session.add(doc2)
            db.session.flush()

            for idx, content in enumerate(doc2_pages):
                sec_match = content.split('\n')[1] if '\n' in content else f"Page {idx+1}"
                chunk = DocumentChunk(
                    document_id=doc2.id,
                    chunk_index=idx,
                    page_number=idx + 1,
                    section_title=sec_match,
                    content=content,
                    content_length=len(content)
                )
                db.session.add(chunk)

        db.session.commit()
        print("Academic PDFs generated and RAG chunks indexed in database.")

        # 8. Study Plan & Tasks
        plan = StudyPlan.query.filter_by(user_id=student.id).first()
        if not plan:
            plan = StudyPlan(
                user_id=student.id,
                title="Final Semester Preparation Strategy",
                plan_type="weekly",
                start_date=today,
                end_date=today + timedelta(days=6),
                target_hours_per_day=3.5,
                completion_percentage=33.3
            )
            db.session.add(plan)
            db.session.flush()

            tasks_data = [
                {
                    'title': 'Revise Turing Machine Decidability & Halting Problem',
                    'subject_id': created_subjects['CS8501'].id,
                    'est': 60,
                    'priority': 'high',
                    'date': today,
                    'time': '17:00:00',
                    'completed': True
                },
                {
                    'title': 'Solve Distance Vector Routing Matrix Questions',
                    'subject_id': created_subjects['CS8591'].id,
                    'est': 45,
                    'priority': 'high',
                    'date': today + timedelta(days=1),
                    'time': '18:15:00',
                    'completed': False
                },
                {
                    'title': 'Practice UML Sequence Diagrams for Payment Gateway',
                    'subject_id': created_subjects['CS8592'].id,
                    'est': 45,
                    'priority': 'medium',
                    'date': today + timedelta(days=2),
                    'time': '19:30:00',
                    'completed': False
                }
            ]

            for td in tasks_data:
                t_obj = StudyTask(
                    plan_id=plan.id,
                    user_id=student.id,
                    subject_id=td['subject_id'],
                    title=td['title'],
                    estimated_minutes=td['est'],
                    priority=td['priority'],
                    scheduled_date=td['date'],
                    start_time=td['time'],
                    is_completed=td['completed'],
                    completed_at=datetime.utcnow() if td['completed'] else None
                )
                db.session.add(t_obj)

        db.session.commit()
        print("Study plan and tasks seeded.")

        # 9. Focus Sessions
        if FocusSession.query.filter_by(user_id=student.id).count() == 0:
            fs1 = FocusSession(
                user_id=student.id,
                subject_id=created_subjects['CS8501'].id,
                duration_minutes=25,
                break_minutes=5,
                actual_focused_seconds=1500,
                session_status='completed',
                started_at=datetime.utcnow() - timedelta(hours=2),
                ended_at=datetime.utcnow() - timedelta(hours=1, minutes=35),
                notes='Covered Chomsky Normal Form conversions.'
            )
            fs2 = FocusSession(
                user_id=student.id,
                subject_id=created_subjects['CS8591'].id,
                duration_minutes=30,
                break_minutes=5,
                actual_focused_seconds=1800,
                session_status='completed',
                started_at=datetime.utcnow() - timedelta(hours=4),
                ended_at=datetime.utcnow() - timedelta(hours=3, minutes=25),
                notes='Solved CIDR prefix addressing calculations.'
            )
            db.session.add_all([fs1, fs2])
            db.session.commit()
            print("Focus study sessions recorded.")

        # 10. Notifications and Smart Alerts Check
        from services.scheduler_service import check_and_deliver_academic_alerts
        check_and_deliver_academic_alerts(app)
        print("Initial smart academic alerts executed and delivered.")

        print("\n=== DEMO DATA SEEDING COMPLETE ===")
        print("Admin:   email: admin@college.edu   password: Admin@123")
        print("Student: email: student@college.edu password: Student@123")

if __name__ == '__main__':
    seed_database()
