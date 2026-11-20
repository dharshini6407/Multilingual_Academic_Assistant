import re
import logging
from datetime import timedelta
from typing import List, Dict, Any, Tuple
from config import Config
from db import db
from models import (
    AcademicDocument, DocumentChunk, UnansweredQuestion,
    User, Subject, AttendanceRecord, Examination
)
from services.attendance_service import calculate_attendance_metrics
from services.scheduler_service import get_kolkata_now, calculate_exam_countdown

logger = logging.getLogger(__name__)

# Common Tanglish marker words (strictly regional / colloquial markers, excluding pure English terms)
TANGLISH_KEYWORDS = {
    'eppo', 'enna', 'irukku', 'irukkanum', 'panrathu', 'solunga',
    'theriyuma', 'kudunga', 'mudiyuma', 'illai', 'illa', 'enga',
    'romba', 'evalo', 'evvalavu', 'aagum', 'kattum', 'varuma',
    'ethana', 'kaatunga', 'pathi', 'solla', 'epdi', 'yaarukku',
    'venum', 'aachu', 'pannalaama', 'theriyala', 'solreengala',
    'nalaiku', 'naalaiku', 'naalai', 'nalai', 'inniku', 'indru', 'netru',
    'evlo', 'eppadi', 'irukka', 'pannu', 'pannunga', 'sollu', 'yen',
    'enakku', 'enaku', 'ennaku', 'unakku', 'ungalukku', 'ennoda',
    'mudiyum', 'mudiyathu', 'venam', 'epothu', 'varala', 'padikren'
}

# Cross-lingual vocabulary expansion for Tanglish & Tamil academic queries
CROSS_LINGUAL_MAPPINGS = {
    'attendance': ['attendance', 'present', 'absent', 'percentage', 'condonation', 'shortage'],
    'varala': ['absent', 'attendance', 'leave'],
    'leave': ['leave', 'absence', 'medical certificate', 'permission'],
    'exam': ['examination', 'exam', 'assessment', 'schedule', 'timetable', 'hall ticket'],
    'arrear': ['arrear', 'reappear', 'supplementary', 'backlog', 'clearing'],
    'mark': ['marks', 'grade', 'cgpa', 'sgpa', 'internal', 'external', 'credits'],
    'grade': ['grading system', 'grade point', 'letter grade', 'classification'],
    'fee': ['fees', 'tuition', 'payment', 'due date', 'fine', 'scholarship'],
    'syllabus': ['curriculum', 'syllabus', 'course structure', 'credits', 'prerequisites'],
    'hall': ['hall ticket', 'admit card', 'examination hall', 'room'],
    'reval': ['revaluation', 'photocopy', 're-totalling', 'review'],
    'malpractice': ['malpractice', 'disciplinary', 'misconduct', 'penalties'],
    'project': ['project work', 'viva voce', 'review', 'dissertation', 'internship'],
    'தேர்வு': ['examination', 'exam', 'assessment'],
    'வருகை': ['attendance', 'percentage', 'classes'],
    'கட்டணம்': ['fee', 'tuition', 'payment'],
    'மதிப்பெண்': ['marks', 'grades', 'credits']
}

def detect_language(query: str) -> str:
    """
    Detect whether text is Tamil (script), Tanglish (Tamil in Latin script), or English.
    """
    if not query:
        return 'en'
    
    # Check for Tamil Unicode range (U+0B80 to U+0BFF)
    tamil_char_count = len(re.findall(r'[\u0B80-\u0BFF]', query))
    if tamil_char_count > 0:
        return 'ta'

    # Check for Tanglish words in lowercased tokenized text
    clean_words = set(re.findall(r'[a-zA-Z]+', query.lower()))
    intersection = clean_words.intersection(TANGLISH_KEYWORDS)
    if len(intersection) >= 1:
        return 'tanglish'

    return 'en'

