# Multilingual Academic Information Assistant - API Documentation

This document describes all RESTful API endpoints provided by the backend Flask server.

- **Base URL:** `http://localhost:5000/api`
- **Default Timezone:** `Asia/Kolkata` (IST, UTC+05:30)
- **Supported Content Types:** `application/json`, `multipart/form-data` (file uploads)
- **Supported Languages:** English (`en`), Tamil (`ta`), Tanglish (`tanglish`)

---

## 1. Authentication & Security

All protected endpoints require an HTTP `Authorization` header containing a valid JSON Web Token (JWT):

```http
Authorization: Bearer <your_jwt_access_token>
```

### Standard Error Responses

```json
{
  "error": "Error description message",
  "status": 400
}
```

Common HTTP status codes:
- `200 OK`: Successful request.
- `201 Created`: Resource successfully created.
- `400 Bad Request`: Validation failure or missing required fields.
- `401 Unauthorized`: Missing, expired, or invalid JWT.
- `403 Forbidden`: Admin role required, or ownership violation.
- `404 Not Found`: Requested resource does not exist.
- `409 Conflict`: Unique constraint violation (e.g. duplicate email/register number).
- `500 Internal Server Error`: Unhandled server exception.

---

## 2. Authentication Endpoints (`/api/auth`)

### `POST /api/auth/register`
Register a new student account.
- **Access:** Public
- **Request Body:**
```json
{
  "name": "Jane Doe",
  "email": "jane@college.edu",
  "password": "Password@123",
  "register_number": "REG2024099",
  "department": "Computer Science & Engineering",
  "semester": 6,
  "language_pref": "en"
}
```
- **Response (201 Created):**
```json
{
  "message": "User registered successfully",
  "token": "eyJhbGciOi...",
  "user": {
    "id": 2,
    "name": "Jane Doe",
    "email": "jane@college.edu",
    "role": "student",
    "language_pref": "en",
    "department": "Computer Science & Engineering",
    "semester": 6,
    "register_number": "REG2024099"
  }
}
```

### `POST /api/auth/login`
Authenticate an existing user.
- **Access:** Public
- **Request Body:**
```json
{
  "email": "student@college.edu",
  "password": "Student@123"
}
```
- **Response (200 OK):**
```json
{
  "token": "eyJhbGciOi...",
  "user": {
    "id": 2,
    "name": "Kavitha R",
    "email": "student@college.edu",
    "role": "student",
    "language_pref": "en",
    "department": "Computer Science & Engineering",
    "semester": 6,
    "register_number": "CSE2024001"
  }
}
```

### `GET /api/auth/profile`
Retrieve the current authenticated user's profile details.
- **Access:** Authenticated (Student or Admin)
- **Response (200 OK):** User profile object.

### `PUT /api/auth/profile`
Update personal details and language preferences.
- **Access:** Authenticated
- **Request Body:**
```json
{
  "name": "Kavitha R",
  "department": "Computer Science & Engineering",
  "semester": 6,
  "language_pref": "ta"
}
```

### `POST /api/auth/change-password`
Change current user's password with old password verification.
- **Access:** Authenticated
- **Request Body:**
```json
{
  "current_password": "OldPassword@123",
  "new_password": "NewPassword@123"
}
```

---

## 3. Student Dashboard (`/api/dashboard`)

### `GET /api/dashboard/summary`
Retrieves live calculated academic statistics directly from the database (no hardcoded placeholders).
- **Access:** Authenticated
- **Response (200 OK):**
```json
{
  "attendance": {
    "overall_percentage": 78.43,
    "total_conducted": 153,
    "total_attended": 120,
    "target_percentage": 75.0,
    "warning": false,
    "status": "Good Standing"
  },
  "upcoming_exams": [
    {
      "id": 1,
      "subject_name": "Operating Systems",
      "exam_name": "Semester Final Exam",
      "exam_date": "2026-10-24T09:30:00",
      "days_left": 0,
      "countdown_label": "Exam Day! 🎓"
    }
  ],
  "pending_assignments": [
    {
      "id": 1,
      "title": "Virtual Memory Simulation",
      "subject_name": "Operating Systems",
      "due_date": "2026-10-27T23:59:59",
      "priority": "high",
      "is_overdue": false
    }
  ],
  "upcoming_activities": [
    {
      "id": 1,
      "title": "Hackathon 2026",
      "activity_date": "2026-10-31T09:00:00",
      "category": "technical"
    }
  ],
  "study_planner_progress": {
    "total_tasks": 6,
    "completed_tasks": 2,
    "completion_percentage": 33.33,
    "remaining_minutes": 240
  },
  "focus_summary": {
    "today_minutes": 45,
    "week_minutes": 310
  },
  "recent_notifications": [ ... ]
}
```

