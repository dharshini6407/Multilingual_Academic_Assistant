import os
import pytest
from services.rag_service import detect_language, generate_rag_answer, retrieve_relevant_chunks
from services.pdf_service import extract_text_and_chunks_from_pdf
from models import AcademicDocument, DocumentChunk, User, Subject, AttendanceRecord, Examination
from db import db

def test_language_detection():
    # Pure English
    assert detect_language("What is the minimum attendance requirement?") == 'en'
    
    # Tamil script
    assert detect_language("தேர்வு எப்போது தொடங்கும்?") == 'ta'
    assert detect_language("வருகை சதவீதம் எவ்வளவு வேண்டும்?") == 'ta'
    
    # Tanglish (Tamil in Latin alphabet)
    assert detect_language("exam eppo start aagum attendance evalo irukkanum?") == 'tanglish'
    assert detect_language("sem fee eppo kattanum solunga?") == 'tanglish'

def test_rag_with_citations_and_fallback(app):
    with app.app_context():
        # Insert test academic document and chunks
        doc = AcademicDocument(
            title="College Regulations 2026",
            file_name="regulations.pdf",
            file_path="dummy.pdf",
            is_active=True
        )
        db.session.add(doc)
        db.session.flush()

        chunk1 = DocumentChunk(
            document_id=doc.id,
            chunk_index=0,
            page_number=4,
            section_title="Attendance Regulations",
            content="Students must maintain a minimum of 75 percent attendance to appear for semester end examinations."
        )
        db.session.add(chunk1)
        db.session.commit()

        # Query in English
        res_en = generate_rag_answer("What is the minimum attendance percentage?")
        assert res_en['is_supported_by_docs'] is True
        assert len(res_en['sources']) > 0
        assert res_en['sources'][0]['document_name'] == "College Regulations 2026"
        assert res_en['sources'][0]['page_number'] == 4
        assert res_en['is_fallback'] is True # Since no AI API key is configured

        # Query in Tanglish
        res_tang = generate_rag_answer("attendance evalo percentage irukkanum?")
        assert res_tang['detected_language'] == 'tanglish'
        assert res_tang['is_supported_by_docs'] is True

def test_unsupported_query_department_contact_fallback(app):
    with app.app_context():
        student = User.query.filter_by(role='student').first()
        res = generate_rag_answer("Can students fly hot air balloons from hostel terrace?", user_id=student.id)
        
        # Verify it does NOT invent facts
        assert res['is_supported_by_docs'] is False
        assert len(res['sources']) == 0
        # Verify it directs user to official department contacts
        assert "Dean of Academic Affairs" in res['answer'] or "Controller of Examinations" in res['answer']

def test_pdf_processing_failures(tmp_path):
    # Test 1: Non-existent file
    with pytest.raises(FileNotFoundError):
        extract_text_and_chunks_from_pdf(str(tmp_path / "nonexistent.pdf"))

    # Test 2: Empty (0 bytes) file
    empty_pdf = tmp_path / "empty.pdf"
    empty_pdf.write_bytes(b"")
    with pytest.raises(ValueError, match="empty"):
        extract_text_and_chunks_from_pdf(str(empty_pdf))

    # Test 3: Corrupt PDF file
    corrupt_pdf = tmp_path / "corrupt.pdf"
    corrupt_pdf.write_bytes(b"NOT A REAL PDF HEADER JUST GARBAGE BYTES")
    with pytest.raises(ValueError, match="PDF processing failed"):
        extract_text_and_chunks_from_pdf(str(corrupt_pdf))

def test_personal_attendance_query_routing(app):
    with app.app_context():
        student = User.query.filter_by(role='student').first()
        sub = Subject.query.first()
        att = AttendanceRecord(
            user_id=student.id,
            subject_id=sub.id,
            conducted_classes=40,
            attended_classes=32,
            target_percentage=75.0
        )
        db.session.add(att)
        db.session.commit()

        # English personal query
        res1 = generate_rag_answer("What is my attendance percentage?", user_id=student.id)
        assert res1['detected_language'] == 'en'
        assert "80.0%" in res1['answer']
        assert "32" in res1['answer'] and "40" in res1['answer']
        assert res1['sources'][0]['document_name'] == 'Live Attendance Database'

        # Tanglish personal query
        res2 = generate_rag_answer("En attendance percentage evlo?", user_id=student.id)
        assert res2['detected_language'] == 'tanglish'
        assert "80.0%" in res2['answer']

def test_enrolled_subjects_query_routing(app):
    with app.app_context():
        student = User.query.filter_by(role='student').first()
        # English query
        res1 = generate_rag_answer("How many subjects do I have this semester?", user_id=student.id)
        assert res1['detected_language'] == 'en'
        assert "CS9999" in res1['answer']
        assert "Test Autonomous Computing" in res1['answer']

        # Tanglish query
        res2 = generate_rag_answer("Indha sem la enaku ethana subject irukku?", user_id=student.id)
        assert res2['detected_language'] == 'tanglish'
        assert "CS9999" in res2['answer']

def test_exam_schedule_query_routing_tomorrow(app):
    from datetime import timedelta
    from services.scheduler_service import get_kolkata_now
    from models import Examination

    with app.app_context():
        student = User.query.filter_by(role='student').first()
        sub = Subject.query.first()
        tomorrow = get_kolkata_now().date() + timedelta(days=1)

        exam = Examination(
            subject_id=sub.id,
            title="Advanced Autonomous Systems Exam",
            exam_type="Semester End Exam",
            exam_date=tomorrow,
            start_time="10:00:00",
            end_time="13:00:00",
            hall_number="Hall 404, Tech Park",
            max_marks=100,
            status="scheduled",
            created_by=1
        )
        db.session.add(exam)
        db.session.commit()

        # Tanglish query
        res_tang = generate_rag_answer("Naalaiku enaku enna exam?", user_id=student.id)
        assert res_tang['detected_language'] == 'tanglish'
        assert "Advanced Autonomous Systems Exam" in res_tang['answer']
        assert "Hall 404, Tech Park" in res_tang['answer']
        assert tomorrow.strftime('%Y-%m-%d') in res_tang['answer']

        # English query
        res_en = generate_rag_answer("Which exam do I have tomorrow?", user_id=student.id)
        assert res_en['detected_language'] == 'en'
        assert "Advanced Autonomous Systems Exam" in res_en['answer']
        assert "10:00:00 - 13:00:00" in res_en['answer']

def test_missing_records_handling_without_fabrication(app):
    from services.scheduler_service import get_kolkata_now
    with app.app_context():
        # User with no attendance
        admin = User.query.filter_by(role='admin').first()
        res_att = generate_rag_answer("What is my attendance percentage?", user_id=admin.id)
        assert "No attendance records were found" in res_att['answer']

        # Date with no exam
        student = User.query.filter_by(role='student').first()
        # Delete any examinations to guarantee none scheduled for tomorrow
        from models import Examination
        Examination.query.delete()
        db.session.commit()

        res_exam = generate_rag_answer("Which exam do I have tomorrow?", user_id=student.id)
        assert "no examinations scheduled for tomorrow" in res_exam['answer'].lower()