def expand_query_for_retrieval(query: str, detected_lang: str) -> str:
    """
    Expand Tamil / Tanglish queries with relevant English academic keywords
    so that matching against English PDF chunks succeeds with high recall.
    """
    tokens = re.findall(r'[\w]+', query.lower())
    extra_keywords = set()

    for token in tokens:
        for key, synonyms in CROSS_LINGUAL_MAPPINGS.items():
            if key in token or token in key:
                extra_keywords.update(synonyms)

    if extra_keywords:
        return f"{query} {' '.join(extra_keywords)}"
    return query

def retrieve_relevant_chunks(query: str, top_k: int = 4, min_score: float = 0.18) -> List[Dict[str, Any]]:
    """
    Perform hybrid retrieval:
    1. Filter only active academic documents
    2. Compute TF-IDF Cosine Similarity across document chunks
    3. Include exact academic keyword boosting (excluding generic stop-words)
    """
    # Load all active chunks joined with their parent document
    chunks = DocumentChunk.query.join(AcademicDocument).filter(
        AcademicDocument.is_active == True
    ).all()

    if not chunks:
        logger.warning("No active document chunks found in database.")
        return []

    detected_lang = detect_language(query)
    expanded_query = expand_query_for_retrieval(query, detected_lang)

    corpus = [f"{c.section_title or ''} {c.content}" for c in chunks]

    GENERIC_WORDS = {
        'students', 'student', 'college', 'university', 'department', 'campus',
        'academic', 'year', 'per', 'any', 'all', 'the', 'and', 'for', 'with',
        'from', 'this', 'that', 'can', 'will', 'are', 'is', 'how', 'what', 'who'
    }

    scored_chunks = []

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words='english',
            min_df=1,
            sublinear_tf=True
        )
        tfidf_matrix = vectorizer.fit_transform(corpus)
        query_vec = vectorizer.transform([expanded_query])
        scores = cosine_similarity(query_vec, tfidf_matrix).flatten()

        for idx, score in enumerate(scores):
            raw_chunk = chunks[idx]
            final_score = float(score)

            # Specific topical keyword presence bonus (excluding generic stop words)
            query_terms = set(re.findall(r'\b[a-zA-Z]{4,}\b', expanded_query.lower())) - GENERIC_WORDS
            chunk_text_lower = corpus[idx].lower()
            keyword_matches = sum(1 for term in query_terms if term in chunk_text_lower)
            if keyword_matches > 0:
                final_score += 0.08 * min(keyword_matches, 3)

            if final_score >= min_score:
                scored_chunks.append({
                    'chunk_id': raw_chunk.id,
                    'document_id': raw_chunk.document_id,
                    'document_name': raw_chunk.document.title if raw_chunk.document else "Official Academic Regulations",
                    'file_name': raw_chunk.document.file_name if raw_chunk.document else "handbook.pdf",
                    'page_number': raw_chunk.page_number,
                    'section_title': raw_chunk.section_title or f"Section {raw_chunk.chunk_index + 1}",
                    'content': raw_chunk.content,
                    'score': round(final_score, 4)
                })

        scored_chunks.sort(key=lambda x: x['score'], reverse=True)
        return scored_chunks[:top_k]

    except Exception as e:
        logger.error(f"Error in TF-IDF retrieval: {e}")
        # Simple substring search fallback
        fallback_scored = []
        q_lower = query.lower()
        for c in chunks:
            if q_lower in c.content.lower():
                fallback_scored.append({
                    'chunk_id': c.id,
                    'document_id': c.document_id,
                    'document_name': c.document.title if c.document else "Academic Regulation",
                    'file_name': c.document.file_name if c.document else "doc.pdf",
                    'page_number': c.page_number,
                    'section_title': c.section_title,
                    'content': c.content,
                    'score': 0.5
                })
        return fallback_scored[:top_k]

