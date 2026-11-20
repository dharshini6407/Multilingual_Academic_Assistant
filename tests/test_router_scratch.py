import re

def detect_query_intent(query: str) -> str:
    if not query:
        return 'DOCUMENT_RAG'
    q = query.lower().strip()

    regulation_patterns = [
        r'\bminimum attendance\b',
        r'\battendance (?:requirement|rule|policy|criteria|norm|regulations?)\b',
        r'\b(?:rules?|regulations?|policy)\b.*\battendance\b',
        r'\bcondonation\b',
        r'\bdebar(?:red|ment)?\b',
        r'\brevaluation\b',
        r'\breval\b',
        r'\bphotocopy\b',
        r'\bmalpractice\b',
        r'\bhandbook\b',
        r'\bpassing marks?\b',
        r'\bgrading (?:scale|system)\b',
        r'\bletter grades?\b',
        r'\bgrade points?\b',
        r'\bcia weightage\b',
        r'\bcurfew\b',
        r'\bhostel rules?\b',
        r'\bscholarship\b',
        r'\blate fees?\b',
        r'\bfees? structure\b',
        r'\bfees? due\b',
        r'\btuition fees?\b',
        r'\bevalo percentage irukkanum\b',
        r'\bevlo percentage irukkanum\b',
        r'\bpercentage irukkanum\b',
        r'\battendance irukkanum\b',
        r'விதி',
        r'விதிகள்'
    ]
    if any(re.search(pat, q) for pat in regulation_patterns):
        return 'DOCUMENT_RAG'

    exam_terms = [
        'exam', 'exams', 'examination', 'examinations', 'test', 'tests',
        'assessment', 'assessments', 'timetable', 'தேர்வு', 'தேர்வுகள்', 'பரீட்சை'
    ]
    has_exam_term = any(re.search(r'\b' + re.escape(w) + r'\b', q) for w in exam_terms)
    has_specific_exam_name = bool(re.search(r'\b(microprocessor|microcontroller|networks lab|theory of computation|ooad)\b', q)) and bool(re.search(r'\b(exam|test|hall|venue|conducted|where|date|time)\b', q))

    if has_exam_term or has_specific_exam_name:
        if any(w in q for w in ['malpractice', 'revaluation fee', 'reval', 'photocopy fee', 'passing mark']):
            return 'DOCUMENT_RAG'
        return 'EXAMS'

    attendance_terms = ['attendance', 'present', 'absent', 'வருகை']
    if any(w in q for w in attendance_terms):
        return 'ATTENDANCE'

    if bool(re.search(r'\b(percentage|evlo|evalo)\b.*\b(irukku|iruku)\b', q)):
        return 'ATTENDANCE'

    subject_terms = ['subject', 'subjects', 'course', 'courses', 'paper', 'papers', 'பாடம்', 'பாடங்கள்']
    if any(re.search(r'\b' + re.escape(w) + r'\b', q) for w in subject_terms):
        if any(w in q for w in ['syllabus pdf', 'download syllabus', 'study material', 'unit 1', 'unit 2', 'notes']):
            return 'DOCUMENT_RAG'
        return 'SUBJECTS'

    return 'DOCUMENT_RAG'

tests = [
    ('How much attendance percentage do I have?', 'ATTENDANCE'),
    ('How many subjects do I have this semester?', 'SUBJECTS'),
    ('What exam do I have today?', 'EXAMS'),
    ('Where will my Microprocessor Lab exam be conducted?', 'EXAMS'),
    ('Which examinations have I completed?', 'EXAMS'),
    ('What is the minimum attendance requirement?', 'DOCUMENT_RAG'),
    ('Enakku evlo attendance irukku?', 'ATTENDANCE'),
    ('Naalaiku enna exam?', 'EXAMS'),
    ('attendance 70% irundha condonation apply panna mudiyuma fee evalo?', 'DOCUMENT_RAG'),
    ('What is the procedure and timeline to apply for revaluation of exam answer sheets?', 'DOCUMENT_RAG'),
    ('semester fee eppo kattanum late fee fine evalo aagum?', 'DOCUMENT_RAG'),
    ('evlo attendance irukkanum?', 'DOCUMENT_RAG'),
    ('What is my attendance?', 'ATTENDANCE'),
    ('Where is my exam?', 'EXAMS'),
    ('When is my next exam?', 'EXAMS'),
    ('What are my subjects?', 'SUBJECTS')
]

all_passed = True
for query, expected in tests:
    res = detect_query_intent(query)
    status = 'PASS' if res == expected else 'FAIL'
    if res != expected:
        all_passed = False
    print(f'[{status}] Query: "{query}" -> Got: {res}, Expected: {expected}')
print('ALL PASSED:', all_passed)
