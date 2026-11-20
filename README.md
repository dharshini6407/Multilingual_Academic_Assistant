# Multilingual Academic Information Assistant with Smart Academic Alerts and Personalized Study Planning

An enterprise-grade, full-stack college academic portal built with **React.js (Vite)**, **Python Flask REST API**, **MySQL**, and **Multilingual Retrieval-Augmented Generation (RAG)** supporting **English**, **Tamil (தமிழ்)**, and **Tanglish**.

---

## 🌟 Key Features

### 1. 🔐 Authentication & Role-Based Access Control
- Student registration & secure authentication with **PBKDF2 SHA-256** password hashing.
- **JWT (JSON Web Token)** bearer authentication with role claims (`student`, `admin`).
- Role-guarded API endpoints and client-side views.
- Student profile customization (name, department, semester, year, language preference).
- Notification preference settings (exam alerts, assignment alerts, activity alerts, low attendance warnings).

### 2. 📊 Student Dashboard (Real Database Data)
- Real-time aggregated metrics directly queried from MySQL (no hardcoded statistics).
- Live attendance percentage aggregated across all enrolled courses.
- Upcoming examination countdown cards synchronized with **Asia/Kolkata** timezone.
- Pending assignments, overdue indicators, and academic symposium announcements.
- Active study plan progress bar and unread smart academic alerts counter.
- Quick navigation shortcuts to all portal modules.

### 3. 💬 Multilingual Academic Chatbot (RAG Engine)
- **Languages Supported**: English, Tamil (`ta`), and Tanglish (Tamil in Latin script).
- Administrator PDF uploads for official handbooks, curriculum, and examination regulations.
- Page-by-page text extraction and sliding-window chunking (`pypdf`, `pdfplumber`, `pymupdf`).
- **Semantic & TF-IDF Retrieval**: High-precision vector and keyword retrieval across active documents.
- **Verbatim Citations**: Displays source document title and exact page numbers.
- **Zero Hallucination Policy**: Never invents academic information when sources do not support an answer; redirects users to official department contact channels.
- **Graceful Retrieval Fallback**: When no external AI key is configured, operates in verified direct passage retrieval mode without error.
- Full conversation history and user feedback rating (thumbs up / down) stored in database.

### 4. 📈 Attendance Tracker & Forecast Simulator
- Stores conducted and attended classes per subject.
- Formula: $\text{Attendance } \% = \frac{\text{Attended}}{\text{Conducted}} \times 100$.
- Allows students to configure personalized attendance targets (e.g. 75% or 80%).
- **Consecutive Classes Required Calculator**:
  $$x = \left\lceil \frac{T \cdot C - A}{1 - T} \right\rceil$$
- **Safety Margin Calculator**: Calculates how many classes a student can safely miss while remaining above the target.
- **What-If Forecast Simulator**: Simulates hypothetical future classes attended or missed.
- Handles zero classes, invalid targets, and impossible states safely.

### 5. 📅 Examination Calendar & Smart Alerts
- Full administrative CRUD: create, reschedule, cancel, and update exams.
- Displays live countdowns calculated in **calendar days** using the **Asia/Kolkata** timezone.
- Dynamic countdown messages:
  - `Exam in N days` (for $N > 1$)
  - `Exam tomorrow` (for $N = 1$)
  - `Exam Day!` (for $N = 0$)
  - `Exam Completed` (for $N < 0$)
- **Automated Smart In-App Alerts**:
  - 7 days before
  - 3 days before
  - 1 day before
  - On exam day:
    - **Title**: `All the Best for Your Exam! 🎓`
    - **Message**: `Your examination is today. Stay calm, read every question carefully, manage your time, and give your best. Good luck! 💙`
- **Deduplication & Restart Recovery**: Unique deduplication keys prevent repeated notifications; missed reminders are automatically scanned and recovered on server startup.
- **Broadcast on Status Change**: Rescheduling or cancelling an exam dispatches urgent notifications to all enrolled students.

### 6. 📝 Assignments & Academic Activities
- Course assignments with priority badges (High, Medium, Low), deadlines, and max marks.
- Student progress workflow: `Pending` ➔ `In Progress` ➔ `Submitted` ➔ `Completed`.
- Automated detection of upcoming vs overdue assignments.
- Academic activities catalog for department workshops, symposiums, guest lectures, and hackathons.

### 7. 🎯 Personalized Study Planner
- Daily and weekly academic study plan creation.
- **Transparent Rule-Based Generator**:
  - Automatically incorporates upcoming exam dates (earlier exams prioritized).
  - Integrates pending assignments based on submission deadlines.
  - Respects daily study hour budget (e.g., 3.0 hours/day).
  - Allocates realistic evening time blocks (17:00, 18:15, 19:45, 21:00).
- Real-time plan completion percentage tracking.

### 8. ⏱️ Pomodoro Focus Timer
- Interactive circular countdown timer with Start, Pause, Resume, and Reset.
- Configurable focus duration (15m, 25m, 45m, 60m) and break duration (5m, 10m, 15m).
- **Accurate Time Tracking**: Paused time is strictly excluded from focused statistics.
- Subject tagging and session note recording.
- Automatically persists completed focus sessions to MySQL.
- Displays focus study history, total hours, and today's focused minutes.