def detect_query_intent(query: str) -> str:
    """
    Detect whether the query intent is:
    - 'ATTENDANCE': Student personal attendance records & calculations
    - 'SUBJECTS': Student enrolled subjects / courses
    - 'EXAMS': Examination schedule, tomorrow's exams, upcoming exams
    - 'DOCUMENT_RAG': General academic regulations, handbooks, condonation rules, revaluation policies, etc.
    """
    if not query:
        return 'DOCUMENT_RAG'

    q = query.lower().strip()

    # Rule 1: High-priority check for general academic regulation terms
    general_regulation_triggers = [
        'condonation', 'debarred', 'debarment', 'revaluation', 'reval',
        'photocopy', 'malpractice', 'handbook', 'passing mark', 'passing marks',
        'grading scale', 'grading system', 'letter grade', 'grade point', 'cia weightage',
        'curfew', 'hostel rule', 'scholarship', 'fine', 'late fee',
        'irukkanum', 'evalo percentage irukkanum', 'minimum attendance', 'விதி', 'விதிகள்'
    ]
    if any(trigger in q for trigger in general_regulation_triggers):
        return 'DOCUMENT_RAG'

    # Rule 2: Personal Attendance queries
    attendance_keywords = ['attendance', 'present', 'absent', 'வருகை']
    has_attendance = any(kw in q for kw in attendance_keywords)
    if has_attendance:
        personal_markers = [
            'my', 'i', 'me', 'have i', 'i have', 'do i', 'mine',
            'en', 'enaku', 'enakku', 'ennaku', 'ennoda', 'irukku', 'iruku', 'evlo', 'evalo',
            'percentage', 'status', 'என்', 'எனக்கு'
        ]
        if any(pm in q.split() or pm in q for pm in personal_markers) or 'how much' in q or 'what is' in q:
            return 'ATTENDANCE'

    # Rule 3: Exam schedule queries
    exam_keywords = ['exam', 'exams', 'examination', 'examinations', 'test', 'tests', 'assessment', 'தேர்வு', 'பரீட்சை']
    has_exam = any(kw in q for kw in exam_keywords)
    if has_exam:
        schedule_markers = [
            'tomorrow', 'tmrw', 'today', 'next', 'upcoming', 'schedule', 'timetable',
            'when', 'date', 'dates', 'time', 'hall', 'naalaiku', 'nalaiku', 'naalai', 'nalai',
            'inniku', 'iniku', 'indru', 'eppo', 'epothu', 'adutha', 'aduthu', 'enna exam',
            'which exam', 'what exam', 'paritsha', 'நாளை', 'நாளைக்கு', 'இன்று', 'எப்போது', 'அடுத்த'
        ]
        if any(sm in q for sm in schedule_markers) or 'when is' in q or 'what is' in q:
            return 'EXAMS'

    # Rule 4: Subject queries
    subject_keywords = ['subject', 'subjects', 'course', 'courses', 'paper', 'papers', 'பாடம்', 'பாடங்கள்']
    has_subject = any(kw in q for kw in subject_keywords)
    if has_subject:
        subject_markers = [
            'how many', 'ethana', 'evlo', 'evalo', 'list', 'what are', 'registered', 'enrolled',
            'this sem', 'this semester', 'indha sem', 'intha sem', 'padikren', 'studying',
            'எத்தனை', 'பாடங்கள்', 'என் பாடம்'
        ]
        if any(sm in q for sm in subject_markers) or 'my' in q or 'en' in q or 'enaku' in q or 'enakku' in q:
            return 'SUBJECTS'

    return 'DOCUMENT_RAG'