---

## 4. Attendance Management (`/api/attendance`)

### `GET /api/attendance/`
Retrieve subject-wise and aggregated attendance.
- **Access:** Authenticated
- **Response (200 OK):**
```json
{
  "overall_percentage": 78.43,
  "total_conducted": 153,
  "total_attended": 120,
  "target_percentage": 75.0,
  "subjects": [
    {
      "subject_id": 1,
      "subject_code": "CS8501",
      "subject_name": "Operating Systems",
      "conducted_classes": 30,
      "attended_classes": 25,
      "percentage": 83.33,
      "status": "safe",
      "classes_needed_for_target": 0,
      "cushion_classes": 3
    }
  ]
}
```

### `POST /api/attendance/target`
Set user's target attendance threshold (e.g. 75% or 80%).
- **Request Body:** `{"target_percentage": 80.0}`

### `POST /api/attendance/simulate`
Simulate "what-if" attendance scenarios.
- **Request Body:**
```json
{
  "subject_id": 1,
  "future_classes": 10,
  "predicted_attended": 8
}
```

### `POST /api/attendance/record`
Admin or student log for conducted and attended classes.
- **Request Body:**
```json
{
  "subject_id": 1,
  "conducted_classes": 32,
  "attended_classes": 27
}
```

---

## 5. Examination Calendar & Smart Alerts (`/api/exams`)

### `GET /api/exams/`
List examinations with calendar-day countdowns in `Asia/Kolkata`.
- **Query Params:** `include_cancelled=false`
- **Response (200 OK):**
```json
[
  {
    "id": 1,
    "subject_id": 1,
    "subject_code": "CS8501",
    "subject_name": "Operating Systems",
    "exam_name": "End Semester Theory",
    "exam_date": "2026-10-24T09:30:00",
    "hall_number": "Mech Lab 202",
    "status": "scheduled",
    "days_left": 0,
    "countdown_label": "Exam Day! 🎓",
    "urgency": "critical"
  }
]
```

### `POST /api/exams/`
Create a new examination schedule.
- **Access:** Admin only
- **Request Body:**
```json
{
  "subject_id": 2,
  "exam_name": "Mid-Term Assessment 2",
  "exam_date": "2026-11-05T10:00:00",
  "duration_minutes": 90,
  "hall_number": "Audi 3",
  "syllabus_topics": "Unit 3 & Unit 4"
}
```

### `PUT /api/exams/<id>`
Update or reschedule an exam (automatically updates countdowns and emits rescheduling notification alerts).
- **Access:** Admin only

### `DELETE /api/exams/<id>`
Cancel an exam (marks status as `cancelled` and alerts affected students).
- **Access:** Admin only

### `POST /api/exams/smart-alerts/check`
Trigger evaluation of smart academic alerts (7-day, 3-day, 1-day, and exam-day exact alerts).
- **Access:** Authenticated / Scheduler

---

## 6. Assignments & Activities (`/api/assignments`, `/api/activities`)

### `GET /api/assignments/`
Get assignments with status (`pending`, `completed`, `submitted`, `overdue`).
- **Query Params:** `filter=pending` or `filter=all`

### `POST /api/assignments/`
Create an assignment (Admin).

### `PUT /api/assignments/<id>/toggle`
Mark student assignment completion state.

### `GET /api/activities/`
List academic events, symposia, guest lectures, and hackathons.

### `POST /api/activities/`
Create academic activity (Admin).

---

## 7. Personalized Study Planner (`/api/planner`)

### `GET /api/planner/tasks`
Fetch study tasks with deadlines, duration estimates, priority, and progress.

### `POST /api/planner/tasks`
Add a custom study task.
- **Request Body:**
```json
{
  "subject_id": 1,
  "title": "Review Deadlock Prevention Algorithms",
  "estimated_minutes": 60,
  "priority": "high",
  "deadline": "2026-10-26T20:00:00"
}
```

### `POST /api/planner/generate`
Generate an automated, conflict-free study schedule based on transparent algorithmic rules (weights: exam urgency 40%, deadline proximity 30%, task priority 20%, subject attendance deficit 10%).
- **Request Body:**
```json
{
  "daily_available_minutes": 180,
  "preferred_slot": "evening",
  "days_to_plan": 7
}
```
- **Response (200 OK):** Generated schedule organized by date with prioritized tasks and recommended breaks.