### 9. 🔔 Notification Center
- Persistent in-app notifications with read/unread statuses and timestamps.
- Filter by category: Exam Alerts, Assignments, Activities, System.
- One-click "Mark All as Read" and deletion controls.
- Strict user ownership enforcement.

### 10. 🛡️ Admin Control Console
- **Student Accounts & Roles**: Manage roles (`student`, `admin`) and activate/disable accounts.
- **Knowledge Base Manager**: Upload PDF handbooks, toggle active/searchable status, delete, and trigger complete reindexing.
- **Unanswered Queries Review**: Review questions where official documents lacked answers, draft official administrative responses, and broadcast directly to student alerts.
- **Delivery Audit Trail**: Inspect smart alert delivery records verifying deduplication keys and delivery timestamps.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 19, Vite, Lucide Icons, Pure Vanilla CSS Design System |
| **Backend** | Python 3.11, Flask 3, Flask-Cors, Flask-JWT-Extended, Flask-SQLAlchemy |
| **Database** | MySQL 8.0+ (with SQLite fallback for zero-friction evaluation) |
| **Scheduler** | APScheduler 3.11 (Asia/Kolkata timezone) |
| **PDF Processing** | pypdf, pdfplumber, pymupdf (fitz) |
| **NLP & RAG** | Scikit-Learn TF-IDF, Cosine Similarity, Unicode Tamil Script Parser |
| **Testing** | Pytest, Webpack/Vite Production Bundler |

---

## 🚀 Quick Start (Development)

### 1. Backend Setup
```powershell
# Navigate to project root
cd "c:\mini project\Multilingual_Academic_Assistant_1"

# Create and activate virtual environment
python -m venv backend\venv
backend\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Seed demo database with realistic records, PDF handbooks, and alert records
python database\seed_demo_data.py

# Start Flask Backend (Port 5000)
python backend\app.py
```

### 2. Frontend Setup
```powershell
# Open a second PowerShell terminal in frontend/
cd "c:\mini project\Multilingual_Academic_Assistant_1\frontend"

# Install node dependencies
npm install

# Start Vite Development Server (Port 5173)
npm run dev
```

Visit **http://localhost:5173** in your web browser.

---

## 🔑 Demo Evaluation Credentials

| Role | Email | Password | Preloaded Context |
|---|---|---|---|
| **Student** | `student@college.edu` | `Student@123` | Enrolled in 6 CSE subjects, exams today & tomorrow, active study plan |
| **Admin** | `admin@college.edu` | `Admin@123` | Full administrative console, PDF upload, exam scheduler |

*Quick 1-Click login buttons are also provided directly on the Login screen for instant evaluation.*

---

## 🧪 Automated Test Suite

Run the full automated test suite containing 22 comprehensive tests:
```powershell
backend\venv\Scripts\pytest -v tests
```

### Verified Test Categories:
1. Student registration & password hashing
2. Authentication & role permissions (403 for unauthorized students)
3. Attendance formulas, consecutive classes needed, and zero-class edge cases
4. Exam countdowns and Asia/Kolkata timezone boundaries
5. Reminder deduplication and restart recovery
6. Exact exam-day title and message verification
7. Exam rescheduling and cancellation alerts
8. Notification and task ownership security
9. Missing AI API key graceful fallback
10. PDF processing corrupt/invalid file failures
11. Invalid input rejection (negative class counts, bad emails)

---

## 📁 Repository Structure

```
Multilingual_Academic_Assistant_1/
├── backend/
│   ├── app.py                      # Flask factory & blueprint registration
│   ├── config.py                   # Asia/Kolkata timezone, JWT, DB settings
│   ├── db.py                       # Universal SQLAlchemy DB instance
│   ├── models.py                   # MySQL/SQLAlchemy data models
│   ├── uploads/                    # PDF uploads & generated test handbooks
│   ├── routes/                     # Blueprint endpoints (auth, dashboard, chat, etc.)
│   └── services/                   # Business logic (attendance, RAG, scheduler, PDF)
├── frontend/
│   ├── src/
│   │   ├── api.js                  # Centralized API fetch client with JWT
│   │   ├── App.jsx                 # App routing & active tab manager
│   │   ├── index.css               # Modern Royal Blue design system
│   │   ├── context/AuthContext.jsx # Auth state & multilingual translations
│   │   ├── components/             # Sidebar, Navbar, ConfirmationModal
│   │   └── pages/                  # Dashboard, Chat, Exams, Attendance, etc.
│   └── index.html                  # HTML entry point with Google Fonts
├── database/
│   ├── schema.sql                  # Production MySQL 8.0+ schema
│   └── seed_demo_data.py           # Demo data seed script
├── tests/                          # 22 Automated pytest unit & integration tests
├── requirements.txt                # Python backend dependencies
├── package.json                    # Root package scripts
├── README.md                       # Comprehensive project documentation
├── WINDOWS_SETUP.md                # Exact Windows PowerShell commands guide
└── API_DOCUMENTATION.md            # Complete REST API reference
```