def handle_attendance_query(user_id: int, lang: str) -> Dict[str, Any]:
    """Retrieve authenticated student's real attendance from database and calculate metrics."""
    if not user_id:
        msg = "Please log in with your student account to check your attendance records."
        return {
            'answer': msg,
            'detected_language': lang,
            'sources': [],
            'is_fallback': False,
            'is_supported_by_docs': True
        }

    records = AttendanceRecord.query.filter_by(user_id=user_id).all()
    if not records:
        if lang == 'ta':
            msg = "உங்கள் கணக்கிற்கான வருகைப் பதிவுகள் எதுவும் தரவுத்தளத்தில் காணப்படவில்லை. உங்கள் துறை அலுவலகத்தைத் தொடர்பு கொள்ளவும்."
        elif lang == 'tanglish':
            msg = "Ungaloda account-ku attendance records edhum database-la illa. Please department coordinator-a contact pannunga."
        else:
            msg = "No attendance records were found for your account in the database. Please contact your department coordinator."
        return {
            'answer': msg,
            'detected_language': lang,
            'sources': [],
            'is_fallback': False,
            'is_supported_by_docs': True
        }

    total_conducted = sum(r.conducted_classes for r in records)
    total_attended = sum(r.attended_classes for r in records)
    metrics = calculate_attendance_metrics(total_conducted, total_attended, 75.0)

    pct = metrics['percentage']
    cushion = metrics['classes_can_miss']
    needed = metrics['classes_needed']
    status = metrics['status']

    subject_lines = []
    for r in records:
        name = r.subject.name if r.subject else f"Subject {r.subject_id}"
        code = r.subject.code if r.subject else ""
        spct = round((r.attended_classes / r.conducted_classes * 100), 2) if r.conducted_classes > 0 else 100.0
        subject_lines.append(f"  • {code} - {name}: **{spct}%** ({r.attended_classes}/{r.conducted_classes} classes)")

    subj_text = "\n".join(subject_lines)

    if lang == 'ta':
        status_note = f"பாதுகாப்பான நிலை ({cushion} வகுப்புகள் வரை விடுப்பு எடுக்கலாம்)." if cushion > 0 else f"இலக்கை அடைய அடுத்த {needed} வகுப்புகளில் கலந்து கொள்ள வேண்டும்."
        answer = (
            f"📊 **உங்கள் வருகைப் பதிவு விவரம் (Attendance Summary):**\n\n"
            f"• **மொத்த வருகை சதவீதம்:** **{pct}%**\n"
            f"• **வருகை புரிந்த வகுப்புகள்:** {total_attended} / {total_conducted}\n"
            f"• **தேவையான இலக்கு:** 75.0%\n"
            f"• **நிலை:** {status} ({status_note})\n\n"
            f"**பாடவாரியான விவரங்கள்:**\n{subj_text}"
        )
    elif lang == 'tanglish':
        status_note = f"Safety cushion irukku ({cushion} classes miss panninaalum 75% ku kuraivadhu)." if cushion > 0 else f"Target 75% reach panna adutha {needed} classes attend pannanum."
        answer = (
            f"📊 **Unga Overall Attendance Summary:**\n\n"
            f"• **Overall Attendance Percentage:** **{pct}%**\n"
            f"• **Attended / Conducted:** {total_attended} / {total_conducted} classes\n"
            f"• **Target Required:** 75.0%\n"
            f"• **Status:** {status} ({status_note})\n\n"
            f"**Subject-wise Breakdown:**\n{subj_text}"
        )
    else:
        status_note = f"You have a safety cushion of {cushion} class{'es' if cushion != 1 else ''}." if cushion > 0 else f"You need to attend the next {needed} consecutive class{'es' if needed != 1 else ''}."
        answer = (
            f"📊 **Your Official Attendance Summary:**\n\n"
            f"• **Overall Attendance:** **{pct}%**\n"
            f"• **Classes Attended:** {total_attended} of {total_conducted}\n"
            f"• **Target Requirement:** 75.0%\n"
            f"• **Status:** {status} — {status_note}\n\n"
            f"**Subject-wise Attendance:**\n{subj_text}"
        )

    sources = [{
        'document_name': 'Live Attendance Database',
        'file_name': 'attendance_records',
        'page_number': 1,
        'section_title': 'Student Attendance Module',
        'excerpt': f"Overall Attendance: {pct}%, Attended: {total_attended}/{total_conducted} classes."
    }]

    return {
        'answer': answer,
        'detected_language': lang,
        'sources': sources,
        'is_fallback': False,
        'is_supported_by_docs': True
    }