---

## 8. Focus Timer (`/api/timer`)

### `GET /api/timer/sessions`
Get focus session history, total productive study hours, and daily streak.

### `POST /api/timer/sessions`
Record a completed focus block (ensuring paused time is subtracted).
- **Request Body:**
```json
{
  "subject_id": 1,
  "task_id": 3,
  "duration_minutes": 25,
  "break_minutes": 5,
  "completed": true,
  "started_at": "2026-10-24T14:00:00",
  "ended_at": "2026-10-24T14:25:00"
}
```

---

## 9. Notification Center (`/api/notifications`)

### `GET /api/notifications/`
List student notifications with delivery status, category, unread count.

### `PUT /api/notifications/<id>/read`
Mark a single notification as read.

### `POST /api/notifications/mark-all-read`
Mark all notifications for the authenticated student as read.

### `GET /api/notifications/preferences` & `PUT /api/notifications/preferences`
Inspect and update smart alert settings (e.g., 7-day, 3-day, 1-day, exam-day, assignment reminders).

---

## 10. Documents & RAG Corpus (`/api/documents`)

### `GET /api/documents/`
List uploaded academic documents (regulations, syllabi, circulars, exam manuals).
- **Access:** Authenticated

### `POST /api/documents/upload`
Upload official PDF documents and trigger background extraction and indexing.
- **Access:** Admin only
- **Content-Type:** `multipart/form-data`
- **Fields:** `file` (PDF file), `title`, `category`, `description`

### `DELETE /api/documents/<id>`
Deactivate or delete document and exclude its chunks from retrieval index.
- **Access:** Admin only

### `POST /api/documents/reindex`
Rebuild the TF-IDF vector corpus and chunk index from all active documents.
- **Access:** Admin only

---

## 11. Multilingual Academic Chatbot (`/api/chat`)

### `POST /api/chat/message`
Query the academic assistant in English, Tamil (தமிழ்), or Tanglish.
- **Request Body:**
```json
{
  "conversation_id": null,
  "message": "What is the minimum attendance percentage required for semester exams?",
  "language": "en"
}
```
- **Example Response (Official Retrieval with Citations):**
```json
{
  "conversation_id": 1,
  "response": "According to the official Academic Regulations 2024, students must maintain a minimum of 75% attendance in each registered course to be eligible to appear for semester end examinations. Students with attendance between 65% and 74% due to medical reasons or approved sports representation may apply for condonation subject to institutional committee approval.",
  "citations": [
    {
      "document_name": "Academic_Regulations_2024.pdf",
      "page_number": 1,
      "snippet": "Clause 4.1 Attendance Requirements: A student shall be permitted to appear for the semester end examinations only if he/she secures not less than 75% attendance..."
    }
  ],
  "detected_language": "en",
  "confidence": 0.88
}
```

- **Example Response (Tanglish Query):**
```json
{
  "conversation_id": 1,
  "response": "Attendance requirement pathi kekkareenga: Official Academic Regulations padi, ovvoru subject-layum minimum 75% attendance kandippa thevai. Medical reasons irundha 65% to 74% kulla condonation apply pannalaam.",
  "citations": [
    {
      "document_name": "Academic_Regulations_2024.pdf",
      "page_number": 1
    }
  ],
  "detected_language": "tanglish"
}
```

- **Example Response (Zero-Hallucination Fallback when ungrounded):**
```json
{
  "conversation_id": 1,
  "response": "I could not find official information regarding this topic in the uploaded institutional documents. To avoid inaccurate information, please contact the Office of the Controller of Examinations (coe@college.edu) or Academic Affairs Dean Office.",
  "citations": [],
  "detected_language": "en",
  "is_fallback": true
}
```

### `GET /api/chat/conversations`
List previous conversation sessions for the authenticated user.

### `GET /api/chat/conversations/<id>`
Retrieve message history for a conversation.

### `POST /api/chat/feedback`
Submit helpful / unhelpful rating with optional comments.

---

## 12. Admin Management (`/api/admin`)

- `GET /api/admin/users`: List all students and staff.
- `PUT /api/admin/users/<id>/role`: Change user role (`student` <-> `admin`).
- `GET /api/admin/subjects` & `POST /api/admin/subjects`: Manage course catalog.
- `GET /api/admin/unanswered-questions`: Review chatbot queries that triggered fallback, allowing admins to upload relevant circulars.
- `GET /api/admin/reminders/status`: View scheduler log and notification delivery statistics.