def handle_subjects_query(user_id: int, lang: str) -> Dict[str, Any]:
    """Retrieve authenticated student's enrolled subjects from database."""
    if not user_id:
        msg = "Please log in with your student account to view your enrolled subjects."
        return {
            'answer': msg,
            'detected_language': lang,
            'sources': [],
            'is_fallback': False,
            'is_supported_by_docs': True
        }

    user = db.session.get(User, user_id)
    profile = user.profile if user else None
    att_records = AttendanceRecord.query.filter_by(user_id=user_id).all()

    enrolled_subjects = []
    if att_records:
        for r in att_records:
            if r.subject and r.subject not in enrolled_subjects:
                enrolled_subjects.append(r.subject)
    elif profile:
        enrolled_subjects = Subject.query.filter_by(
            department=profile.department,
            semester=profile.semester
        ).order_by(Subject.code).all()
    else:
        enrolled_subjects = Subject.query.order_by(Subject.code).all()

    if not enrolled_subjects:
        if lang == 'ta':
            msg = "தற்போதைய செமஸ்டருக்கான பாடங்கள் எதுவும் பதிவு செய்யப்படவில்லை."
        elif lang == 'tanglish':
            msg = "Ungaloda current semester-ku enrolled subjects edhum database-la illa."
        else:
            msg = "No enrolled subjects were found for your current semester in the database."
        return {
            'answer': msg,
            'detected_language': lang,
            'sources': [],
            'is_fallback': False,
            'is_supported_by_docs': True
        }

    sem_label = f"Semester {profile.semester}" if profile else "Current Semester"
    dept_label = profile.department if profile else "Engineering"
    count = len(enrolled_subjects)

    subject_lines = []
    for s in enrolled_subjects:
        fac = f" (Faculty: {s.faculty_name})" if s.faculty_name else ""
        subject_lines.append(f"  • **{s.code}** - {s.name} [{s.credits} Credits]{fac}")

    subj_text = "\n".join(subject_lines)

    if lang == 'ta':
        answer = (
            f"📚 **பதிவு செய்யப்பட்ட பாடங்கள் ({sem_label} - {dept_label}):**\n\n"
            f"இந்த செமஸ்டரில் நீங்கள் மொத்தம் **{count} பாடங்கள்** பயில்கிறீர்கள்:\n\n"
            f"{subj_text}"
        )
    elif lang == 'tanglish':
        answer = (
            f"📚 **Enrolled Subjects ({sem_label} - {dept_label}):**\n\n"
            f"Ungalukku indha semester motham **{count} subjects** registered aagi irukku:\n\n"
            f"{subj_text}"
        )
    else:
        answer = (
            f"📚 **Your Enrolled Subjects ({sem_label} - {dept_label}):**\n\n"
            f"You have **{count} subjects** registered this semester:\n\n"
            f"{subj_text}"
        )

    sources = [{
        'document_name': 'Live Academic Curriculum Database',
        'file_name': 'subjects',
        'page_number': 1,
        'section_title': 'Course Registration',
        'excerpt': f"Total Enrolled Courses: {count} subjects for {sem_label}."
    }]

    return {
        'answer': answer,
        'detected_language': lang,
        'sources': sources,
        'is_fallback': False,
        'is_supported_by_docs': True
    }

def handle_exams_query(user_id: int, query: str, lang: str) -> Dict[str, Any]:
    """Retrieve examination calendar data with Asia/Kolkata live schedule matching."""
    now_kolkata = get_kolkata_now()
    today = now_kolkata.date()
    tomorrow = today + timedelta(days=1)
    q = query.lower()

    is_tomorrow = any(w in q for w in ['tomorrow', 'tmrw', 'naalaiku', 'nalaiku', 'naalai', 'nalai', 'நாளை'])
    is_today = any(w in q for w in ['today', 'inniku', 'iniku', 'indru', 'இன்று'])

    if is_tomorrow:
        target_date = tomorrow
        exams = Examination.query.filter(
            Examination.exam_date == target_date,
            Examination.status.in_(['scheduled', 'rescheduled'])
        ).order_by(Examination.start_time.asc()).all()

        date_str = target_date.strftime('%Y-%m-%d')
        if not exams:
            if lang == 'ta':
                msg = f"நாளை ({date_str}) உங்களுக்கு தேர்வுகள் எதுவும் திட்டமிடப்படவில்லை."
            elif lang == 'tanglish':
                msg = f"Naalaiku ({date_str}) ungalukku endha exam-mum schedule aagala."
            else:
                msg = f"You have no examinations scheduled for tomorrow ({date_str})."
            return {
                'answer': msg,
                'detected_language': lang,
                'sources': [],
                'is_fallback': False,
                'is_supported_by_docs': True
            }

        lines = []
        for ex in exams:
            s_code = ex.subject.code if ex.subject else ""
            s_name = ex.subject.name if ex.subject else ex.title
            lines.append(
                f"📝 **{ex.title}**\n"
                f"  • **Subject:** {s_code} - {s_name}\n"
                f"  • **Date:** {ex.exam_date} (Tomorrow)\n"
                f"  • **Time:** {ex.start_time} - {ex.end_time}\n"
                f"  • **Exam Hall:** {ex.hall_number}\n"
                f"  • **Max Marks:** {ex.max_marks}\n"
                f"  • **Status:** {ex.status.capitalize()}"
            )
        exam_body = "\n\n".join(lines)

        if lang == 'ta':
            answer = f"⚡ **நாளை ({date_str}) நடைபெற உள்ள தேர்வு:**\n\n{exam_body}"
        elif lang == 'tanglish':
            answer = f"⚡ **Naalaiku ({date_str}) Ungalukku Irukka Exam Schedule:**\n\n{exam_body}"
        else:
            answer = f"⚡ **Tomorrow's Examination Schedule ({date_str}):**\n\n{exam_body}"

        sources = [{
            'document_name': 'Live Examination Calendar',
            'file_name': 'examinations',
            'page_number': 1,
            'section_title': 'Exam Schedule',
            'excerpt': f"Examination on {date_str}: {exams[0].title} at {exams[0].start_time} in {exams[0].hall_number}."
        }]

        return {
            'answer': answer,
            'detected_language': lang,
            'sources': sources,
            'is_fallback': False,
            'is_supported_by_docs': True
        }

    # Next / upcoming exams
    upcoming_exams = Examination.query.filter(
        Examination.exam_date >= today,
        Examination.status.in_(['scheduled', 'rescheduled'])
    ).order_by(Examination.exam_date.asc(), Examination.start_time.asc()).limit(3).all()

    if not upcoming_exams:
        if lang == 'ta':
            msg = "தற்போது வரவிருக்கும் தேர்வுகள் எதுவும் திட்டமிடப்படவில்லை."
        elif lang == 'tanglish':
            msg = "Ippo schedule aana upcoming exams edhum illa."
        else:
            msg = "There are no upcoming examinations scheduled at this time."
        return {
            'answer': msg,
            'detected_language': lang,
            'sources': [],
            'is_fallback': False,
            'is_supported_by_docs': True
        }

    lines = []
    for ex in upcoming_exams:
        cd = calculate_exam_countdown(ex.exam_date, today)
        rem = cd.get('days_remaining', 0)
        rem_str = "Today" if rem == 0 else ("Tomorrow" if rem == 1 else f"in {rem} days")
        s_code = ex.subject.code if ex.subject else ""
        s_name = ex.subject.name if ex.subject else ex.title
        lines.append(
            f"📝 **{ex.title}** ({rem_str})\n"
            f"  • **Subject:** {s_code} - {s_name}\n"
            f"  • **Date & Time:** {ex.exam_date} ({ex.start_time} - {ex.end_time})\n"
            f"  • **Exam Hall:** {ex.hall_number}"
        )
    exam_body = "\n\n".join(lines)

    if lang == 'ta':
        answer = f"📅 **அடுத்து வரவிருக்கும் தேர்வுகள் அட்டவணை:**\n\n{exam_body}"
    elif lang == 'tanglish':
        answer = f"📅 **Upcoming Examination Schedule:**\n\n{exam_body}"
    else:
        answer = f"📅 **Upcoming Examination Schedule:**\n\n{exam_body}"

    sources = [{
        'document_name': 'Live Examination Calendar',
        'file_name': 'examinations',
        'page_number': 1,
        'section_title': 'Exam Schedule',
        'excerpt': f"Next exam: {upcoming_exams[0].title} on {upcoming_exams[0].exam_date}."
    }]

    return {
        'answer': answer,
        'detected_language': lang,
        'sources': sources,
        'is_fallback': False,
        'is_supported_by_docs': True
    }

def generate_document_rag_answer(query: str, user_id: int = None, lang: str = 'en') -> Dict[str, Any]:
    """Retrieve and format answers from uploaded academic regulations and handbook PDFs."""
    retrieved_chunks = retrieve_relevant_chunks(query)

    # CASE 1: Query not supported by documents -> DO NOT invent information
    if not retrieved_chunks:
        # Record unanswered question for administrator review
        try:
            if user_id:
                unanswered = UnansweredQuestion(
                    user_id=user_id,
                    question=query,
                    detected_language=lang,
                    context_attempted="No matching document chunks exceeded confidence threshold."
                )
                db.session.add(unanswered)
                db.session.commit()
        except Exception as err:
            db.session.rollback()
            logger.error(f"Failed to record unanswered question: {err}")

        if lang == 'ta':
            answer_text = (
                "மன்னிக்கவும், கல்லூரியின் அதிகாரப்பூர்வ ஆவணங்களில் இதற்கான தகவல் கிடைக்கவில்லை. "
                "முறையற்ற தவறான தகவல்களை நாங்கள் வழங்க மாட்டோம்.\n\n"
                f"தயவுசெய்து பின்வரும் அதிகாரப்பூர்வ அலுவலகங்களை தொடர்பு கொள்ளவும்:\n"
                f"• {Config.OFFICIAL_DEPT_CONTACT}\n"
                f"• {Config.COE_CONTACT}"
            )
        elif lang == 'tanglish':
            answer_text = (
                "Mannikavum, college-oda official regulations/handbook-la indha query-kaana direct information illai. "
                "Official rules illadha thappana info-va naanga provide panna maattom.\n\n"
                f"Please contact the respective department directly:\n"
                f"• {Config.OFFICIAL_DEPT_CONTACT}\n"
                f"• {Config.COE_CONTACT}"
            )
        else:
            answer_text = (
                "I apologize, but this information is not available in the official college documents currently on record. "
                "To maintain academic integrity, unofficial answers are not provided.\n\n"
                f"Please consult the relevant department office directly:\n"
                f"• {Config.OFFICIAL_DEPT_CONTACT}\n"
                f"• {Config.COE_CONTACT}"
            )

        return {
            'answer': answer_text,
            'detected_language': lang,
            'sources': [],
            'is_fallback': True,
            'is_supported_by_docs': False
        }

    # Format source citations
    sources = []
    seen_sources = set()
    for rc in retrieved_chunks:
        source_key = (rc['document_name'], rc['page_number'])
        if source_key not in seen_sources:
            seen_sources.add(source_key)
            sources.append({
                'document_name': rc['document_name'],
                'file_name': rc['file_name'],
                'page_number': rc['page_number'],
                'section_title': rc['section_title'],
                'excerpt': rc['content'][:250] + ("..." if len(rc['content']) > 250 else "")
            })

    # CASE 2: External AI API Key configured
    if Config.AI_PROVIDER in ['gemini', 'openai'] and Config.AI_API_KEY:
        try:
            external_answer = call_external_llm(query, retrieved_chunks, lang)
            if external_answer:
                return {
                    'answer': external_answer,
                    'detected_language': lang,
                    'sources': sources,
                    'is_fallback': False,
                    'is_supported_by_docs': True
                }
        except Exception as e:
            logger.warning(f"External LLM invocation failed, reverting to retrieval fallback: {e}")

    # CASE 3: Retrieval-Based Fallback (No AI API key or API call fallback)
    passages_summary = []
    for idx, c in enumerate(retrieved_chunks[:3]):
        sec = f"[{c['section_title']}]" if c['section_title'] else ""
        passages_summary.append(f"• {sec} {c['content']} (Source: {c['document_name']}, Page {c['page_number']})")

    passages_text = "\n\n".join(passages_summary)

    if lang == 'ta':
        header = "📋 **அதிகாரப்பூர்வ கல்லூரி ஆவணங்களிலிருந்து பெறப்பட்ட தகவல்கள்:**\n\n"
        footer = "\n\n*(குறிப்பு: நேரடி ஆவண மீட்டெடுப்பு முறையில் பதிலளிக்கப்படுகிறது)*"
    elif lang == 'tanglish':
        header = "📋 **Official Academic Records-la irundhu edukkappatta verified information:**\n\n"
        footer = "\n\n*(Note: Running in verified official document retrieval mode)*"
    else:
        header = "📋 **Verified Information from Official College Documents:**\n\n"
        footer = "\n\n*(Note: Generated via direct document retrieval mode using official handbook passages)*"

    final_answer = f"{header}{passages_text}{footer}"

    return {
        'answer': final_answer,
        'detected_language': lang,
        'sources': sources,
        'is_fallback': True,
        'is_supported_by_docs': True
    }

def generate_rag_answer(query: str, user_id: int = None) -> Dict[str, Any]:
    """
    Multilingual Academic Chatbot Router:
    1. Detects query language (en, ta, tanglish)
    2. Identifies user intent (Attendance, Enrolled Subjects, Exam Schedule, or Document Regulations)
    3. Routes to appropriate verified database module or PDF document RAG pipeline
    4. Adheres strictly to academic integrity without inventing records
    """
    lang = detect_language(query)
    intent = detect_query_intent(query)

    if intent == 'ATTENDANCE':
        return handle_attendance_query(user_id, lang)
    elif intent == 'SUBJECTS':
        return handle_subjects_query(user_id, lang)
    elif intent == 'EXAMS':
        return handle_exams_query(user_id, query, lang)

    # General Academic Document Regulations RAG
    return generate_document_rag_answer(query, user_id, lang)

def call_external_llm(query: str, chunks: List[Dict[str, Any]], language: str) -> str:
    """Helper to call Gemini or OpenAI when API key is provided."""
    import requests

    context_str = "\n\n".join([
        f"--- Document: {c['document_name']} (Page {c['page_number']}) ---\n{c['content']}"
        for c in chunks
    ])

    lang_instruction = {
        'ta': 'Answer fluently in pure Tamil (தமிழ்). Keep terminology accurate.',
        'tanglish': 'Answer casually in Tanglish (Tamil written in English script, conversational Tamil college student style).',
        'en': 'Answer clearly in English.'
    }.get(language, 'Answer in English.')

    system_prompt = (
        "You are an official college academic assistant. Answer strictly based on the following official college excerpts. "
        "Do not invent facts, deadlines, percentages, or rules not present in the excerpts. "
        "Always cite the source document name and page number for each key statement. "
        f"{lang_instruction}\n\n"
        f"OFFICIAL CONTEXT:\n{context_str}\n\n"
        f"STUDENT QUESTION:\n{query}"
    )

    if Config.AI_PROVIDER == 'gemini':
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={Config.AI_API_KEY}"
        payload = {
            "contents": [{"parts": [{"text": system_prompt}]}]
        }
        res = requests.post(url, json=payload, timeout=12)
        if res.status_code == 200:
            data = res.json()
            return data['candidates'][0]['content']['parts'][0]['text']

    elif Config.AI_PROVIDER == 'openai':
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {Config.AI_API_KEY}"}
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You are an official academic assistant. Adhere strictly to provided context."},
                {"role": "user", "content": system_prompt}
            ],
            "temperature": 0.2
        }
        res = requests.post(url, json=payload, headers=headers, timeout=12)
        if res.status_code == 200:
            data = res.json()
            return data['choices'][0]['message']['content']

    return None
